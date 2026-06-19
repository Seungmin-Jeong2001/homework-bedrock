variable "project_name" {
  type = string
}

variable "lambda_zip_path" {
  type = string
}

variable "github_token" {
  type      = string
  sensitive = true
}

variable "slack_webhook_url" {
  type      = string
  sensitive = true
  default   = ""
}

variable "github_webhook_secret" {
  type      = string
  sensitive = true
  default   = ""
}

variable "disable_webhook_secret_verify" {
  type = bool
}

variable "max_diff_chars" {
  type = number
}

variable "bedrock_agent_id" {
  type = string
}

variable "bedrock_agent_alias_id" {
  type = string
}
