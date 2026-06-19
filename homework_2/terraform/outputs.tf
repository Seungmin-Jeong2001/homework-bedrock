output "webhook_url" {
  description = "GitHub Webhook Payload URL."
  value       = module.api_lambda.webhook_url
}

output "lambda_function_name" {
  description = "Lambda function name."
  value       = module.api_lambda.lambda_function_name
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch Log Group name."
  value       = module.api_lambda.cloudwatch_log_group_name
}

output "opensearch_collection_endpoint" {
  description = "OpenSearch Serverless collection endpoint."
  value       = module.opensearch_serverless.collection_endpoint
}

output "opensearch_collection_name" {
  description = "OpenSearch Serverless collection name."
  value       = module.opensearch_serverless.collection_name
}

output "opensearch_access_policy_name" {
  description = "OpenSearch Serverless data access policy name."
  value       = module.opensearch_serverless.access_policy_name
}

output "opensearch_access_policy_principals" {
  description = "Principals allowed by the OpenSearch Serverless data access policy."
  value       = module.opensearch_serverless.access_policy_principals
}

output "terraform_caller_arn" {
  description = "ARN of the principal used by Terraform."
  value       = module.opensearch_serverless.terraform_caller_arn
}

output "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID."
  value       = try(module.bedrock_knowledge_base[0].knowledge_base_id, "")
}

output "bedrock_agent_id" {
  description = "Bedrock Agent ID."
  value       = try(module.bedrock_agent[0].agent_id, "")
}

output "bedrock_agent_alias_id" {
  description = "Bedrock Agent Alias ID."
  value       = try(module.bedrock_agent[0].agent_alias_id, "")
}

output "aws_region" {
  description = "AWS region used by this deployment."
  value       = var.aws_region
}
