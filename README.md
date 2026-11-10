# SOAT13 Revenda - EKS, ECR and API Gateway

Terraform and Kubernetes deployment for the Clientes, Veiculos, and Vendas
microservices. The stack creates a VPC, private EKS workers, ECR repositories,
an internal ALB ingress, and an HTTP API Gateway connected through a VPC Link.
The RDS stack is maintained in `soat13-tc-revenda-infra-db`.

## Security and cost

- Use AWS CLI/IAM Identity Center credentials; no access keys are stored in
  Terraform variables or this repository.
- Set `kubectl_cidr_allowlist` to a trusted public IP CIDR. Do not use
  `0.0.0.0/0`.
- RDS and the ALB are private. Only API Gateway is public, and every route
  requires AWS IAM/SigV4 authorization; the caller role needs
  `execute-api:Invoke` on the deployed API.
- The default stack creates two `t3.medium` EKS workers, an EKS control plane,
  an internal ALB, a NAT Gateway, three RDS instances, ECR, and API Gateway.
  These resources incur ongoing AWS charges. Review the current regional AWS
  pricing and quotas before applying.
- Terraform state contains sensitive infrastructure values. Use the private,
  encrypted, versioned S3 bucket created by `scripts/bootstrap-state.sh`.

## Prerequisites

AWS CLI, Terraform >= 1.9, Docker, `kubectl`, `jq`, `curl`, and access to the
AWS Load Balancer Controller Helm chart. Configure an AWS CLI profile for
the new account after revoking any exposed keys.

```sh
export AWS_PROFILE=default
export AWS_REGION=us-east-1
export TF_STATE_BUCKET='your-globally-unique-state-bucket'
export KUBECTL_CIDR_ALLOWLIST='YOUR_PUBLIC_IP/32'
export DB_MASTER_USERNAME='application_db_admin'
export DB_MASTER_PASSWORD='use-a-unique-strong-password'
bash scripts/bootstrap-state.sh
bash scripts/deploy.sh
```

The deploy script applies EKS/ECR, creates the private database tier, builds and
pushes the three application images, initializes each RDS schema using the
service's `database/init.sql`, applies Kubernetes resources, discovers
the internal ALB listener, and connects API Gateway. Supply the service source
directories through `CLIENTES_DIR`, `VEICULOS_DIR`, and `VENDAS_DIR` when they
are not adjacent to this repository. Do not put credentials in `terraform.tfvars`.

The deployment uses two Terraform applies for the API Gateway because the
internal ALB listener is created by the Kubernetes ingress controller after
the first EKS apply.

## Production smoke test

After deployment, call the public API Gateway URL using the configured AWS CLI
profile. Requests are signed with SigV4; response bodies are not printed.

```sh
export API_BASE_URL="$(terraform output -raw api_gateway_url)"
bash scripts/smoke-test.sh
```

The smoke test sends read-only GET requests to the health, customer, available
vehicle, and sales-list endpoints.
