# AWS Setup

## Free Tier Account Preparation

1. Sign in to AWS.
2. Choose the target region, default `ap-northeast-2`.
3. Create an AWS Budget alert at $30 or less.
4. Confirm your IAM user or role can manage Lambda, IAM, API Gateway, CloudWatch Logs, Bedrock Agent, Knowledge Base, and OpenSearch Serverless.
5. Enable Bedrock model access in the `ap-northeast-2` Bedrock console.

## Bedrock Model Access

In Amazon Bedrock:

1. Open Model access.
2. Request access for a low-cost model such as Claude 3 Haiku if available.
3. Confirm that `amazon.titan-embed-text-v2:0` is available in `ap-northeast-2`.
4. Wait until access is granted.
5. Use the exact model ID in Terraform variable `foundation_model`.

## Knowledge Base Embedding Model Region

Bedrock Knowledge Base의 embedding model ARN은 Terraform 배포 리전과 동일해야 합니다.

- `ap-northeast-2`에 배포하면 embedding model ARN도 `ap-northeast-2`여야 합니다.
- Terraform은 `embedding_model_id`와 `aws_region`으로 현재 리전 기반 embedding ARN을 생성합니다.

서울 리전에서 embedding 모델 확인:

```bash
aws bedrock list-foundation-models \
  --region ap-northeast-2 \
  --by-output-modality EMBEDDING \
  --query "modelSummaries[].{ModelId:modelId,Provider:providerName,Arn:modelArn}" \
  --output table
```

확인된 기본 embedding model:

```text
amazon.titan-embed-text-v2:0
```

## OpenSearch Serverless Vector Index

OpenSearch Serverless Collection과 vector index는 다릅니다. Collection은 저장소 컨테이너이고, Bedrock Knowledge Base가 사용하는 `codebuddy-index`는 Collection 안에 별도로 생성되어야 합니다.

Collection 생성만으로 `codebuddy-index`가 자동 생성되지 않습니다. Knowledge Base 생성 전에 다음 mapping을 가진 vector index가 필요합니다.

- Index name: `codebuddy-index`
- Vector field: `vector`
- Text field: `text`
- Metadata field: `metadata`
- Titan Text Embeddings V2 dimension: `1024`

이 저장소의 실제 배포는 Terraform/Ansible입니다. Ansible deploy playbook이 `scripts/create_opensearch_index.py`를 실행해 Knowledge Base 생성 전에 index를 생성합니다.

## Region Notes

PDF 실습은 서울 리전 기준이며, 이번 실제 배포 기본 리전도 `ap-northeast-2`입니다.

Observed issue:

```text
The embedding model ARN ... is in a different region.
```

Cause:

CloudFormation 시도 당시 stack은 `ap-northeast-2`에 있었고, Knowledge Base `EmbeddingModelArn`은 `us-east-1`이었습니다.

Additional check:

- `ap-northeast-2`에서 `amazon.titan-embed-text-v2:0`가 확인되었습니다.
- 기존 실패는 모델 부재가 아니라 `us-east-1` ARN 하드코딩으로 인한 리전 불일치였습니다.

Resolution:

본 과제 배포는 `ap-northeast-2`로 진행합니다.

## AWS CLI Profile

```bash
aws configure --profile codebuddy
aws sts get-caller-identity --profile codebuddy
```

For Terraform deployment, set:

```hcl
aws_profile = "codebuddy"
aws_region  = "ap-northeast-2"
```

Alternatively, leave `aws_profile = ""` and use environment variables such as `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.
