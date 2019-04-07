variable "bucket_name" {
  type = "string"
}

variable "repo_name" {
  type        = "string"
  description = "The name of the ECR repository"
}

variable "instance_type" {
  type        = "string"
  description = "The type of EC2 instance to create"
}

data "aws_region" "current" {}

data "aws_ecr_repository" "this" {
  name = "${var.repo_name}"
}

data "aws_s3_bucket" "this" {
  bucket = "${var.bucket_name}"
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

data "aws_iam_policy_document" "role_policy" {
  statement = {
    actions = [
      "sts:AssumeRole",
    ]

    principals = {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "this" {
  assume_role_policy = "${data.aws_iam_policy_document.role_policy.json}"
}

data "aws_iam_policy_document" "read_s3_ecr" {
  statement = {
    actions = [
      "s3:ListAllMyBuckets",
    ]

    resources = [
      "*",
    ]
  }

  statement = {
    actions = [
      "s3:ListBucket",
      "s3:GetObject",
    ]

    resources = [
      "${data.aws_s3_bucket.this.arn}",
      "${data.aws_s3_bucket.this.arn}/*",
    ]
  }

  statement = {
    actions = [
      "ecr:GetAuthorizationToken",
    ]

    resources = [
      "*",
    ]
  }

  statement = {
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:GetRepositoryPolicy",
      "ecr:DescribeRepositories",
      "ecr:ListImages",
      "ecr:DescribeImages",
      "ecr:BatchGetImage",
    ]

    resources = [
      "${data.aws_ecr_repository.this.arn}",
    ]
  }
}

resource "aws_iam_role_policy" "this" {
  role   = "${aws_iam_role.this.id}"
  policy = "${data.aws_iam_policy_document.read_s3_ecr.json}"
}

resource "aws_iam_instance_profile" "this" {
  role = "${aws_iam_role.this.name}"
}

resource "aws_security_group" "this" {
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_eip" "this" {
  vpc      = true
  instance = "${aws_instance.this.id}"
}

data "template_file" "this" {
  template = "${file("${path.module}/on_create.tpl")}"

  vars = {
    repo_url = "${data.aws_ecr_repository.this.repository_url}"
    region   = "${data.aws_region.current.name}"
  }
}

resource "aws_instance" "this" {
  ami                         = "${data.aws_ami.amazon_linux.id}"
  instance_type               = "${var.instance_type}"
  subnet_id                   = "${element(data.aws_subnet_ids.all.ids, 0)}"
  vpc_security_group_ids      = ["${aws_security_group.this.id}"]
  associate_public_ip_address = true
  iam_instance_profile        = "${aws_iam_instance_profile.this.name}"
  user_data                   = "${data.template_file.this.rendered}"

  root_block_device = [{
    volume_type = "gp2"
    volume_size = 10
  }]
}

output "url" {
  value = "${aws_eip.this.public_dns}"
}
