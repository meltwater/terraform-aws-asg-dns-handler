resource "aws_sns_topic" "autoscale_handling" {
  name = format("%s-%s", var.vpc_name, var.autoscale_handler_unique_identifier)
}

resource "aws_sns_topic" "autoscale_multihost_handling" {
  name = format("%s-%s-multi", var.vpc_name, var.autoscale_handler_unique_identifier)
}

resource "aws_iam_role_policy" "autoscale_handling" {
  name = format("%s-%s", var.vpc_name, var.autoscale_handler_unique_identifier)
  role = aws_iam_role.autoscale_handling.name

  policy = data.aws_iam_policy_document.autoscale_handling_document.json
}

data "aws_iam_policy_document" "autoscale_handling_document" {
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = [
      "arn:aws:logs:*:*:*"
    ]
  }
  statement {
    actions = [
      "autoscaling:DescribeTags",
      "autoscaling:DescribeAutoScalingGroups",
      "autoscaling:CompleteLifecycleAction",
      "ec2:DescribeInstances",
      "route53:GetHostedZone",
      "ec2:CreateTags"
    ]
    resources = [
      "*"
    ]
  }
  statement {
    actions = [
      "route53:ChangeResourceRecordSets",
      "route53:ListResourceRecordSets"
    ]
    resources = [
      format("arn:aws:route53:::hostedzone/%s", var.autoscale_route53zone_arn)
    ]
  }
}

resource "aws_iam_role" "autoscale_handling" {
  name               = format("%s-%s", var.vpc_name, var.autoscale_handler_unique_identifier)
  assume_role_policy = data.aws_iam_policy_document.assume_lambda_role_policy_document.json
}

data "aws_iam_policy_document" "assume_lambda_role_policy_document" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lifecycle" {
  name               = format("%s-%s-lifecycle", var.vpc_name, var.autoscale_handler_unique_identifier)
  assume_role_policy = data.aws_iam_policy_document.lifecycle_role.json
}

data "aws_iam_policy_document" "lifecycle_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["autoscaling.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "lifecycle_policy" {
  name   = format("%s-%s-lifecycle", var.vpc_name, var.autoscale_handler_unique_identifier)
  role   = aws_iam_role.lifecycle.id
  policy = data.aws_iam_policy_document.lifecycle_policy.json
}

data "aws_iam_policy_document" "lifecycle_policy" {
  statement {
    effect    = "Allow"
    actions   = ["sns:Publish", "autoscaling:CompleteLifecycleAction"]
    resources = [aws_sns_topic.autoscale_handling.arn, aws_sns_topic.autoscale_multihost_handling.arn]
  }
}

data "archive_file" "autoscale" {
  type        = "zip"
  source_file = format("%s/lambda/autoscale/autoscale.py", path.module)
  output_path = format("%s/lambda/dist/autoscale.zip", path.module)
}

resource "aws_lambda_function" "autoscale_handling" {
  depends_on = [aws_sns_topic.autoscale_handling]

  filename         = data.archive_file.autoscale.output_path
  function_name    = format("%s-%s", var.vpc_name, var.autoscale_handler_unique_identifier)
  role             = aws_iam_role.autoscale_handling.arn
  handler          = "autoscale.lambda_handler"
  runtime          = "python3.8"
  source_code_hash = filebase64sha256(data.archive_file.autoscale.output_path)
  description      = "Handles DNS for autoscaling groups by receiving autoscaling notifications and setting/deleting records from route53"
  environment {
    variables = {
      "use_public_ip" = var.use_public_ip
    }
  }
}

resource "aws_lambda_permission" "autoscale_handling" {
  depends_on = [aws_lambda_function.autoscale_handling]

  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.autoscale_handling.arn
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.autoscale_handling.arn
}

resource "aws_sns_topic_subscription" "autoscale_handling" {
  depends_on = [aws_lambda_permission.autoscale_handling]

  topic_arn = aws_sns_topic.autoscale_handling.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.autoscale_handling.arn
}

data "archive_file" "multihost" {
  type        = "zip"
  source_file = format("%s/lambda/multihost/multihost.py", path.module)
  output_path = format("%s/lambda/dist/multihost.zip", path.module)
}

resource "aws_lambda_function" "autoscale_multihost_handling" {
  depends_on = [aws_sns_topic.autoscale_multihost_handling]

  filename         = data.archive_file.multihost.output_path
  function_name    = format("%s-%s-multi", var.vpc_name, var.autoscale_handler_unique_identifier)
  role             = aws_iam_role.autoscale_handling.arn
  handler          = "multihost.lambda_handler"
  runtime          = "python3.8"
  source_code_hash = filebase64sha256(data.archive_file.multihost.output_path)
  description      = "Handles DNS for autoscaling groups by receiving autoscaling notifications and setting/deleting records from route53"
  environment {
    variables = {
      "use_public_ip" = var.use_public_ip
    }
  }
}

resource "aws_lambda_permission" "autoscale_multihost_handling" {
  depends_on = [aws_lambda_function.autoscale_multihost_handling]

  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.autoscale_multihost_handling.arn
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.autoscale_multihost_handling.arn
}

resource "aws_sns_topic_subscription" "autoscale_multihost_handling" {
  depends_on = [aws_lambda_permission.autoscale_multihost_handling]

  topic_arn = aws_sns_topic.autoscale_multihost_handling.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.autoscale_multihost_handling.arn
}
