# Lambda Functions
resource "aws_lambda_function" "payment_monitor" {
  filename         = var.lambda_payload
  function_name    = "${var.environment}-payment-monitor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"

  environment {
    variables = {
      ENVIRONMENT = var.environment
      DB_HOST     = var.db_host
    }
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.environment}-flexrp-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ... more compute resources 