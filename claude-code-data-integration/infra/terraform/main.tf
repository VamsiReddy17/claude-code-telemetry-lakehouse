terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "prefix" {
  type    = string
  default = "claudetelem"
}

variable "location" {
  type    = string
  default = "eastus2"
}

resource "azurerm_resource_group" "rg" {
  name     = "rg-${var.prefix}"
  location = var.location
}

resource "azurerm_storage_account" "sa" {
  name                     = "stg${var.prefix}dev"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "ZRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true

  blob_properties {
    versioning_enabled  = true
    delete_retention_policy { days = 30 }
  }
}

resource "azurerm_storage_container" "telemetry" {
  name                  = "claude-telemetry"
  storage_account_id    = azurerm_storage_account.sa.id
  container_access_type = "private"
}

output "storage_account" {
  value = azurerm_storage_account.sa.name
}

output "dfs_endpoint" {
  value = azurerm_storage_account.sa.primary_dfs_endpoint
}
