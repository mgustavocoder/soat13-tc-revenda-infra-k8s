#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/bin:$PATH"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
DEV_DIR="$(dirname "$INFRA_DIR")"
AWS_REGION="${AWS_REGION:-us-east-1}"
TF_STATE_BUCKET="${TF_STATE_BUCKET:?Set the private S3 state bucket name}"
DB_MASTER_USERNAME="${DB_MASTER_USERNAME:?Set a database master username}"
DB_MASTER_PASSWORD="${DB_MASTER_PASSWORD:?Set a unique database master password}"
CLIENTES_DIR="${CLIENTES_DIR:-$DEV_DIR/soat13-tc-revenda-clientes}"
VEICULOS_DIR="${VEICULOS_DIR:-$DEV_DIR/soat13-tc-revenda-veiculos}"
VENDAS_DIR="${VENDAS_DIR:-$DEV_DIR/soat13-tc-revenda-vendas}"

service_dir() {
  case "$1" in
    clientes) printf '%s' "$CLIENTES_DIR" ;;
    veiculos) printf '%s' "$VEICULOS_DIR" ;;
    vendas) printf '%s' "$VENDAS_DIR" ;;
    *) echo "Unknown service: $1" >&2; return 1 ;;
  esac
}

for tool in aws terraform kubectl docker python3; do
  command -v "$tool" >/dev/null || { echo "Required tool not found: $tool" >&2; exit 1; }
done
for source_dir in "$CLIENTES_DIR" "$VEICULOS_DIR" "$VENDAS_DIR"; do
  [[ -f "$source_dir/Dockerfile" ]] || { echo "Dockerfile not found in $source_dir" >&2; exit 1; }
done

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
CLUSTER_NAME="soat13-tc-revenda"
TAG="${IMAGE_TAG:-$(date -u +%Y%m%d%H%M%S)}"
ECR_HOST="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
TMP_DIR="$(mktemp -d)"
trap 'rm -f "$TMP_DIR/clientes.yaml" "$TMP_DIR/veiculos.yaml" "$TMP_DIR/vendas.yaml" "$TMP_DIR/clientes-db.env" "$TMP_DIR/veiculos-db.env" "$TMP_DIR/vendas-db.env"; rmdir "$TMP_DIR"' EXIT

terraform -chdir="$INFRA_DIR" init \
  -backend-config="bucket=$TF_STATE_BUCKET" \
  -backend-config="key=infra-k8s/terraform.tfstate" \
  -backend-config="region=$AWS_REGION" \
  -backend-config="use_lockfile=true"
terraform -chdir="$INFRA_DIR" apply -auto-approve \
  -var="region=$AWS_REGION" \
  -var="kubectl_cidr_allowlist=[\"${KUBECTL_CIDR_ALLOWLIST:?Set KUBECTL_CIDR_ALLOWLIST to your trusted public IP CIDR}\"]"

aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME"
kubectl apply -f "$INFRA_DIR/k8s/namespace.yaml"

terraform -chdir="$DEV_DIR/soat13-tc-revenda-infra-db" init \
  -backend-config="bucket=$TF_STATE_BUCKET" \
  -backend-config="key=infra-db/terraform.tfstate" \
  -backend-config="region=$AWS_REGION" \
  -backend-config="use_lockfile=true"
export TF_VAR_tf_state_bucket="$TF_STATE_BUCKET"
export TF_VAR_region="$AWS_REGION"
export TF_VAR_master_username="$DB_MASTER_USERNAME"
export TF_VAR_master_password="$DB_MASTER_PASSWORD"
terraform -chdir="$DEV_DIR/soat13-tc-revenda-infra-db" apply -auto-approve

