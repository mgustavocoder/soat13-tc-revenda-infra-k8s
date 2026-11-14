# Saga coreografada de vendas.
#
# Cada serviço publica os seus eventos de domínio na própria fila e consome a
# fila de eventos do outro serviço. Não há orquestrador central:
#
#   vendas   --VENDA_CRIADA / PAGAMENTO_RECEBIDO / VENDA_CANCELADA-->  vendas-eventos   --> veiculos-worker
#   veiculos --VEICULO_RESERVADO / *_FALHOU / VENDIDO / LIBERADO----->  veiculos-eventos --> vendas-worker
#
# Filas standard (entrega pelo menos uma vez): os consumidores são idempotentes.
# Mensagens que excedem maxReceiveCount vão para a DLQ de cada fila.

locals {
  event_queues = {
    vendas-eventos   = { service = "vendas" }
    veiculos-eventos = { service = "veiculos" }
  }

  # Permissões de cada ServiceAccount: publica na própria fila e consome a do outro serviço.
  queue_access = {
    vendas = {
      publishes = "vendas-eventos"
      consumes  = "veiculos-eventos"
    }
    veiculos = {
      publishes = "veiculos-eventos"
      consumes  = "vendas-eventos"
    }
  }

  oidc_issuer = replace(module.eks.cluster_oidc_issuer_url, "https://", "")
}

resource "aws_sqs_queue" "events_dlq" {
  for_each = local.event_queues

  name                      = "${var.project_name}-${each.key}-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true

  tags = {
    Project = var.project_name
    Service = each.value.service
  }
}

resource "aws_sqs_queue" "events" {
  for_each = local.event_queues

  name                       = "${var.project_name}-${each.key}"
  message_retention_seconds  = 345600
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = 180
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.events_dlq[each.key].arn
    maxReceiveCount     = 5
  })

  tags = {
    Project = var.project_name
    Service = each.value.service
  }
}

data "aws_iam_policy_document" "queue_assume_role" {
  for_each = local.queue_access

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [module.eks.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:sub"
      values   = ["system:serviceaccount:revenda:${each.key}"]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "queue" {
  for_each = local.queue_access

  name               = "${var.project_name}-${each.key}-sqs"
  assume_role_policy = data.aws_iam_policy_document.queue_assume_role[each.key].json

  tags = {
    Project = var.project_name
    Service = each.key
  }
}

data "aws_iam_policy_document" "queue_access" {
  for_each = local.queue_access

  statement {
    sid       = "PublishOwnEvents"
    actions   = ["sqs:GetQueueAttributes", "sqs:SendMessage"]
    resources = [aws_sqs_queue.events[each.value.publishes].arn]
  }

  statement {
    sid = "ConsumePeerEvents"
    actions = [
      "sqs:ChangeMessageVisibility",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:ReceiveMessage"
    ]
    resources = [aws_sqs_queue.events[each.value.consumes].arn]
  }
}

resource "aws_iam_role_policy" "queue_access" {
  for_each = local.queue_access

  name   = "${var.project_name}-${each.key}-sqs"
  role   = aws_iam_role.queue[each.key].id
  policy = data.aws_iam_policy_document.queue_access[each.key].json
}

moved {
  from = aws_iam_role.vendas_queue
  to   = aws_iam_role.queue["vendas"]
}

moved {
  from = aws_iam_role_policy.vendas_queue_access
  to   = aws_iam_role_policy.queue_access["vendas"]
}

output "vendas_eventos_queue_url" {
  description = "SQS queue where the sales service publishes its saga events."
  value       = aws_sqs_queue.events["vendas-eventos"].url
}

output "veiculos_eventos_queue_url" {
  description = "SQS queue where the vehicles service publishes its saga events."
  value       = aws_sqs_queue.events["veiculos-eventos"].url
}

output "vendas_queue_role_arn" {
  description = "IRSA role ARN used by the sales API and worker."
  value       = aws_iam_role.queue["vendas"].arn
}

output "veiculos_queue_role_arn" {
  description = "IRSA role ARN used by the vehicles worker."
  value       = aws_iam_role.queue["veiculos"].arn
}
