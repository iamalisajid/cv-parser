#!/bin/bash
set -euo pipefail
exec > /var/log/user-data.log 2>&1

# Install Docker
dnf update -y
dnf install -y docker git
systemctl enable docker
systemctl start docker

# Install Docker Compose
DOCKER_COMPOSE_VERSION="v2.29.7"
curl -SL "https://github.com/docker/compose/releases/download/$${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Add ec2-user to docker group
usermod -aG docker ec2-user

# Create project directory
mkdir -p /opt/${project_name}
cd /opt/${project_name}

# Write .env file
cat > .env <<'ENVEOF'
DATABASE_URL=postgresql://${db_username}:${db_password}@${db_host}:${db_port}/${db_name}
OPENAI_API_KEY=${openai_api_key}
GOOGLE_CLIENT_ID=${google_client_id}
VITE_GOOGLE_CLIENT_ID=${google_client_id}
JWT_SECRET=${jwt_secret}
CORS_ORIGINS=*
ALLOWED_EMAIL_DOMAIN=${allowed_email_domain}
ENVEOF

chown -R ec2-user:ec2-user /opt/${project_name}

# Clone and deploy if repo URL is provided
%{ if app_repo_url != "" }
git clone ${app_repo_url} /opt/${project_name}/app
cd /opt/${project_name}/app
cp /opt/${project_name}/.env .env
mkdir -p creds cvs output
docker-compose -f docker-compose.prod.yml up -d --build
%{ endif }

echo "User-data bootstrap complete at $(date)"
echo "Project directory: /opt/${project_name}"
%{ if app_repo_url == "" }
echo "No repo URL provided. To deploy manually:"
echo "  1. scp your project to /opt/${project_name}/app"
echo "  2. cd /opt/${project_name}/app"
echo "  3. cp /opt/${project_name}/.env .env"
echo "  4. docker-compose -f docker-compose.prod.yml up -d --build"
%{ endif }
