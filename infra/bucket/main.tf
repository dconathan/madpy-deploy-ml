variable "bucket_name" {
  type        = "string"
  description = "The name of the S3 bucket where models are stored"
}

resource "aws_s3_bucket" "this" {
  bucket = "${var.bucket_name}"
}
