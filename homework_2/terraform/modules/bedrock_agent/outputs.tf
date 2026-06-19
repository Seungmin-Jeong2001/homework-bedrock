output "agent_id" {
  value = aws_bedrockagent_agent.this.id
}

output "agent_alias_id" {
  value = aws_bedrockagent_agent_alias.this.agent_alias_id
}
