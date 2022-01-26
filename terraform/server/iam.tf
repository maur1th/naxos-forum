resource "aws_iam_instance_profile" "this" {
  name = local.name
  role = aws_iam_role.this.name
}

data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "this" {
  name               = local.name
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json
}

data "aws_s3_bucket" "this" {
  bucket = local.name
}

data "aws_iam_policy_document" "permissions" {
  statement {
    actions   = ["s3:ListBucket"]
    resources = [data.aws_s3_bucket.this.arn]
  }
  statement {
    actions = [
      "s3:DeleteObject",
      "s3:DeleteObjectVersion",
      "s3:GetObject",
      "s3:GetObjectAcl",
      "s3:GetObjectTagging",
      "s3:GetObjectVersion",
      "s3:PutObject",
      "s3:PutObjectAcl",
    ]
    resources = ["${data.aws_s3_bucket.this.arn}*"]
  }
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "permissions" {
  name   = "Permissions"
  role   = aws_iam_role.this.id
  policy = data.aws_iam_policy_document.permissions.json
}
