data "aws_partition" "current" {}

locals {
  create_bedrock      = var.deployment_stage == "full"
  embedding_model_arn = "arn:${data.aws_partition.current.partition}:bedrock:${var.aws_region}::foundation-model/${var.embedding_model_id}"
}

module "opensearch_serverless" {
  source = "./modules/opensearch_serverless"

  project_name                   = var.project_name
  vector_index_name              = var.vector_index_name
  opensearch_admin_principal_arn = var.opensearch_admin_principal_arn
}

module "bedrock_knowledge_base" {
  source = "./modules/bedrock_knowledge_base"
  count  = local.create_bedrock ? 1 : 0

  project_name                   = var.project_name
  embedding_model_arn            = local.embedding_model_arn
  s3_knowledge_bucket_arn        = var.s3_knowledge_bucket_arn
  opensearch_collection_arn      = module.opensearch_serverless.collection_arn
  opensearch_vector_index_name   = var.vector_index_name
  opensearch_vector_field_name   = "vector"
  opensearch_text_field_name     = "text"
  opensearch_metadata_field_name = "metadata"
  knowledge_base_role_arn        = module.opensearch_serverless.knowledge_base_role_arn
  knowledge_base_role_name       = module.opensearch_serverless.knowledge_base_role_name
}

module "bedrock_agent" {
  source = "./modules/bedrock_agent"
  count  = local.create_bedrock ? 1 : 0

  project_name      = var.project_name
  foundation_model  = var.foundation_model
  knowledge_base_id = module.bedrock_knowledge_base[0].knowledge_base_id
}

module "api_lambda" {
  source = "./modules/api_lambda"

  project_name                  = var.project_name
  lambda_zip_path               = var.lambda_zip_path
  github_token                  = var.github_token
  slack_webhook_url             = var.slack_webhook_url
  github_webhook_secret         = var.github_webhook_secret
  disable_webhook_secret_verify = var.disable_webhook_secret_verify
  max_diff_chars                = var.max_diff_chars
  bedrock_agent_id              = local.create_bedrock ? module.bedrock_agent[0].agent_id : ""
  bedrock_agent_alias_id        = local.create_bedrock ? module.bedrock_agent[0].agent_alias_id : ""
}
