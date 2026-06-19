import hashlib
import hmac
import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SUPPORTED_ACTIONS = {"opened", "synchronize", "reopened"}
MAX_DIFF_CHARS = int(os.getenv("MAX_DIFF_CHARS", "12000"))
BEDROCK_MAX_TOKENS = int(os.getenv("BEDROCK_MAX_TOKENS", "800"))
ENABLE_DIRECT_INVOKE_MODEL = os.getenv("ENABLE_DIRECT_INVOKE_MODEL", "false").lower() == "true"


def log_event(level: str, message: str, **fields: Any) -> None:
    payload = {"message": message, **fields}
    getattr(logger, level.lower())(json.dumps(payload, ensure_ascii=False))


def response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def get_header(headers: dict[str, str] | None, name: str) -> str | None:
    if not headers:
        return None
    lowered = {key.lower(): value for key, value in headers.items()}
    return lowered.get(name.lower())


def verify_github_signature(headers: dict[str, str] | None, raw_body: str) -> bool:
    if os.getenv("DISABLE_WEBHOOK_SECRET_VERIFY", "false").lower() == "true":
        return True

    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        log_event("warning", "webhook secret is not configured")
        return False

    signature = get_header(headers, "x-hub-signature-256")
    if not signature or not signature.startswith("sha256="):
        log_event("warning", "missing github webhook signature")
        return False

    digest = hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"
    return hmac.compare_digest(expected, signature)


def parse_event_body(event: dict[str, Any]) -> tuple[dict[str, Any], str]:
    raw_body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64

        raw_body = base64.b64decode(raw_body).decode("utf-8")
    return json.loads(raw_body), raw_body


def extract_pr_context(payload: dict[str, Any]) -> dict[str, Any]:
    repository = payload["repository"]
    pull_request = payload["pull_request"]
    return {
        "action": payload.get("action"),
        "owner": repository["owner"]["login"],
        "repo": repository["name"],
        "pull_number": pull_request["number"],
        "pr_url": pull_request["html_url"],
        "diff_url": pull_request.get("diff_url"),
    }


