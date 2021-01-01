resource "aws_s3_bucket" "tf" {
  bucket = "terraform.maurin.io"
  acl    = "private"

  versioning {
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "tf" {
  bucket = aws_s3_bucket.tf.bucket

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

