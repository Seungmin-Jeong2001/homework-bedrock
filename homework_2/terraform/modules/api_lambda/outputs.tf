output "webhook_url" {
  value = "${aws_apigatewayv2_api.http.api_endpoint}/github/webhook"
}

output "lambda_function_name" {
  value = aws_lambda_function.orchestrator.function_name
}

output "cloudwatch_log_group_name" {
  value = aws_cloudwatch_log_group.lambda.name
}
