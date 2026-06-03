output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.main.name
}

output "aks_resource_group" {
  value = azurerm_resource_group.main.name
}

output "aks_kube_config" {
  value     = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive = true
}

output "aks_cluster_identity" {
  value = azurerm_kubernetes_cluster.main.identity[0].principal_id
}

output "oidc_issuer_url" {
  value = azurerm_kubernetes_cluster.main.oidc_issuer_url
}

output "storage_account_name" {
  value = azurerm_storage_account.main.name
}

output "storage_account_primary_endpoint" {
  value = azurerm_storage_account.main.primary_blob_endpoint
}

output "storage_container_name" {
  value = azurerm_storage_container.csv_uploads.name
}

output "csv_app_managed_identity_client_id" {
  value = azurerm_user_assigned_identity.csv_app.client_id
}

output "csv_app_managed_identity_id" {
  value = azurerm_user_assigned_identity.csv_app.id
}

output "connect_to_cluster" {
  value = "az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${azurerm_kubernetes_cluster.main.name}"
}
