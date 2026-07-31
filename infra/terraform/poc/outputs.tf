output "public_ip" {
  description = "Elastic IP of the POC instance → set as GitHub secret EC2_HOST."
  value       = aws_eip.app.public_ip
}

output "public_dns" {
  description = "Public DNS of the instance."
  value       = aws_instance.app.public_dns
}

output "ssh_command" {
  description = "Convenience SSH command (use your matching private key)."
  value       = "ssh ubuntu@${aws_eip.app.public_ip}"
}

output "app_url" {
  description = "App URL once the stack is deployed (frontend on port 80)."
  value       = "http://${aws_eip.app.public_ip}"
}

output "frontend_bucket" {
  description = "S3 frontend bucket (only when enable_s3_frontend = true)."
  value       = var.enable_s3_frontend ? aws_s3_bucket.frontend[0].bucket : null
}

output "frontend_website_endpoint" {
  description = "S3 website endpoint (only when enable_s3_frontend = true)."
  value       = var.enable_s3_frontend ? aws_s3_bucket_website_configuration.frontend[0].website_endpoint : null
}

output "github_secrets_hint" {
  description = "What to put in GitHub → Settings → Secrets and variables → Actions."
  value = {
    EC2_HOST     = aws_eip.app.public_ip
    EC2_USERNAME = "ubuntu"
    EC2_SSH_KEY  = "<contents of the PRIVATE key matching ssh_public_key>"
    OPENAI_API_KEY = "<your key, optional>"
    JWT_SECRET     = "<a long random string>"
  }
}
