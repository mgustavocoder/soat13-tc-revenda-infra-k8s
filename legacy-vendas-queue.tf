# Fila de comandos do fluxo antigo (orquestrado) de vendas.
#
# Mantida temporariamente para que a migração para a saga coreografada seja
# feita em duas etapas: primeiro o deploy cria as filas de eventos e troca as
# aplicações; só depois esta fila é removida. Assim, se o apply falhar (por
# exemplo, por falta de sqs:CreateQueue nas filas novas), os pods antigos
# continuam funcionando.
#
# Remova este arquivo em um deploy posterior, depois de confirmar que vendas e
# veículos já usam vendas-eventos/veiculos-eventos e que esta fila está vazia.

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
