variable "region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

variable "twitch_credentials" {
  description = "Twitch credentials"
  type = object({
    name = string

    data = object({
      client_id     = string
      client_secret = string
    })
  })

  default = {
    name = "CHANGEME"
    data = {
      client_id     = "CHANGEME"
      client_secret = "CHANGEME"
    }
  }
}

variable "bucket" {
  description = "S3 Bucket to hold Twitch data"
  type = object({
    name   = string
    prefix = string
  })
  default = {
    name   = "CHANGEME"
    prefix = "stream_updates"
  }
}

variable "lambda" {
  description = "Lambda variables"
  type = object({
    name               = string
    handler            = string
    runtime            = string
    memory_size        = number
    timeout            = number
    s3_role_name       = string
    s3_policy_name     = string
    secret_policy_name = string

    layers = list(string)

  })
  default = {
    name               = "twitch_get_stream_data"
    handler            = "twitch_metrics_updater.handle"
    runtime            = "python3.10"
    memory_size        = 512
    timeout            = 600
    s3_role_name       = "twitch_lambda_s3_role"
    s3_policy_name     = "twitch_lambda_s3_policy"
    secret_policy_name = "twitch_lambda_secrets_policy"
    layers = [
      "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python310:20",
      "arn:aws:lambda:us-east-1:177933569100:layer:AWS-Parameters-and-Secrets-Lambda-Extension:11"
    ]
  }
}

variable "cloudwatch" {
  description = "Cloudwatch variables"
  type = object({
    name                = string
    schedule_expression = string
  })
  default = {
    name                = "trigger_twitch_lambda_every_15_minutes"
    schedule_expression = "cron(0/15 * * * ? *)"
  }
}
