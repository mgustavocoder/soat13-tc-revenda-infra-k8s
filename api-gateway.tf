locals {
  api_gateway_enabled = var.load_balancer_listener_arn != ""
  api_gateway_rest_body = jsonencode({
    swagger = "2.0"
    info = {
      title   = "${var.project_name}-api"
      version = "1.0"
    }
    schemes                              = ["https"]
    "x-amazon-apigateway-api-key-source" = "HEADER"
    securityDefinitions = {
      api_key = {
        type = "apiKey"
        name = "x-api-key"
        in   = "header"
      }
    }
    paths = {
      "/{proxy+}" = {
        parameters = [
          {
            name     = "proxy"
            in       = "path"
            required = true
            type     = "string"
          }
        ]
        "x-amazon-apigateway-any-method" = {
          security = [{ api_key = [] }]
          responses = {
            "200" = { description = "Microservice response" }
          }
          "x-amazon-apigateway-integration" = {
            type              = "http_proxy"
            httpMethod        = "ANY"
            uri               = "http://${data.aws_lb.api_gateway[0].dns_name}/{proxy}"
            connectionType    = "VPC_LINK"
            connectionId      = aws_apigatewayv2_vpc_link.main[0].id
            integrationTarget = data.aws_lb.api_gateway[0].arn
            requestParameters = {
              "integration.request.path.proxy" = "method.request.path.proxy"
            }
          }
        }
        options = {
          responses = {
            "200" = {
              description = "CORS preflight response"
              headers = {
                "Access-Control-Allow-Headers" = { type = "string" }
                "Access-Control-Allow-Methods" = { type = "string" }
                "Access-Control-Allow-Origin"  = { type = "string" }
                "Access-Control-Max-Age"       = { type = "string" }
              }
            }
          }
          "x-amazon-apigateway-integration" = {
            type = "mock"
            requestTemplates = {
              "application/json" = "{\"statusCode\": 200}"
            }
            responses = {
              default = {
                statusCode = "200"
                responseParameters = {
                  "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-API-Key'"
                  "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,PATCH,DELETE,OPTIONS'"
                  "method.response.header.Access-Control-Allow-Origin"  = "'*'"
                  "method.response.header.Access-Control-Max-Age"       = "'3600'"
                }
              }
            }
          }
        }
      }
    }
  })
}

data "aws_lb_listener" "api_gateway" {
  count = local.api_gateway_enabled ? 1 : 0
  arn   = var.load_balancer_listener_arn
}

data "aws_lb" "api_gateway" {
  count = local.api_gateway_enabled ? 1 : 0
  arn   = data.aws_lb_listener.api_gateway[0].load_balancer_arn
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

resource "aws_api_gateway_rest_api" "keyed" {
  count = local.api_gateway_enabled ? 1 : 0

  name              = "${var.project_name}-public-api"
  description       = "Public REST API protected by an API key."
  api_key_source    = "HEADER"
  body              = local.api_gateway_rest_body
  fail_on_warnings  = true
  put_rest_api_mode = "overwrite"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_deployment" "keyed" {
  count       = local.api_gateway_enabled ? 1 : 0
  rest_api_id = aws_api_gateway_rest_api.keyed[0].id

  triggers = {
    redeployment = sha1(local.api_gateway_rest_body)
  }

  depends_on = [aws_api_gateway_rest_api.keyed]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "keyed" {
  count         = local.api_gateway_enabled ? 1 : 0
  rest_api_id   = aws_api_gateway_rest_api.keyed[0].id
  deployment_id = aws_api_gateway_deployment.keyed[0].id
  stage_name    = "v1"
}

resource "aws_api_gateway_api_key" "client" {
  count       = local.api_gateway_enabled ? 1 : 0
  name        = "${var.project_name}-public-client"
  description = "Shared API key for public API access."
  enabled     = true
}

resource "aws_api_gateway_usage_plan" "client" {
  count = local.api_gateway_enabled ? 1 : 0
  name  = "${var.project_name}-public-client"

  api_stages {
    api_id = aws_api_gateway_rest_api.keyed[0].id
    stage  = aws_api_gateway_stage.keyed[0].stage_name
  }

  throttle_settings {
    burst_limit = 20
    rate_limit  = 10
  }
}

resource "aws_api_gateway_usage_plan_key" "client" {
  count         = local.api_gateway_enabled ? 1 : 0
  key_id        = aws_api_gateway_api_key.client[0].id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.client[0].id
}

output "api_gateway_url" {
  value       = local.api_gateway_enabled ? aws_api_gateway_stage.keyed[0].invoke_url : null
  description = "Public REST API Gateway URL, available after the internal ALB listener ARN is configured."
}

output "api_gateway_api_key" {
  value       = local.api_gateway_enabled ? aws_api_gateway_api_key.client[0].value : null
  sensitive   = true
  description = "Shared API key for requests in the x-api-key header."
}
