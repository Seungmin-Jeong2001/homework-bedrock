output "collection_name" {
  value = aws_opensearchserverless_collection.this.name
}

output "collection_arn" {
  value = aws_opensearchserverless_collection.this.arn
}

output "collection_endpoint" {
  value = aws_opensearchserverless_collection.this.collection_endpoint
}

output "dashboard_endpoint" {
  value = aws_opensearchserverless_collection.this.dashboard_endpoint
}

output "knowledge_base_role_arn" {
  value = aws_iam_role.knowledge_base.arn
}

output "knowledge_base_role_name" {
  value = aws_iam_role.knowledge_base.name
}

output "index_creator_role_arn" {
  value = aws_iam_role.index_creator.arn
}

output "access_policy_name" {
  value = aws_opensearchserverless_access_policy.data.name
}

output "terraform_caller_arn" {
  value = data.aws_caller_identity.current.arn
}

output "access_policy_principals" {
  value = local.access_policy_principals
}
