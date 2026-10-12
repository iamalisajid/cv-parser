data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_eip" "main" {
  domain = "vpc"
  tags   = { Name = "${var.project_name}-eip" }
}

resource "aws_eip_association" "main" {
  instance_id   = aws_instance.app.id
  allocation_id = aws_eip.main.id
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  key_name               = var.ssh_key_name
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    db_host              = aws_db_instance.postgres.address
    db_port              = aws_db_instance.postgres.port
    db_name              = var.db_name
    db_username          = var.db_username
    db_password          = var.db_password
    openai_api_key       = var.openai_api_key
    google_client_id     = var.google_client_id
    jwt_secret           = var.jwt_secret
    allowed_email_domain = var.allowed_email_domain
    project_name         = var.project_name
    app_repo_url         = var.app_repo_url
  }))

  tags = { Name = "${var.project_name}-app" }

  depends_on = [aws_db_instance.postgres]
}
