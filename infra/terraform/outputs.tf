output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.juakazi.repository_url
}

output "app_runner_url" {
  description = "App Runner service URL"
  value       = aws_apprunner_service.juakazi.service_url
}
