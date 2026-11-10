locals {
  api_gateway_enabled = var.load_balancer_listener_arn != ""
}

resource "aws_security_group" "api_gateway_vpc_link" {
  count       = local.api_gateway_enabled ? 1 : 0
  name        = "${var.project_name}-apigw-vpc-link"
  description = "Egress from API Gateway VPC Link to the internal ALB."
  vpc_id      = module.vpc.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }
}

resource "aws_apigatewayv2_vpc_link" "main" {
  count              = local.api_gateway_enabled ? 1 : 0
  name               = "${var.project_name}-vpc-link"
  security_group_ids = [aws_security_group.api_gateway_vpc_link[0].id]
  subnet_ids         = module.vpc.private_subnets
}

resource "aws_apigatewayv2_api" "main" {
  count         = local.api_gateway_enabled ? 1 : 0
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"
  description   = "Public API Gateway for Clientes, Veiculos, and Vendas."

  cors_configuration {
    allow_headers = ["Content-Type", "Authorization"]
    allow_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    allow_origins = ["*"]
    max_age       = 3600
  }
}

resource "aws_apigatewayv2_integration" "main" {
  count                  = local.api_gateway_enabled ? 1 : 0
  api_id                 = aws_apigatewayv2_api.main[0].id
  integration_type       = "HTTP_PROXY"
  integration_uri        = var.load_balancer_listener_arn
  integration_method     = "ANY"
  connection_type        = "VPC_LINK"
  connection_id          = aws_apigatewayv2_vpc_link.main[0].id
  payload_format_version = "1.0"
}

resource "aws_apigatewayv2_route" "default" {
  count              = local.api_gateway_enabled ? 1 : 0
  api_id             = aws_apigatewayv2_api.main[0].id
  route_key          = "$default"
  target             = "integrations/${aws_apigatewayv2_integration.main[0].id}"
  authorization_type = "AWS_IAM"
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  count             = local.api_gateway_enabled ? 1 : 0
  name              = "/aws/apigateway/${var.project_name}"
  retention_in_days = 7
}

resource "aws_apigatewayv2_stage" "main" {
  count       = local.api_gateway_enabled ? 1 : 0
  api_id      = aws_apigatewayv2_api.main[0].id
  name        = "v1"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway[0].arn
    format = jsonencode({
      requestId   = "$context.requestId"
      sourceIp    = "$context.identity.sourceIp"
      requestTime = "$context.requestTime"
      routeKey    = "$context.routeKey"
      status      = "$context.status"
    })
  }
}

output "api_gateway_url" {
  value       = local.api_gateway_enabled ? aws_apigatewayv2_stage.main[0].invoke_url : null
  description = "Public API Gateway URL, available after the internal ALB listener ARN is configured."
}
