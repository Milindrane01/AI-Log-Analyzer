variable "aws_region" {
  description = "AWS region to deploy the POC into."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name prefix for all resources."
  type        = string
  default     = "ai-log-analyzer"
}

variable "instance_type" {
  description = "EC2 instance type. t3.large recommended (worker runs sentence-transformers/torch)."
  type        = string
  default     = "t3.large"
}

variable "root_volume_gb" {
  description = "Root EBS volume size in GB (gp3)."
  type        = number
  default     = 40
}

variable "ssh_public_key" {
  description = "Contents of your SSH PUBLIC key (e.g. contents of ~/.ssh/id_ed25519.pub). The matching PRIVATE key goes into the GitHub secret EC2_SSH_KEY."
  type        = string
}

variable "ssh_allowed_cidr" {
  description = "CIDR allowed to SSH (port 22). Set to YOUR.IP/32 — never 0.0.0.0/0 in real use."
  type        = string
  default     = "0.0.0.0/0"
}

variable "http_allowed_cidr" {
  description = "CIDR allowed to reach HTTP/HTTPS (80/443)."
  type        = string
  default     = "0.0.0.0/0"
}

variable "enable_s3_frontend" {
  description = "If true, create an S3 static-website bucket for the React frontend (Phase 4). For the basic POC the frontend is served by the Nginx container on EC2, so leave false."
  type        = bool
  default     = false
}

variable "vpc_cidr" {
  description = "CIDR for the POC VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR for the single public subnet."
  type        = string
  default     = "10.20.1.0/24"
}
