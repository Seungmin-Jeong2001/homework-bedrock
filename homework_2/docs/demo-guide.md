# Demo Guide

## Recording Flow

1. Show AWS Budget.
2. Show Bedrock model access in `ap-northeast-2`.
3. Show that the architecture still uses Bedrock Agent, Knowledge Base, and OpenSearch Serverless.
4. Explain the CloudFormation attempt and why Terraform/Ansible was chosen.
5. Run `./scripts/deploy.sh`.
6. Show the OpenSearch endpoint and `codebuddy-index` creation step in Ansible output.
7. Register Terraform output `webhook_url` in GitHub Webhook settings.
8. Create a PR with `sample/vulnerable_app.py`.
9. Show the GitHub PR review comment.
10. Show Slack notification.
11. Run `./scripts/verify.sh`.
12. Run `./scripts/destroy.sh`.

## Slide Note

In the retrospective slide, state: "CloudFormation was attempted first, but the deployment moved to Terraform/Ansible to explicitly create the OpenSearch vector index before Bedrock Knowledge Base creation. The architecture itself remains the PDF-style Bedrock Agent + Knowledge Base + OpenSearch design."
