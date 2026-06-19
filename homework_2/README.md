# CodeBuddy: AWS Bedrock Agent GitHub PR Reviewer

CodeBuddy는 PDF 실습 원형과 동일하게 Bedrock Agent, Knowledge Base, OpenSearch Serverless를 사용하는 GitHub PR 자동 리뷰 시스템입니다. 변경된 점은 배포 도구입니다. CloudFormation 배포는 중단하고, OpenSearch vector index 생성 단계를 명확하게 제어하기 위해 Terraform + Ansible로 배포합니다.

Flow:

GitHub PR -> GitHub Webhook -> API Gateway -> Lambda Orchestrator -> Bedrock Agent -> Knowledge Base -> OpenSearch Serverless -> GitHub PR 댓글 -> Slack 알림

## PDF 실습과 본 구현

| 구분 | PDF 실습 | 본 구현 |
|---|---|---|
| 인프라 배포 | CloudFormation | Terraform + Ansible |
| AI 호출 방식 | Bedrock Agent | Bedrock Agent |
| Knowledge Base | 사용 | 사용 |
| OpenSearch Serverless | 사용 | 사용 |
| Lambda Orchestrator | 사용 | 사용 |
| GitHub PR 댓글 | 사용 | 사용 |
| Slack 알림 | 사용 | 사용 |

Lambda는 Bedrock Runtime `InvokeModel` 직접 호출로 후퇴하지 않습니다. 기본 경로는 Bedrock Agent Runtime `invoke_agent`입니다.

## 왜 Terraform/Ansible로 전환했나

CloudFormation 시도 중 `CodeBuddyKnowledgeBase`가 반복 실패했습니다.

```text
Dependency error document status code: 404, error message: no such index [codebuddy-index]
```

원인은 OpenSearch Serverless Collection은 생성되었지만 Knowledge Base가 참조하는 vector index `codebuddy-index`가 아직 없었기 때문입니다. Collection과 index는 별개이며, Knowledge Base 생성 전에 index가 먼저 존재해야 합니다.

Terraform/Ansible로 전환한 이유:

- OpenSearch vector index 생성 단계를 배포 흐름에 명시적으로 넣기 위해
- foundation 리소스와 Bedrock 리소스를 단계별로 제어하기 위해
- 배포, 검증, 삭제를 반복 가능한 명령으로 자동화하기 위해

CloudFormation 시도 기록은 [docs/cloudformation-attempt.md](docs/cloudformation-attempt.md)에 보관했습니다.

## 배포 순서

Ansible deploy playbook은 아래 순서를 자동으로 실행합니다.

1. Lambda 패키징
2. `terraform init`
3. `terraform apply -var deployment_stage=foundation`
4. Terraform output에서 OpenSearch endpoint 획득
5. `scripts/create_opensearch_index.py`로 `codebuddy-index` 생성
6. `terraform apply -var deployment_stage=full`
7. `webhook_url` 출력

## 사전 준비

1. AWS Budget $30 설정
2. `ap-northeast-2`에서 Bedrock model access 활성화
3. AWS CLI profile 설정
4. Terraform 설치
5. Ansible 설치
6. GitHub token 생성
7. Slack webhook 생성
8. Knowledge Base 문서용 S3 bucket 준비

Knowledge Base 문서는 `knowledge-base/` 아래 파일을 S3 bucket에 업로드하세요.

```bash
aws s3 sync knowledge-base/ s3://YOUR_KNOWLEDGE_BUCKET/ --region ap-northeast-2
```

## 변수 설정

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
```

`terraform/terraform.tfvars`를 수정합니다.

```hcl
aws_region  = "ap-northeast-2"
aws_profile = "default"

project_name     = "codebuddy"
deployment_stage = "full"
lambda_zip_path  = "../build/lambda.zip"

foundation_model   = "anthropic.claude-3-haiku-20240307-v1:0"
embedding_model_id = "amazon.titan-embed-text-v2:0"