DB_HOSTS_JSON="$(terraform -chdir="$DEV_DIR/soat13-tc-revenda-infra-db" output -json db_hosts)"
DB_USERNAME="$DB_MASTER_USERNAME"
umask 077
for service in clientes veiculos vendas; do
  db_host="$(printf '%s' "$DB_HOSTS_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)[sys.argv[1]])' "$service")"
  secret_file="$TMP_DIR/${service}-db.env"
  printf 'host=%s\nusername=%s\npassword=%s\n' "$db_host" "$DB_USERNAME" "$DB_MASTER_PASSWORD" >"$secret_file"
  kubectl -n revenda create secret generic "${service}-db" \
    --from-env-file="$secret_file" \
    --dry-run=client -o yaml | kubectl apply -f -

  source_dir="$(service_dir "$service")"
  kubectl -n revenda create configmap "${service}-schema" \
    --from-file=schema.sql="$source_dir/database/init.sql" \
    --dry-run=client -o yaml | kubectl apply -f -

  job="db-schema-${service}-${TAG}"
  kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: ${job}
  namespace: revenda
spec:
  backoffLimit: 3
  ttlSecondsAfterFinished: 3600
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: initialize-schema
          image: mysql:8.4
          command:
            - /bin/sh
            - -c
            - mysql --host="\$DB_HOST" --user="\$DB_USER" "\$DB_NAME" < /schema/schema.sql
          env:
            - name: DB_HOST
              valueFrom:
                secretKeyRef:
                  name: ${service}-db
                  key: host
            - name: DB_USER
              valueFrom:
                secretKeyRef:
                  name: ${service}-db
                  key: username
            - name: MYSQL_PWD
              valueFrom:
                secretKeyRef:
                  name: ${service}-db
                  key: password
            - name: DB_NAME
              value: ${service}_db
          volumeMounts:
            - name: schema
              mountPath: /schema
              readOnly: true
      volumes:
        - name: schema
          configMap:
            name: ${service}-schema
EOF
  if ! kubectl -n revenda wait --for=condition=complete "job/$job" --timeout=10m; then
    kubectl -n revenda logs "job/$job"
    exit 1
  fi
done

aws ecr get-login-password --region "$AWS_REGION" |
  docker login --username AWS --password-stdin "$ECR_HOST"

for service in clientes veiculos vendas; do
  source_dir="$(service_dir "$service")"
  image="$ECR_HOST/soat13-tc-revenda-$service:$TAG"
  docker build --tag "$image" "$source_dir"
  docker push "$image"
  sed "s|IMAGE_${service^^}|$image|g" "$INFRA_DIR/k8s/$service.yaml" >"$TMP_DIR/$service.yaml"
done

kubectl apply -f "$TMP_DIR/clientes.yaml" -f "$TMP_DIR/veiculos.yaml" -f "$TMP_DIR/vendas.yaml"
kubectl apply -f "$INFRA_DIR/k8s/ingress.yaml"
kubectl -n revenda rollout status deployment/clientes --timeout=10m
kubectl -n revenda rollout status deployment/veiculos --timeout=10m
kubectl -n revenda rollout status deployment/vendas --timeout=10m

for attempt in $(seq 1 60); do
  ALB_DNS="$(kubectl -n revenda get ingress revenda -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)"
  [[ -n "$ALB_DNS" ]] && break
  sleep 10
done
[[ -n "${ALB_DNS:-}" ]] || { echo "Internal ALB was not provisioned." >&2; exit 1; }

ALB_ARN="$(aws elbv2 describe-load-balancers --region "$AWS_REGION" \
  --query "LoadBalancers[?DNSName=='$ALB_DNS'].LoadBalancerArn | [0]" --output text)"
LISTENER_ARN="$(aws elbv2 describe-listeners --region "$AWS_REGION" --load-balancer-arn "$ALB_ARN" \
  --query 'Listeners[?Port==`80`].ListenerArn | [0]' --output text)"
[[ "$LISTENER_ARN" == arn:* ]] || { echo "Could not resolve internal ALB listener ARN." >&2; exit 1; }

terraform -chdir="$INFRA_DIR" apply -auto-approve \
  -var="region=$AWS_REGION" \
  -var="kubectl_cidr_allowlist=[\"$KUBECTL_CIDR_ALLOWLIST\"]" \
  -var="load_balancer_listener_arn=$LISTENER_ARN"

echo "Deployment completed."
terraform -chdir="$INFRA_DIR" output -raw api_gateway_url
echo
