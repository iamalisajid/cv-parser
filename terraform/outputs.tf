output "ec2_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_eip.main.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_address" {
  description = "RDS hostname (without port)"
  value       = aws_db_instance.postgres.address
}

output "database_url" {
  description = "Full DATABASE_URL for the application"
  value       = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${var.db_name}"
  sensitive   = true
}

output "ssh_command" {
  description = "SSH command to connect to EC2"
  value       = "ssh -i <key>.pem ec2-user@${aws_eip.main.public_ip}"
}

output "app_url" {
  description = "Application URL (HTTP direct)"
  value       = "http://${aws_eip.main.public_ip}"
}

output "cloudfront_domain" {
  description = "CloudFront domain with HTTPS"
  value       = aws_cloudfront_distribution.app.domain_name
}

output "cloudfront_url" {
  description = "Application URL (HTTPS via CloudFront)"
  value       = "https://${aws_cloudfront_distribution.app.domain_name}"
}
