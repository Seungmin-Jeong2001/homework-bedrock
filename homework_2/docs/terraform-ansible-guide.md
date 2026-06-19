# Terraform and Ansible Guide

## Role Split

Terraform creates AWS resources:

- API Gateway HTTP API
- Lambda Orchestrator
- Lambda IAM Role
- CloudWatch Log Group
- OpenSearch Serverless policies and VECTORSEARCH collection
- Bedrock Knowledge Base IAM Role
- Bedrock Knowledge Base and Data Source
- Bedrock Agent and Agent Alias

Ansible controls the deployment order:

1. Package Lambda.
2. Run `terraform init`.
3. Run `terraform apply -var deployment_stage=foundation`.
4. Read `opensearch_collection_endpoint`.
5. Run `scripts/create_opensearch_index.py`.
6. Run `terraform apply -var deployment_stage=full`.
7. Print `webhook_url`.

## Why Two Stages

Bedrock Knowledge Base fails if `codebuddy-index` does not exist in the OpenSearch Serverless collection. Terraform creates the collection first, Ansible creates the index, and Terraform then creates the Knowledge Base and Agent.

## Deploy

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
./scripts/deploy.sh
```

## Verify

```bash
./scripts/verify.sh
```

## Destroy

```bash
./scripts/destroy.sh
```

## Common Errors

- `no such index [codebuddy-index]`: run deployment through Ansible so the index creation step happens before Knowledge Base creation.
- AWS credential error: run `aws sts get-caller-identity`.
- Bedrock access denied: enable model access in `ap-northeast-2`.
- GitHub 401 or 403: check PAT scopes and webhook secret.
