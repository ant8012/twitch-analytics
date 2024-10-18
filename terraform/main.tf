provider "aws" {
  region = var.region
}

terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}


resource "aws_secretsmanager_secret" "twitch_client_credentials" {
  name        = "${var.twitch_credentials.name}-${terraform.workspace}"
  description = "Twitch client credentials including client_id and client_secret"
}

resource "aws_secretsmanager_secret_version" "twitch_client_credentials_version" {
  secret_id = aws_secretsmanager_secret.twitch_client_credentials.id
  secret_string = jsonencode({
    client_id     = var.twitch_credentials.data.client_id
    client_secret = var.twitch_credentials.data.client_secret
  })

  depends_on = [aws_secretsmanager_secret.twitch_client_credentials]
}

resource "aws_s3_bucket" "twitch_data_bucket" {
  bucket = "${var.bucket.name}-${terraform.workspace}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_object" "twitch_data_prefix" {
  bucket     = aws_s3_bucket.twitch_data_bucket.bucket
  key        = "${var.bucket.prefix}/"
  depends_on = [aws_s3_bucket.twitch_data_bucket]

  lifecycle {
    prevent_destroy = true
  }
}


resource "aws_iam_role" "lambda_s3_role" {
  name = "${var.lambda.s3_role_name}-${terraform.workspace}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "lambda_secrets_policy" {
  name = "${var.lambda.secret_policy_name}-${terraform.workspace}"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue"
        ],
        Effect   = "Allow",
        Resource = aws_secretsmanager_secret.twitch_client_credentials.arn
      }
    ]
  })

  depends_on = [aws_secretsmanager_secret_version.twitch_client_credentials_version]
}

resource "aws_iam_policy" "lambda_s3_policy" {
  name = "${var.lambda.s3_policy_name}-${terraform.workspace}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject"
        ],
        Effect = "Allow",
        Resource = [
          aws_s3_bucket.twitch_data_bucket.arn,
          "${aws_s3_bucket.twitch_data_bucket.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_attach_policies" {
  for_each = {
    secrets_policy = aws_iam_policy.lambda_secrets_policy.arn
    s3_policy      = aws_iam_policy.lambda_s3_policy.arn
  }

  role       = aws_iam_role.lambda_s3_role.name
  policy_arn = each.value

  depends_on = [
    aws_iam_role.lambda_s3_role,
    aws_iam_policy.lambda_secrets_policy,
    aws_iam_policy.lambda_s3_policy,
  ]
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_function.zip"
  source {
    content  = file("${path.module}/../lambda/twitch_metrics_updater.py")
    filename = "twitch_metrics_updater.py"
  }

  source {
    content  = file("${path.module}/../lambda/aws_wrapper.py")
    filename = "aws_wrapper.py"
  }

  source {
    content  = file("${path.module}/../lambda/twitch_wrapper.py")
    filename = "twitch_wrapper.py"
  }
}

resource "aws_lambda_function" "twitch_get_streams_lambda" {
  function_name = "${var.lambda.name}-${terraform.workspace}"
  role          = aws_iam_role.lambda_s3_role.arn
  handler       = var.lambda.handler
  runtime       = var.lambda.runtime
  memory_size   = var.lambda.memory_size
  timeout       = var.lambda.timeout

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = filebase64sha256(data.archive_file.lambda_zip.output_path)

  layers = var.lambda.layers

  environment {
    variables = {
      S3_BUCKET_PATH          = "s3://${aws_s3_bucket.twitch_data_bucket.bucket}/${aws_s3_object.twitch_data_prefix.key}",
      TWITCH_CREDENTIALS_NAME = "${aws_secretsmanager_secret.twitch_client_credentials.name}"

    }
  }

  depends_on = [
    data.archive_file.lambda_zip,
    aws_iam_role_policy_attachment.lambda_attach_policies
  ]
}

resource "aws_cloudwatch_event_rule" "every_15_minutes" {
  name                = "${var.cloudwatch.name}-${terraform.workspace}"
  description         = "Triggers Lambda every 15 minutes"
  schedule_expression = var.cloudwatch.schedule_expression
}

resource "aws_cloudwatch_event_target" "trigger_lambda" {
  rule      = aws_cloudwatch_event_rule.every_15_minutes.name
  target_id = "lambda_target"
  arn       = aws_lambda_function.twitch_get_streams_lambda.arn

  depends_on = [
    aws_cloudwatch_event_rule.every_15_minutes,
    aws_lambda_function.twitch_get_streams_lambda,
  ]
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.twitch_get_streams_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_15_minutes.arn

  depends_on = [
    aws_lambda_function.twitch_get_streams_lambda,
    aws_cloudwatch_event_rule.every_15_minutes
  ]
}

resource "databricks_notebook" "twitch_notebook" {
  path     = "/Users/${var.databricks_pipeline.email}/${var.databricks.notebook}"
  format   = "SOURCE"
  source   = "${path.module}/../${var.databricks.notebook_path}/${var.databricks.notebook}"
}

resource "databricks_pipeline" "this" {
  name    = var.databricks.name
  configuration = {
    s3_bucket_path = var.databricks_pipeline.s3_bucket_path
  }

  target = "default"
  serverless = true
  catalog = var.databricks_pipeline.catalog
  photon = true
  continuous = false

  library {
    notebook {
      path = databricks_notebook.twitch_notebook.id
    }
  }

  filters {}
  development = true
}

resource "databricks_job" "this" {
  name = var.databricks.name

  task {
    task_key = var.databricks.task_key
    pipeline_task {
      pipeline_id = databricks_pipeline.this.id
    }
  }

  schedule {
    quartz_cron_expression = var.databricks.schedule_expression
    timezone_id            = var.databricks.timezone_id
  }

  depends_on = [
    databricks_notebook.twitch_notebook,
  ]

  email_notifications {
    on_failure = [var.databricks_pipeline.email]
  }
}