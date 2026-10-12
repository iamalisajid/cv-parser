variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "cv-parser"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "cvparser"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "cvparser"
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "ssh_key_name" {
  description = "Name of an existing EC2 key pair for SSH access"
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed for SSH access (e.g. your IP/32)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "openai_api_key" {
  description = "OpenAI API key for skill extraction"
  type        = string
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth client ID for web login"
  type        = string
}

variable "jwt_secret" {
  description = "Secret key for signing JWT session tokens"
  type        = string
  sensitive   = true
}

variable "allowed_email_domain" {
  description = "Optional Google email domain allowed to sign in; empty allows any verified Google account"
  type        = string
  default     = ""
}

variable "app_repo_url" {
  description = "Git repository URL to clone on the EC2 instance"
  type        = string
  default     = ""
}
