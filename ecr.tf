locals {
  services = toset(["clientes", "veiculos", "vendas"])
}

resource "aws_ecr_repository" "service" {
  for_each = local.services

  name                 = "${var.project_name}-${each.value}"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Project = var.project_name
    Service = each.value
  }
}

resource "aws_ecr_lifecycle_policy" "service" {
  for_each   = local.services
  repository = aws_ecr_repository.service[each.value].name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the latest 10 images."
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

output "ecr_repository_urls" {
  value       = { for service, repository in aws_ecr_repository.service : service => repository.repository_url }
  description = "ECR URLs for the three application services."
}