s3_knowledge_bucket_arn = "arn:aws:s3:::YOUR_KNOWLEDGE_BUCKET"

github_token          = "YOUR_GITHUB_PAT"
github_webhook_secret = "YOUR_RANDOM_WEBHOOK_SECRET"
slack_webhook_url     = "YOUR_SLACK_WEBHOOK_OR_EMPTY"
```

Do not commit `terraform/terraform.tfvars` or Terraform state files.

## 배포

배포 전 현재 AWS 실행자 ARN을 확인하세요.

```bash
aws sts get-caller-identity
```

Ansible이 로컬에서 `scripts/create_opensearch_index.py`를 실행하므로, 이 ARN이 OpenSearch Serverless data access policy의 Principal에 포함되어야 합니다. Terraform은 기본적으로 `data.aws_caller_identity.current.arn`을 access policy에 자동 포함합니다. 다른 IAM 사용자/Role로 index를 만들려면 `terraform.tfvars`에 `opensearch_admin_principal_arn`을 지정하세요.

```bash
./scripts/deploy.sh
```

배포가 끝나면 출력된 `GitHub Webhook Payload URL`을 GitHub Webhook에 등록합니다.

GitHub Webhook 설정:

- Payload URL: Terraform output `webhook_url`
- Content type: `application/json`
- Secret: `github_webhook_secret`와 같은 값
- Events: Pull requests

## 검증

```bash
./scripts/verify.sh
```

검증 항목:

- Lambda 존재 확인
- OpenSearch Serverless Collection 확인
- `codebuddy-index` 존재 확인
- Knowledge Base ID 확인
- Bedrock Agent ID와 Alias ID 확인
- Webhook URL 출력

## 삭제

```bash
./scripts/destroy.sh
```

삭제 후 AWS 콘솔 또는 CLI로 OpenSearch Serverless, Bedrock Knowledge Base, Bedrock Agent, CloudWatch Log Group 잔여 리소스를 확인하세요.

## 비용 주의

OpenSearch Serverless와 Knowledge Base는 비용이 발생할 수 있습니다. 시연 직전에 배포하고, 시연 후 바로 삭제하세요. Knowledge Base 문서는 작은 샘플만 사용합니다.

## 보안 주의

GitHub token, Slack webhook URL, webhook secret을 README나 문서에 직접 적지 마세요. 값이 노출되었다면 즉시 GitHub token과 Slack webhook을 회전하세요.

## OpenSearch 403 권한 확인

`Failed to create index codebuddy-index: 403 Forbidden`이 발생하면 다음을 확인하세요.

1. `aws sts get-caller-identity`로 현재 실행자 ARN 확인
2. Terraform output `opensearch_access_policy_principals`에 해당 ARN이 포함되어 있는지 확인
3. 배포 IAM 사용자/Role에 `aoss:APIAccessAll` 권한이 있는지 확인

현재 index 생성 스크립트는 `urllib` 직접 서명 방식 대신 `opensearch-py`의 `OpenSearch`, `RequestsHttpConnection`, `AWSV4SignerAuth`를 사용합니다.

예시 IAM policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "aoss:APIAccessAll",
        "aoss:DashboardsAccessAll",
        "aoss:BatchGetCollection",
        "aoss:ListCollections",
        "aoss:CreateCollection",
        "aoss:DeleteCollection",
        "aoss:UpdateCollection",
        "aoss:CreateSecurityPolicy",
        "aoss:GetSecurityPolicy",
        "aoss:UpdateSecurityPolicy",
        "aoss:DeleteSecurityPolicy",
        "aoss:ListSecurityPolicies",
        "aoss:CreateAccessPolicy",
        "aoss:GetAccessPolicy",
        "aoss:UpdateAccessPolicy",
        "aoss:DeleteAccessPolicy",
        "aoss:ListAccessPolicies"
      ],
      "Resource": "*"
    }
  ]
}
```
