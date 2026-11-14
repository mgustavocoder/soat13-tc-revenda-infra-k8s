resource "aws_sqs_queue" "vendas_dlq" {
  name                      = "${var.project_name}-vendas-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true

  tags = {
    Project = var.project_name
    Service = "vendas"
  }
}

resource "aws_sqs_queue" "vendas" {
  name                       = "${var.project_name}-vendas"
  message_retention_seconds  = 345600
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = 180
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.vendas_dlq.arn
    maxReceiveCount     = 5
  })

  tags = {
    Project = var.project_name
    Service = "vendas"
  }
}

data "aws_iam_policy_document" "vendas_queue_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [module.eks.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(module.eks.cluster_oidc_issuer_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:revenda:vendas"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(module.eks.cluster_oidc_issuer_url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "vendas_queue" {
  name               = "${var.project_name}-vendas-sqs"
  assume_role_policy = data.aws_iam_policy_document.vendas_queue_assume_role.json

  tags = {
    Project = var.project_name
    Service = "vendas"
  }
}

data "aws_iam_policy_document" "vendas_queue_access" {
  statement {
    actions = [
      "sqs:ChangeMessageVisibility",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:ReceiveMessage",
      "sqs:SendMessage"
    ]
    resources = [aws_sqs_queue.vendas.arn]
  }
}

resource "aws_iam_role_policy" "vendas_queue_access" {
  name   = "${var.project_name}-vendas-sqs"
  role   = aws_iam_role.vendas_queue.id
  policy = data.aws_iam_policy_document.vendas_queue_access.json
}

output "vendas_queue_url" {
  description = "SQS queue URL for asynchronous sales operations."
  value       = aws_sqs_queue.vendas.url
}

output "vendas_queue_role_arn" {
  description = "IRSA role ARN used by the sales API and queue worker."
  value       = aws_iam_role.vendas_queue.arn
}
