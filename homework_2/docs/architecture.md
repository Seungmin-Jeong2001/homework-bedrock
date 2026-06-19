# Architecture

Actual deployment architecture:

```text
GitHub Pull Request
  -> GitHub Webhook
  -> API Gateway HTTP API
  -> Lambda Orchestrator
  -> Bedrock Agent Runtime invoke_agent
  -> Bedrock Knowledge Base
  -> OpenSearch Serverless VECTORSEARCH collection
  -> codebuddy-index
  -> GitHub PR Markdown comment
  -> Slack Incoming Webhook
```

The architecture remains aligned with the PDF practice: Bedrock Agent, Knowledge Base, and OpenSearch Serverless are all used. The deployment tooling is Terraform + Ansible instead of CloudFormation.

The important operational detail is that OpenSearch Serverless Collection and OpenSearch vector index are different resources. `codebuddy-index` must exist before the Bedrock Knowledge Base is created.
