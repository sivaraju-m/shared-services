# Cloud Storage Cost-Optimized Module
#
# SJ-VERIFY
# - Path: /ai-trading-machine/infra/modules/gcs_cost_optimized
# - Type: terraform
# - Checks: types,docs,sebi,gcp

terraform {
  required_version = ">= 1.3"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

# Primary bucket for active trading data
resource "google_storage_bucket" "trading_data" {
  name     = var.bucket_name
  location = var.region

  # Cost optimization: Use Standard class for active data
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  # Cost optimization: Disable versioning for non-critical data
  versioning {
    enabled = var.enable_versioning
  }

  # Lifecycle rules for automatic cost optimization
  lifecycle_rule {
    condition {
      age = var.nearline_transition_days
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = var.coldline_transition_days
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = var.archive_transition_days
    }
    action {
      type          = "SetStorageClass"
      storage_class = "ARCHIVE"
    }
  }

  # SEBI compliance: Retain data for required period then auto-delete
  lifecycle_rule {
    condition {
      age = var.deletion_age_days
    }
    action {
      type = "Delete"
    }
  }

  # Cost optimization: Delete incomplete multipart uploads
  lifecycle_rule {
    condition {
      age = 7 # Delete incomplete uploads after 7 days
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }

  # Cost optimization: Delete old versions
  dynamic "lifecycle_rule" {
    for_each = var.enable_versioning ? [1] : []
    content {
      condition {
        age        = var.version_retention_days
        with_state = "ARCHIVED"
      }
      action {
        type = "Delete"
      }
    }
  }

  # CORS configuration for web access
  cors {
    origin          = var.cors_origins
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  labels = {
    environment    = var.environment
    purpose        = "trading-data"
    managed_by     = "terraform"
    cost_optimized = "true"
  }
}

# Separate bucket for critical/compliance data with versioning
resource "google_storage_bucket" "critical_data" {
  count = var.enable_critical_bucket ? 1 : 0

  name     = "${var.bucket_name}-critical"
  location = var.region

  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  # Enable versioning for critical data
  versioning {
    enabled = true
  }

  # More conservative lifecycle for critical data
  lifecycle_rule {
    condition {
      age = var.critical_nearline_days
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = var.critical_coldline_days
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  # SEBI compliance: Keep critical data longer
  lifecycle_rule {
    condition {
      age = var.critical_deletion_days
    }
    action {
      type = "Delete"
    }
  }

  # Version management for critical data
  lifecycle_rule {
    condition {
      age        = var.critical_version_retention_days
      with_state = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    purpose     = "critical-data"
    managed_by  = "terraform"
    compliance  = "sebi"
  }
}

# Bucket for temporary/staging data (most aggressive cost optimization)
resource "google_storage_bucket" "temp_data" {
  count = var.enable_temp_bucket ? 1 : 0

  name     = "${var.bucket_name}-temp"
  location = var.region

  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  # No versioning for temp data
  versioning {
    enabled = false
  }

  # Aggressive deletion for temp data
  lifecycle_rule {
    condition {
      age = var.temp_retention_days
    }
    action {
      type = "Delete"
    }
  }

  # Clean up incomplete uploads quickly
  lifecycle_rule {
    condition {
      age = 1 # Delete incomplete uploads after 1 day
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }

  labels = {
    environment = var.environment
    purpose     = "temporary"
    managed_by  = "terraform"
    auto_delete = "true"
  }
}

# Notification for cost monitoring
resource "google_storage_notification" "cost_monitoring" {
  count = var.enable_cost_monitoring ? 1 : 0

  bucket         = google_storage_bucket.trading_data.name
  payload_format = "JSON_API_V1"
  topic          = var.notification_topic

  event_types = [
    "OBJECT_FINALIZE",
    "OBJECT_DELETE"
  ]

  depends_on = [google_storage_bucket.trading_data]
}
