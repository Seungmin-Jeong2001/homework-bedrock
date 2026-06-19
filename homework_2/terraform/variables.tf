variable "aws_region" {
  description = "AWS region for the deployment."
  type        = string
  default     = "ap-northeast-2"
}

variable "aws_profile" {
  description = "Optional AWS CLI profile name. Leave empty to use environment credentials."
  type        = string
  default     = ""
}

variable "project_name" {
  description = "Name prefix for AWS resources."
  type        = string
  default     = "codebuddy"
}

variable "deployment_stage" {
  description = "foundation creates API/Lambda/OpenSearch only. full also creates Knowledge Base and Bedrock Agent."
  type        = string
  default     = "full"

  validation {
    condition     = contains(["foundation", "full"], var.deployment_stage)
    error_message = "deployment_stage must be foundation or full."
  }
}

variable "lambda_zip_path" {
  description = "Path to the packaged Lambda zip file."
  type        = string
  default     = "../build/lambda.zip"
}

variable "foundation_model" {
  description = "Bedrock foundation model ID for the Agent."
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}

variable "embedding_model_id" {
  description = "Bedrock embedding model ID for the Knowledge Base."
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "github_token" {
  description = "GitHub Personal Access Token used to read PR diffs and post comments."
  type        = string
  sensitive   = true
}

variable "slack_webhook_url" {
  description = "Optional Slack incoming webhook URL."
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_webhook_secret" {
  description = "GitHub webhook secret used to verify payload signatures."
  type        = string
  sensitive   = true
  default     = ""
}

variable "disable_webhook_secret_verify" {
  description = "Set true only for initial local or temporary testing."
  type        = bool
  default     = false
}

variable "max_diff_chars" {
  description = "Maximum PR diff characters sent to Bedrock Agent."
  type        = number
  default     = 12000
}

variable "s3_knowledge_bucket_arn" {
  description = "S3 bucket ARN containing Knowledge Base documents."
  type        = string
}

variable "vector_index_name" {
  description = "OpenSearch Serverless vector index name."
  type        = string
  default     = "codebuddy-index"
}

variable "vector_dimension" {
  description = "Titan Text Embeddings V2 vector dimension."
  type        = number
  default     = 1024
}

variable "opensearch_admin_principal_arn" {
  description = "Optional IAM principal ARN allowed to create OpenSearch Serverless index during deployment. Leave empty to use the Terraform caller ARN."
  type        = string
  default     = ""
}
