variable "bucket_name" {
  type        = "string"
  description = "The S3 bucket where models are stored"
}

variable "aws_region" {
  type        = "string"
  description = "The AWS region"
}

provider "aws" {
  region = "${var.aws_region}"
}

resource "aws_s3_bucket" "b" {
  bucket = "${var.bucket_name}"
  acl    = "private"
}
