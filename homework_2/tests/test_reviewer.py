import importlib.util
import json
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("orchestrator", ROOT / "lambda" / "orchestrator.py")
orchestrator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orchestrator)


def load_payload():
    return json.loads((ROOT / "tests" / "test_payload.json").read_text())


def test_extract_pr_context():
    context = orchestrator.extract_pr_context(load_payload())
    assert context["owner"] == "octocat"
    assert context["repo"] == "demo-repo"
    assert context["pull_number"] == 7
    assert context["pr_url"].endswith("/pull/7")


def test_build_review_prompt_contains_diff_and_sections():
    context = orchestrator.extract_pr_context(load_payload())
    prompt = orchestrator.build_review_prompt(context, "diff --git a/app.py b/app.py")
    assert "octocat/demo-repo" in prompt
    assert "## 주요 발견" in prompt
    assert "diff --git" in prompt


def test_lambda_handler_happy_path(monkeypatch):
    monkeypatch.setenv("DISABLE_WEBHOOK_SECRET_VERIFY", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_fake")
    monkeypatch.setenv("BEDROCK_AGENT_ID", "agent123")
    monkeypatch.setenv("BEDROCK_AGENT_ALIAS_ID", "alias123")

    event = {
        "headers": {"x-github-event": "pull_request"},
        "body": json.dumps(load_payload()),
        "isBase64Encoded": False,
    }

    with patch.object(orchestrator, "fetch_pr_diff", return_value="diff --git a/app.py b/app.py"), patch.object(
        orchestrator, "generate_review", return_value="리뷰 결과"
    ), patch.object(orchestrator, "post_pr_comment") as post_comment, patch.object(orchestrator, "notify_slack") as slack:
        result = orchestrator.lambda_handler(event, None)

    assert result["statusCode"] == 200
    post_comment.assert_called_once()
    slack.assert_called_once()


def test_lambda_handler_ignores_unsupported_action(monkeypatch):
    monkeypatch.setenv("DISABLE_WEBHOOK_SECRET_VERIFY", "true")
    payload = load_payload()
    payload["action"] = "closed"
    event = {"headers": {"x-github-event": "pull_request"}, "body": json.dumps(payload)}

    result = orchestrator.lambda_handler(event, None)

    assert result["statusCode"] == 202
