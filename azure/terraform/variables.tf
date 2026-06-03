variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
  default     = "devops-case-study-rg"
}

variable "cluster_name" {
  description = "AKS cluster name"
  type        = string
  default     = "devops-aks-cluster"
}

variable "kubernetes_version" {
  description = "Kubernetes version for AKS"
  type        = string
  default     = "1.29"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "dns_prefix" {
  description = "DNS prefix for the AKS cluster"
  type        = string
  default     = "devops-csv"
}

variable "storage_account_name" {
  description = "Azure Storage Account name (globally unique)"
  type        = string
  default     = "devopscsvuploads"
}

variable "container_name" {
  description = "Azure Blob container name"
  type        = string
  default     = "csv-uploads"
}

# Node pool sizing
variable "system_node_count" {
  description = "System node pool count"
  type        = number
  default     = 3
}

variable "ondemand_min_count" {
  description = "On-demand node pool minimum"
  type        = number
  default     = 2
}

variable "ondemand_max_count" {
  description = "On-demand node pool maximum"
  type        = number
  default     = 10
}

variable "spot_min_count" {
  description = "Spot node pool minimum"
  type        = number
  default     = 0
}

variable "spot_max_count" {
  description = "Spot node pool maximum"
  type        = number
  default     = 20
}

variable "gpu_max_count" {
  description = "GPU spot node pool maximum"
  type        = number
  default     = 5
}
