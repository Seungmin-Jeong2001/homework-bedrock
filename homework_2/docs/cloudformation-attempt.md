# CloudFormation Attempt

This project originally attempted to deploy the PDF-style architecture with CloudFormation.

## What Was Attempted

- API Gateway HTTP API
- Lambda Orchestrator
- Bedrock Agent
- Bedrock Knowledge Base
- OpenSearch Serverless VECTORSEARCH collection
- CloudFormation Custom Resource for `codebuddy-index`

## Failures Observed

1. Embedding model ARN region mismatch

The stack was deployed in `ap-northeast-2`, but the Knowledge Base embedding model ARN was hardcoded to `us-east-1`.

2. Missing OpenSearch vector index

```text
CodeBuddyKnowledgeBase CREATE_FAILED
Dependency error document status code: 404, error message: no such index [codebuddy-index]
```

OpenSearch Serverless Collection creation does not automatically create the vector index used by Bedrock Knowledge Base.

## Why Terraform and Ansible

CloudFormation can work with a Custom Resource, but this assignment switched to Terraform and Ansible to make the deployment stages explicit:

1. Create foundation resources and OpenSearch Serverless collection.
2. Create `codebuddy-index` with a signed OpenSearch Serverless API request.
3. Create Bedrock Knowledge Base, Data Source, Agent, and Agent Alias.

The architecture remains the PDF practice architecture. Only the deployment tooling changed.
