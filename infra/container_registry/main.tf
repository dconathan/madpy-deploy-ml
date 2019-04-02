variable "repo_name" {
  type        = "string"
  description = "The name of the ECR repository"
}

variable "aws_region" {
  type        = "string"
  description = "The AWS region"
}

provider "aws" {
  region = "${var.aws_region}"
}

resource "aws_ecr_repository" "this" {
  name = "${var.repo_name}"
}

output "repo_url" {
  value = "${aws_ecr_repository.this.repository_url}"
}
