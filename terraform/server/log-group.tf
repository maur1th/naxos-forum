resource "aws_cloudwatch_log_group" "this" {
  name              = local.name
  retention_in_days = 14

  tags = local.tags
}