def github_request(url: str, token: str, method: str = "GET", body: dict[str, Any] | None = None) -> str:
    data = None
    headers = {
        "accept": "application/vnd.github+json",
        "authorization": f"Bearer {token}",
        "user-agent": "codebuddy-bedrock-reviewer",
        "x-github-api-version": "2022-11-28",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["content-type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as res:
            return res.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {exc.code}: {detail}") from exc


def fetch_pr_diff(owner: str, repo: str, pull_number: int, token: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    headers = {
        "accept": "application/vnd.github.v3.diff",
        "authorization": f"Bearer {token}",
        "user-agent": "codebuddy-bedrock-reviewer",
    }
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=20) as res:
            return res.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub diff fetch error {exc.code}: {detail}") from exc


def truncate_diff(diff_text: str, max_chars: int = MAX_DIFF_CHARS) -> str:
    if len(diff_text) <= max_chars:
        return diff_text
    suffix = "\n\n[Diff truncated to control Bedrock token cost.]"
    return diff_text[: max_chars - len(suffix)] + suffix


def build_review_prompt(context: dict[str, Any], diff_text: str) -> str:
    return f"""You are CodeBuddy, a concise senior code reviewer.
Review this GitHub pull request for correctness, security, reliability, and test gaps.
Return Markdown in Korean with these sections:

## 요약
## 주요 발견
## 권장 수정
## 테스트 제안

Repository: {context["owner"]}/{context["repo"]}
Pull Request: #{context["pull_number"]}
URL: {context["pr_url"]}

Unified diff:
```diff
{diff_text}
```
"""


def build_bedrock_body(model_id: str, prompt: str) -> dict[str, Any]:
    if "anthropic.claude-3" in model_id or "anthropic.claude" in model_id:
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": BEDROCK_MAX_TOKENS,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        }
    return {
        "inputText": prompt,
        "textGenerationConfig": {"maxTokenCount": BEDROCK_MAX_TOKENS, "temperature": 0.2},
    }


def parse_bedrock_response(body_text: str) -> str:
    try:
        body = json.loads(body_text)
    except json.JSONDecodeError:
        return body_text

    try:
        content = body.get("content")
        if isinstance(content, list) and content:
            texts = [item.get("text", "") for item in content if isinstance(item, dict)]
            return "\n".join(text for text in texts if text).strip()

        if "completion" in body:
            return str(body["completion"]).strip()

        results = body.get("results")
        if isinstance(results, list) and results:
            first = results[0]
            return str(first.get("outputText") or first.get("text") or first).strip()

        if "outputText" in body:
            return str(body["outputText"]).strip()
    except Exception as exc:
        log_event("warning", "failed to parse known bedrock response shape", error=str(exc))

    return json.dumps(body, ensure_ascii=False)[:4000]


def invoke_bedrock(prompt: str) -> str:
    import boto3

    model_id = os.environ["BEDROCK_MODEL_ID"]
    client = boto3.client("bedrock-runtime")
    request_body = build_bedrock_body(model_id, prompt)
    result = client.invoke_model(
        modelId=model_id,
        body=json.dumps(request_body).encode("utf-8"),
        contentType="application/json",
        accept="application/json",
    )
    body_text = result["body"].read().decode("utf-8")
    review = parse_bedrock_response(body_text)
    return review or "Bedrock returned an empty review."


def invoke_bedrock_agent(prompt: str, context: dict[str, Any]) -> str:
    import boto3

    agent_id = os.environ["BEDROCK_AGENT_ID"]
    agent_alias_id = os.environ["BEDROCK_AGENT_ALIAS_ID"]
    session_id = f"github-pr-{context['owner']}-{context['repo']}-{context['pull_number']}"
    client = boto3.client("bedrock-agent-runtime")
    result = client.invoke_agent(
        agentId=agent_id,
        agentAliasId=agent_alias_id,
        sessionId=session_id[:100],
        inputText=prompt,
    )

    chunks: list[str] = []
    for event in result.get("completion", []):
        chunk = event.get("chunk")
        if chunk and "bytes" in chunk:
            chunks.append(chunk["bytes"].decode("utf-8", errors="replace"))
    return "".join(chunks).strip() or "Bedrock Agent returned an empty review."


def generate_review(prompt: str, context: dict[str, Any]) -> str:
    if ENABLE_DIRECT_INVOKE_MODEL:
        log_event("warning", "using direct InvokeModel fallback")
        return invoke_bedrock(prompt)
    return invoke_bedrock_agent(prompt, context)


def post_pr_comment(owner: str, repo: str, pull_number: int, token: str, markdown: str) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pull_number}/comments"
    body = {"body": markdown}
    github_request(url, token, method="POST", body=body)


def notify_slack(webhook_url: str | None, context: dict[str, Any], review: str) -> None:
    if not webhook_url:
        return

    preview = review.replace("\n", " ")[:300]
    body = {
        "text": (
            f"CodeBuddy review completed for {context['owner']}/{context['repo']} "
            f"PR #{context['pull_number']}: {context['pr_url']}\n{preview}"
        )
    }
    request = urllib.request.Request(
        webhook_url,
        data=json.dumps(body).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as res:
            res.read()
    except Exception as exc:
        log_event("warning", "slack notification failed", error=str(exc), error_type=type(exc).__name__)


def build_comment(review: str) -> str:
    return f"""## CodeBuddy Bedrock Review

{review}

---
Generated by AWS Lambda + Amazon Bedrock Agent. Please verify suggestions before merging.
"""


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    try:
        if event.get("requestContext", {}).get("http", {}).get("method") == "GET":
            return response(200, {"message": "codebuddy orchestrator is healthy"})

        payload, raw_body = parse_event_body(event)

        if not verify_github_signature(event.get("headers"), raw_body):
            return response(401, {"message": "invalid webhook signature"})

        event_name = get_header(event.get("headers"), "x-github-event")
        if event_name and event_name != "pull_request":
            return response(202, {"message": f"ignored event {event_name}"})

        action = payload.get("action")
        if action not in SUPPORTED_ACTIONS:
            return response(202, {"message": f"ignored action {action}"})

        context = extract_pr_context(payload)
        log_event("info", "processing pull request", **context)

        github_token = os.environ["GITHUB_TOKEN"]
        diff = fetch_pr_diff(context["owner"], context["repo"], context["pull_number"], github_token)
        limited_diff = truncate_diff(diff)
        prompt = build_review_prompt(context, limited_diff)
        review = generate_review(prompt, context)
        comment = build_comment(review)
        post_pr_comment(context["owner"], context["repo"], context["pull_number"], github_token, comment)
        notify_slack(os.getenv("SLACK_WEBHOOK_URL"), context, review)

        log_event("info", "review completed", owner=context["owner"], repo=context["repo"], pull_number=context["pull_number"])
        return response(200, {"message": "review completed", "pull_number": context["pull_number"]})
    except KeyError as exc:
        log_event("error", "missing required configuration or payload field", error=str(exc))
        return response(500, {"message": "missing required configuration or payload field"})
    except Exception as exc:
        log_event("error", "review failed", error=str(exc), error_type=type(exc).__name__)
        return response(500, {"message": "review failed"})
