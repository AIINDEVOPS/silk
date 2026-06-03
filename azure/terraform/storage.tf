# ── Azure Storage Account (equivalent to AWS S3 bucket) ──────────────────────
resource "azurerm_storage_account" "main" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "GRS"           # Geo-redundant (equiv to S3 cross-region replication)
  account_kind             = "StorageV2"

  # Security settings (equiv to S3 public access block)
  allow_nested_items_to_be_public  = false
  public_network_access_enabled    = true    # Set false for private endpoint only
  https_traffic_only_enabled       = true
  min_tls_version                  = "TLS1_2"

  # Versioning (equiv to S3 versioning)
  blob_properties {
    versioning_enabled = true

    # Soft delete (equiv to S3 versioning + MFA delete protection)
    delete_retention_policy {
      days = 30
    }

    container_delete_retention_policy {
      days = 30
    }

    # CORS (equiv to S3 CORS config)
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["GET", "POST", "PUT"]
      allowed_origins    = ["*"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 3000
    }
  }

  tags = local.common_tags
}

# ── Blob Container (equiv to S3 bucket prefix structure) ─────────────────────
resource "azurerm_storage_container" "csv_uploads" {
  name                  = var.container_name
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# ── Lifecycle Management Policy (equiv to AWS S3 Glacier lifecycle) ───────────
#
# Azure Blob Storage Tiers (AWS S3 equivalents):
# ─────────────────────────────────────────────
#  Azure Hot          ≈ AWS S3 Standard
#  Azure Cool         ≈ AWS S3 Standard-IA      (30-day min, cheaper storage)
#  Azure Cold         ≈ AWS S3 Glacier IR       (90-day min, ms retrieval)
#  Azure Archive      ≈ AWS S3 Glacier / Deep Archive (180-day min, hours retrieval)
#
# Azure lifecycle timeline:
#  Day 0   → Hot (uploaded)
#  Day 30  → Cool   (40% cheaper storage)
#  Day 90  → Cold   (further 50% cheaper)
#  Day 180 → Archive (lowest cost, 1-15hr rehydration)
#  Day 730 → Delete (2 years retention)
#
resource "azurerm_storage_management_policy" "csv_lifecycle" {
  storage_account_id = azurerm_storage_account.main.id

  rule {
    name    = "processed-csv-lifecycle"
    enabled = true

    filters {
      prefix_match = ["csv-uploads/processed/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        # Move to Cool after 30 days (equiv S3 STANDARD_IA transition)
        tier_to_cool_after_days_since_modification_greater_than = 30

        # Move to Cold after 90 days (equiv S3 GLACIER_IR)
        tier_to_cold_after_days_since_modification_greater_than = 90

        # Move to Archive after 180 days (equiv S3 GLACIER / DEEP_ARCHIVE)
        tier_to_archive_after_days_since_modification_greater_than = 180

        # Delete after 730 days (2 years retention)
        delete_after_days_since_modification_greater_than = 730
      }

      # Lifecycle for old snapshot versions
      snapshot {
        tier_to_cool_after_days_since_creation_greater_than    = 30
        tier_to_archive_after_days_since_creation_greater_than = 90
        delete_after_days_since_creation_greater_than          = 365
      }

      # Version lifecycle
      version {
        tier_to_cool_after_days_since_creation             = 30
        tier_to_archive_after_days_since_creation          = 90
        delete_after_days_since_creation                   = 365
      }
    }
  }

  rule {
    name    = "uploads-temp-cleanup"
    enabled = true

    filters {
      prefix_match = ["csv-uploads/uploads/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        # Delete raw uploads after 7 days (already moved to processed/)
        delete_after_days_since_modification_greater_than = 7
      }
    }
  }

  rule {
    name    = "incomplete-upload-cleanup"
    enabled = true

    filters {
      prefix_match = ["csv-uploads/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      # Clean up failed/incomplete block uploads after 7 days
      base_blob {
        delete_after_days_since_last_access_time_greater_than = 7
      }
    }
  }
}

# ── Private Endpoint for Storage (production security) ───────────────────────
resource "azurerm_private_endpoint" "storage" {
  name                = "${var.storage_account_name}-private-endpoint"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.user_nodes.id

  private_service_connection {
    name                           = "${var.storage_account_name}-connection"
    private_connection_resource_id = azurerm_storage_account.main.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  tags = local.common_tags
}
