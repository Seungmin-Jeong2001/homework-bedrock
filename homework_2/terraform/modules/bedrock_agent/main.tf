resource "aws_iam_role" "agent" {
  name = "${var.project_name}-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "agent" {
  name = "${var.project_name}-agent-policy"
  role = aws_iam_role.agent.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:Retrieve"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_bedrockagent_agent" "this" {
  agent_name                  = "${var.project_name}-pr-review-agent"
  agent_resource_role_arn     = aws_iam_role.agent.arn
  foundation_model            = var.foundation_model
  idle_session_ttl_in_seconds = 600
  instruction                 = "You are CodeBuddy, a senior GitHub pull request reviewer. Review code changes for correctness, security, reliability, and test gaps. Use the attached Knowledge Base when helpful and respond in concise Korean Markdown."
}

resource "aws_bedrockagent_agent_knowledge_base_association" "this" {
  agent_id             = aws_bedrockagent_agent.this.id
  description          = "Reference documents for secure pull request review."
  knowledge_base_id    = var.knowledge_base_id
  knowledge_base_state = "ENABLED"
}

resource "aws_bedrockagent_agent_alias" "this" {
  agent_alias_name = "live"
  agent_id         = aws_bedrockagent_agent.this.id

  depends_on = [
    aws_bedrockagent_agent_knowledge_base_association.this
  ]
}
