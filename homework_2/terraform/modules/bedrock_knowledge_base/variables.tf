variable "project_name" {
  type = string
}

variable "embedding_model_arn" {
  type = string
}

variable "s3_knowledge_bucket_arn" {
  type = string
}

variable "opensearch_collection_arn" {
  type = string
}

variable "opensearch_vector_index_name" {
  type = string
}

variable "opensearch_vector_field_name" {
  type = string
}

variable "opensearch_text_field_name" {
  type = string
}

variable "opensearch_metadata_field_name" {
  type = string
}

variable "knowledge_base_role_arn" {
  type = string
}

variable "knowledge_base_role_name" {
  type = string
}
