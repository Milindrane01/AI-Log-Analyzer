# Canonical's official Ubuntu 24.04 LTS AMI id for this region (via SSM public parameter)
data "aws_ssm_parameter" "ubuntu_2404" {
  name = "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id"
}

# Key pair created from YOUR public key; keep the matching private key safe
# (it becomes the GitHub secret EC2_SSH_KEY).
resource "aws_key_pair" "poc" {
  key_name   = "${var.project_name}-poc"
  public_key = var.ssh_public_key
}

resource "aws_instance" "app" {
  ami                    = nonsensitive(data.aws_ssm_parameter.ubuntu_2404.value)
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.app.id]
  key_name               = aws_key_pair.poc.key_name

  root_block_device {
    volume_size = var.root_volume_gb
    volume_type = "gp3"
    encrypted   = true
  }

  user_data = templatefile("${path.module}/user_data.sh", {
    project_name = var.project_name
  })

  # Re-run bootstrap if user_data changes
  user_data_replace_on_change = true

  tags = { Name = "${var.project_name}-poc" }
}

# Stable public IP that survives stop/start
resource "aws_eip" "app" {
  domain   = "vpc"
  instance = aws_instance.app.id
  tags     = { Name = "${var.project_name}-poc-eip" }
}
