resource "aws_iam_role_policy" "knowledge_base" {
  name = "${var.project_name}-kb-bedrock-policy"
  role = var.knowledge_base_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = var.embedding_model_arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_knowledge_bucket_arn,
          "${var.s3_knowledge_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_bedrockagent_knowledge_base" "this" {
  name     = "${var.project_name}-knowledge-base"
  role_arn = var.knowledge_base_role_arn

  knowledge_base_configuration {
    type = "VECTOR"

    vector_knowledge_base_configuration {
      embedding_model_arn = var.embedding_model_arn
    }
  }

  storage_configuration {
    type = "OPENSEARCH_SERVERLESS"

    opensearch_serverless_configuration {
      collection_arn    = var.opensearch_collection_arn
      vector_index_name = var.opensearch_vector_index_name

      field_mapping {
        vector_field   = var.opensearch_vector_field_name
        text_field     = var.opensearch_text_field_name
        metadata_field = var.opensearch_metadata_field_name
      }
    }
  }

  depends_on = [
    aws_iam_role_policy.knowledge_base
  ]
}

resource "aws_bedrockagent_data_source" "this" {
  name              = "${var.project_name}-s3-documents"
  knowledge_base_id = aws_bedrockagent_knowledge_base.this.id

  data_source_configuration {
    type = "S3"

    s3_configuration {
      bucket_arn = var.s3_knowledge_bucket_arn
    }
  }
}
