# Shared Services Terraform Infrastructure
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  backend "gcs" {
    bucket = "ai-trading-terraform-state"
    prefix = "shared-services"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "shared_services" {
  location      = var.region
  repository_id = "shared-services"
  description   = "Shared Services Docker repository"
  format        = "DOCKER"

  labels = {
    component   = "shared-services"
    environment = var.environment
    managed-by  = "terraform"
  }
}

# Service Account for Shared Services
resource "google_service_account" "shared_services" {
  account_id   = "shared-services-sa"
  display_name = "Shared Services Service Account"
  description  = "Service account for Shared Services"
}

# IAM bindings for service account
resource "google_project_iam_member" "shared_services_bigquery_user" {
  project = var.project_id
  role    = "roles/bigquery.user"
  member  = "serviceAccount:${google_service_account.shared_services.email}"
}

resource "google_project_iam_member" "shared_services_storage_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.shared_services.email}"
}

resource "google_project_iam_member" "shared_services_pubsub_editor" {
  project = var.project_id
  role    = "roles/pubsub.editor"
  member  = "serviceAccount:${google_service_account.shared_services.email}"
}

resource "google_project_iam_member" "shared_services_monitoring_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.shared_services.email}"
}

resource "google_project_iam_member" "shared_services_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.shared_services.email}"
}

# Cloud Run service
resource "google_cloud_run_v2_service" "shared_services" {
  name     = "shared-services"
  location = var.region
  
  deletion_protection = false

  template {
    service_account = google_service_account.shared_services.email
    
    timeout = "300s"
    
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/shared-services/shared-services:latest"
      
      ports {
        container_port = 8080
      }
      
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      
      env {
        name  = "REGION"
        value = var.region
      }

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
      }
      
      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 30
        timeout_seconds       = 10
        period_seconds        = 10
        failure_threshold     = 3
      }
      
      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 60
        timeout_seconds       = 10
        period_seconds        = 30
        failure_threshold     = 3
      }
    }
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
    
    labels = {
      component   = "shared-services"
      environment = var.environment
      managed-by  = "terraform"
    }
  }
  
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [google_artifact_registry_repository.shared_services]
}

# IAM policy for Cloud Run service
resource "google_cloud_run_service_iam_member" "shared_services_invoker" {
  service  = google_cloud_run_v2_service.shared_services.name
  location = google_cloud_run_v2_service.shared_services.location
  role     = "roles/run.invoker"
  member   = "allAuthenticatedUsers"
}

# Pub/Sub topics for inter-service communication
resource "google_pubsub_topic" "trading_events" {
  name = "trading-events"
  
  labels = {
    component   = "shared-services"
    environment = var.environment
    managed-by  = "terraform"
  }
}

resource "google_pubsub_topic" "system_alerts" {
  name = "system-alerts"
  
  labels = {
    component   = "shared-services"
    environment = var.environment
    managed-by  = "terraform"
  }
}

resource "google_pubsub_topic" "data_updates" {
  name = "data-updates"
  
  labels = {
    component   = "shared-services"
    environment = var.environment
    managed-by  = "terraform"
  }
}

# Pub/Sub subscriptions
resource "google_pubsub_subscription" "trading_events_sub" {
  name  = "trading-events-sub"
  topic = google_pubsub_topic.trading_events.name

  message_retention_duration = "604800s"  # 7 days
  ack_deadline_seconds       = 20

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

resource "google_pubsub_subscription" "system_alerts_sub" {
  name  = "system-alerts-sub"
  topic = google_pubsub_topic.system_alerts.name

  message_retention_duration = "604800s"  # 7 days
  ack_deadline_seconds       = 20
}

resource "google_pubsub_subscription" "data_updates_sub" {
  name  = "data-updates-sub"
  topic = google_pubsub_topic.data_updates.name

  message_retention_duration = "604800s"  # 7 days
  ack_deadline_seconds       = 20
}

# Cloud Storage buckets for shared data
resource "google_storage_bucket" "shared_data" {
  name     = "${var.project_id}-shared-data"
  location = var.region

  labels = {
    component   = "shared-services"
    environment = var.environment
    managed-by  = "terraform"
  }

  lifecycle_rule {
    condition {
      age = var.data_retention_days
    }
    action {
      type = "Delete"
    }
  }

  versioning {
    enabled = true
  }
}

resource "google_storage_bucket" "config_data" {
  name     = "${var.project_id}-config-data"
  location = var.region

  labels = {
    component   = "shared-services"
    environment = var.environment
    managed-by  = "terraform"
  }

  versioning {
    enabled = true
  }
}

# BigQuery dataset for shared metrics
resource "google_bigquery_dataset" "shared_metrics" {
  dataset_id    = "shared_metrics"
  friendly_name = "Shared Metrics"
  description   = "Dataset for storing cross-service metrics and analytics"
  location      = var.bigquery_location

  labels = {
    component   = "shared-services"
    environment = var.environment
    managed-by  = "terraform"
  }

  delete_contents_on_destroy = false

  access {
    role          = "OWNER"
    user_by_email = google_service_account.shared_services.email
  }
}

# Redis instance for caching and session management
resource "google_redis_instance" "cache" {
  name           = "shared-cache"
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size_gb
  region         = var.region

  auth_enabled = true
  
  labels = {
    component   = "shared-services"
    environment = var.environment
    managed-by  = "terraform"
  }
}

# Cloud Scheduler job for cache cleanup
resource "google_cloud_scheduler_job" "cache_cleanup" {
  name        = "cache-cleanup-job"
  description = "Clean up expired cache entries"
  schedule    = var.cache_cleanup_schedule
  time_zone   = var.timezone
  region      = var.region

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.shared_services.uri}/cleanup-cache"
    
    oidc_token {
      service_account_email = google_service_account.shared_services.email
    }
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      action = "cleanup_expired_entries"
    }))
  }
}

# Monitoring alert policy for shared services
resource "google_monitoring_alert_policy" "shared_services_health" {
  display_name = "Shared Services Health"
  combiner     = "OR"
  
  conditions {
    display_name = "Shared Services Error Rate"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"shared-services\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 0.05
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_MEAN"
        group_by_fields = ["resource.labels.service_name"]
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  alert_strategy {
    auto_close = "86400s"
  }
}

# Budget alert for shared services costs
resource "google_billing_budget" "shared_services_budget" {
  count = var.enable_budget_alerts ? 1 : 0
  
  billing_account = var.billing_account_id
  display_name    = "Shared Services Budget"

  budget_filter {
    projects = ["projects/${var.project_id}"]
    labels = {
      component = "shared-services"
    }
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.monthly_budget)
    }
  }

  threshold_rules {
    threshold_percent = 0.8
    spend_basis      = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 1.0
    spend_basis      = "CURRENT_SPEND"
  }
}
