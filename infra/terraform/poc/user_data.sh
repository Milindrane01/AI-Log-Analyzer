#!/usr/bin/env bash
# EC2 bootstrap: install Docker Engine + Compose plugin on Ubuntu 24.04.
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ca-certificates curl gnupg

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Let the 'ubuntu' user run docker without sudo (used by the deploy workflow)
usermod -aG docker ubuntu
systemctl enable --now docker

# Prepare the app directory the CI workflow deploys into
mkdir -p /home/ubuntu/${project_name}
chown -R ubuntu:ubuntu /home/ubuntu/${project_name}
