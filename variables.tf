variable "region" {
  description = "AWS region for the stack."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix used for AWS resources."
  type        = string
  default     = "soat13-tc-revenda"
}

variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
  default     = "soat13-tc-revenda"
}

variable "kubernetes_version" {
  description = "Kubernetes version for EKS."
  type        = string
  default     = "1.32"
}

variable "kubectl_cidr_allowlist" {
  description = "Public CIDR ranges allowed to reach the EKS API endpoint."
  type        = list(string)
}

variable "node_instance_type" {
  description = "Worker node EC2 instance type."
  type        = string
  default     = "t3.medium"
}

variable "desired_nodes" {
  description = "Desired EKS worker node count."
  type        = number
  default     = 2
}

variable "min_nodes" {
  description = "Minimum EKS worker node count."
  type        = number
  default     = 2
}

variable "max_nodes" {
  description = "Maximum EKS worker node count."
  type        = number
  default     = 4
}

variable "load_balancer_listener_arn" {
  description = "Internal ALB listener ARN, populated after the ingress is provisioned."
  type        = string
  default     = ""
}
