# ── Resource Group ──────────────────────────────────────────────────────────
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.common_tags
}

# ── Virtual Network & Subnets ────────────────────────────────────────────────
resource "azurerm_virtual_network" "main" {
  name                = "${var.cluster_name}-vnet"
  address_space       = ["10.0.0.0/8"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.common_tags
}

resource "azurerm_subnet" "system_nodes" {
  name                 = "system-nodes-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.240.0.0/16"]
}

resource "azurerm_subnet" "user_nodes" {
  name                 = "user-nodes-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.241.0.0/16"]
}

resource "azurerm_subnet" "spot_nodes" {
  name                 = "spot-nodes-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.242.0.0/16"]
}

# ── Log Analytics Workspace (for AKS monitoring) ─────────────────────────────
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.cluster_name}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.common_tags
}

# ── AKS Cluster ─────────────────────────────────────────────────────────────
resource "azurerm_kubernetes_cluster" "main" {
  name                = var.cluster_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = var.dns_prefix
  kubernetes_version  = var.kubernetes_version

  # ── System Node Pool (equivalent to kops masters + baseline nodes)
  # Must be on-demand for system reliability
  default_node_pool {
    name                 = "system"
    node_count           = var.system_node_count
    vm_size              = "Standard_D2s_v3"
    vnet_subnet_id       = azurerm_subnet.system_nodes.id
    os_disk_size_gb      = 128
    type                 = "VirtualMachineScaleSets"
    enable_auto_scaling  = true
    min_count            = 3
    max_count            = 5
    only_critical_addons_enabled = true   # System pods only
    node_labels = {
      "node-type" = "system"
      "nodepool"  = "system"
    }
    tags = local.common_tags
  }

  # ── Identity (Managed Identity - Azure equivalent of kops IAM role)
  identity {
    type = "SystemAssigned"
  }

  # ── Network profile (Azure CNI - equivalent to Calico on kops)
  network_profile {
    network_plugin     = "azure"
    network_policy     = "calico"
    load_balancer_sku  = "standard"
    outbound_type      = "loadBalancer"
    pod_cidr           = null  # Azure CNI assigns pod IPs from subnet
    service_cidr       = "10.0.0.0/16"
    dns_service_ip     = "10.0.0.10"
  }

  # ── Built-in Cluster Autoscaler (enabled per node pool below)
  # AKS manages CA natively - no separate deployment needed

  # ── Azure Monitor / OMS integration
  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  }

  # ── Azure AD RBAC integration
  azure_active_directory_role_based_access_control {
    managed            = true
    azure_rbac_enabled = true
  }

  # ── Workload Identity (Azure equivalent of AWS IRSA)
  workload_identity_enabled = true
  oidc_issuer_enabled       = true

  # ── Auto upgrade channel
  automatic_channel_upgrade = "patch"

  # ── Maintenance window
  maintenance_window {
    allowed {
      day   = "Sunday"
      hours = [1, 2, 3]
    }
  }

  tags = local.common_tags
}

# ── On-Demand User Node Pool ─────────────────────────────────────────────────
# Azure equivalent of kops nodes-ondemand IG with mixed instance policy
resource "azurerm_kubernetes_cluster_node_pool" "ondemand" {
  name                  = "ondemand"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = "Standard_D4s_v3"
  vnet_subnet_id        = azurerm_subnet.user_nodes.id
  os_disk_size_gb       = 128
  mode                  = "User"

  # Cluster Autoscaler - equivalent to kops minSize/maxSize
  enable_auto_scaling = true
  min_count           = var.ondemand_min_count
  max_count           = var.ondemand_max_count
  node_count          = var.ondemand_min_count

  node_labels = {
    "node-type"              = "ondemand"
    "workload-type"          = "general"
  }

  node_taints = []   # No taints - accepts all workloads

  tags = local.common_tags
}

# ── Spot User Node Pool ───────────────────────────────────────────────────────
# Azure equivalent of kops nodes-spot IG
# Azure Spot VMs = AWS Spot Instances (eviction-based pricing)
resource "azurerm_kubernetes_cluster_node_pool" "spot" {
  name                  = "spot"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = "Standard_D4s_v3"
  vnet_subnet_id        = azurerm_subnet.spot_nodes.id
  os_disk_size_gb       = 128
  mode                  = "User"

  # Spot configuration - equivalent to AWS spot lifecycle
  priority        = "Spot"
  eviction_policy = "Delete"
  spot_max_price  = -1   # -1 = pay up to on-demand price (same as AWS no-bid-cap)

  enable_auto_scaling = true
  min_count           = var.spot_min_count
  max_count           = var.spot_max_count
  node_count          = 0

  node_labels = {
    "node-type"                         = "spot"
    "kubernetes.azure.com/scalesetpriority" = "spot"
  }

  # Spot taint - equivalent to kops spot PreferNoSchedule taint
  node_taints = [
    "kubernetes.azure.com/scalesetpriority=spot:PreferNoSchedule"
  ]

  tags = local.common_tags
}

# ── GPU Spot Node Pool ────────────────────────────────────────────────────────
# Azure equivalent of kops nodes-gpu-spot IG
resource "azurerm_kubernetes_cluster_node_pool" "gpu_spot" {
  name                  = "gpuspot"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = "Standard_NC6s_v3"    # NVIDIA V100 - equiv to AWS p3.2xlarge
  vnet_subnet_id        = azurerm_subnet.spot_nodes.id
  os_disk_size_gb       = 128
  mode                  = "User"

  priority        = "Spot"
  eviction_policy = "Delete"
  spot_max_price  = -1

  enable_auto_scaling = true
  min_count           = 0
  max_count           = var.gpu_max_count
  node_count          = 0

  node_labels = {
    "node-type"                             = "gpu-spot"
    "accelerator"                           = "nvidia-gpu"
    "kubernetes.azure.com/scalesetpriority" = "spot"
  }

  node_taints = [
    "nvidia.com/gpu=present:NoSchedule",
    "kubernetes.azure.com/scalesetpriority=spot:PreferNoSchedule"
  ]

  tags = local.common_tags
}

# ── Managed Identity for Workload (app pod identity) ────────────────────────
resource "azurerm_user_assigned_identity" "csv_app" {
  name                = "${var.cluster_name}-csv-app-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.common_tags
}

# ── Federated Identity Credential (Azure IRSA equivalent) ───────────────────
resource "azurerm_federated_identity_credential" "csv_app" {
  name                = "csv-app-federated-credential"
  resource_group_name = azurerm_resource_group.main.name
  audience            = ["api://AzureADTokenExchange"]
  issuer              = azurerm_kubernetes_cluster.main.oidc_issuer_url
  parent_id           = azurerm_user_assigned_identity.csv_app.id
  subject             = "system:serviceaccount:csv-app:csv-app-sa"
}

# ── RBAC: Assign Storage Blob Contributor to app identity ───────────────────
resource "azurerm_role_assignment" "csv_app_storage" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.csv_app.principal_id
}

locals {
  common_tags = {
    Project     = "devops-case-study"
    ManagedBy   = "terraform"
    Environment = var.environment
    Platform    = "azure"
  }
}
