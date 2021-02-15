data "aws_ami" "amazon_linux" {
  most_recent = true

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-2.0.*-arm64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["137112412989"]
}

data "aws_subnet_ids" "selected" {
  vpc_id = data.aws_vpc.selected.id
}

resource "random_shuffle" "subnet_ids" {
  input        = data.aws_subnet_ids.selected.ids
  result_count = 1
}

resource "aws_instance" "this" {
  ami                  = data.aws_ami.amazon_linux.image_id
  instance_type        = "t4g.micro"
  subnet_id            = random_shuffle.subnet_ids.result[0]
  security_groups      = [aws_security_group.this.name]
  key_name             = aws_key_pair.tmaurin_change.key_name
  iam_instance_profile = aws_iam_instance_profile.this.name

  tags = {
    Name = local.name
  }

  lifecycle {
    ignore_changes = [ami]
  }
}

resource "aws_eip" "this" {
  instance = aws_instance.this.id
  vpc      = true

  tags = {
    Name = local.name
  }
}
