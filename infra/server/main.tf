variable "aws_region" {
  type = "string"
}

variable "bucket_name" {
  type = "string"
}

provider "aws" {
  region = "${var.aws_region}"
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnet_ids" "all" {
  vpc_id = "${data.aws_vpc.default.id}"
}

data "aws_ami" "amazon_linux" {
  most_recent = true

  owners = ["amazon"]

  filter {
    name = "name"

    values = [
      "amzn2-ami-hvm-*-x86_64-gp2",
    ]
  }

  filter {
    name = "owner-alias"

    values = [
      "amazon",
    ]
  }
}

module "container_registry" {
  source = "../container_registry"
}

resource "aws_iam_role" "this" {
  assume_role_policy = <<EOF
  {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "s3:*",
                "ecr:*",
            ],
            "Resource": [
                "arn:aws:s3:::${var.bucket_name}",
                "arn:aws:s3:::${var.bucket_name}/*",
                "arn:aws:ecr:*:*:repository/${module.container_registry.repo_url}"
            ]
        }
    ]
}
  EOF
}

resource "aws_iam_instance_profile" "this" {
  role = "${aws_iam_role.this.name}"
}

module "security_group" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "2.7.0"

  name        = "example"
  description = "Security group for example usage with EC2 instance"
  vpc_id      = "${data.aws_vpc.default.id}"

  ingress_cidr_blocks = ["0.0.0.0/0"]
  ingress_rules       = ["http-80-tcp"]
  egress_rules        = ["all-all"]
}

resource "aws_eip" "this" {
  vpc      = true
  instance = "${aws_instance.app-server.id}"
}

data "template_file" "this" {
  template = "${file("${path.module}/on_create.tpl")}"
  vars = {
    repo_url = "${module.container_registry.repo_url}"
  }
}

resource "aws_instance" "app-server" {
  ami                         = "${data.aws_ami.amazon_linux.id}"
  instance_type               = "t2.medium"
  subnet_id                   = "${element(data.aws_subnet_ids.all.ids, 0)}"
  vpc_security_group_ids      = ["${module.security_group.this_security_group_id}"]
  associate_public_ip_address = true
  iam_instance_profile        = "${aws_iam_instance_profile.this.name}"
  user_data                   = "${data.template_file.this}"

  root_block_device = [{
    volume_type = "gp2"
    volume_size = 10
  }]
}

output "url" {
  value = "${aws_eip.this.public_dns}"
}
