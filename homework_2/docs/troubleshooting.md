# Troubleshooting

## CodeBuddyKnowledgeBase CREATE_FAILED: embedding model region mismatch

Problem:

```text
CodeBuddyKnowledgeBase CREATE_FAILED
The embedding model ARN ... is in a different region.
```

Cause:

CloudFormation 스택 리전과 Knowledge Base `EmbeddingModelArn`의 리전이 다릅니다. 예를 들어 스택은 `ap-northeast-2`에 배포하면서 embedding model ARN은 `us-east-1`로 넘기면 `AWS::Bedrock::KnowledgeBase` 생성이 실패합니다.

Fix:

스택 배포 리전과 embedding model ARN 리전을 일치시킵니다. 본 프로젝트는 `ap-northeast-2` 기준으로 배포합니다.

Terraform은 `embedding_model_id`를 받아 현재 리전 기반 ARN을 생성합니다.

```yaml
embedding_model_arn = "arn:${partition}:bedrock:${aws_region}::foundation-model/${embedding_model_id}"
```

Deploy with Terraform/Ansible after fixing the template values:

```bash
./scripts/deploy.sh
```

## CodeBuddyKnowledgeBase CREATE_FAILED: no such index

Problem:

```text
CodeBuddyKnowledgeBase CREATE_FAILED
The knowledge base storage configuration provided is invalid...
Dependency error document status code: 404, error message: no such index [codebuddy-index]
```

Cause:

OpenSearch Serverless Collection은 생성되었지만, Knowledge Base가 참조하는 vector index `codebuddy-index`가 Collection 안에 아직 생성되지 않았습니다. Collection과 vector index는 서로 다릅니다.

Fix:

현재 실제 배포 경로에서는 CloudFormation을 사용하지 않고 Ansible이 `scripts/create_opensearch_index.py`를 실행해 `codebuddy-index`를 먼저 생성합니다. 그 다음 Terraform이 Knowledge Base와 Bedrock Agent를 생성합니다.

Index mapping must match the Knowledge Base storage configuration:

- Vector index name: `codebuddy-index`
- Vector field: `vector`
- Text field: `text`
- Metadata field: `metadata`
- Titan Text Embeddings V2 dimension: `1024`

Check failed stack events:

```bash
aws cloudformation describe-stack-events \
  --stack-name codebuddy-bedrock-agent \
  --region ap-northeast-2 \
  --query "StackEvents[?contains(ResourceStatus, 'FAILED')].[Timestamp,LogicalResourceId,ResourceType,ResourceStatus,ResourceStatusReason]" \
  --output table
```

For the Terraform/Ansible deployment, rerun:

```bash
./scripts/deploy.sh
```

## Failed to create index codebuddy-index: 403 Forbidden

Error:

```text
Failed to create index codebuddy-index: 403 Forbidden
```

Cause:

OpenSearch Serverless data access policy에 index 생성 스크립트를 실행하는 IAM principal이 포함되지 않았거나, 해당 principal의 IAM policy에 `aoss:APIAccessAll` 권한이 부족합니다. `scripts/create_opensearch_index.py`는 Ansible에서 로컬 AWS credential로 실행되므로 현재 실행자 ARN이 access policy Principal에 있어야 합니다.

Fix:

1. 현재 ARN 확인

```bash
aws sts get-caller-identity
```

2. Terraform access policy Principal 확인

```bash
terraform -chdir=terraform output opensearch_access_policy_principals
```

3. 다른 principal을 명시적으로 허용해야 하면 `terraform.tfvars`에 추가

```hcl
opensearch_admin_principal_arn = "arn:aws:iam::123456789012:role/YourDeployRole"
```

4. 배포 IAM 사용자/Role에 `aoss:APIAccessAll` 권한 추가

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

5. 재실행

```bash
./scripts/deploy.sh
```

현재 스크립트는 `urllib` 직접 서명 방식 대신 `opensearch-py`의 `AWSV4SignerAuth` 기반 OpenSearch client를 사용합니다. 403이 계속되면 서명 코드보다 Principal/IAM 권한 문제일 가능성이 높습니다.
