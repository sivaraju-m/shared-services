# Shared Services Terraform Outputs

output "service_account_email" {
  description = "Email of the Shared Services service account"
  value       = google_service_account.shared_services.email
}

output "cloud_run_service_url" {
  description = "URL of the Shared Services Cloud Run service"
  value       = google_cloud_run_v2_service.shared_services.uri
}

output "cloud_run_service_name" {
  description = "Name of the Shared Services Cloud Run service"
  value       = google_cloud_run_v2_service.shared_services.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository for Docker images"
  value       = google_artifact_registry_repository.shared_services.name
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.shared_services.repository_id}"
}

output "pubsub_topics" {
  description = "Pub/Sub topic names"
  value = {
    trading_events = google_pubsub_topic.trading_events.name
    system_alerts  = google_pubsub_topic.system_alerts.name
    data_updates   = google_pubsub_topic.data_updates.name
  }
}

output "pubsub_subscriptions" {
  description = "Pub/Sub subscription names"
  value = {
    trading_events = google_pubsub_subscription.trading_events_sub.name
    system_alerts  = google_pubsub_subscription.system_alerts_sub.name
    data_updates   = google_pubsub_subscription.data_updates_sub.name
  }
}

output "storage_buckets" {
  description = "Cloud Storage bucket names"
  value = {
    shared_data = google_storage_bucket.shared_data.name
    config_data = google_storage_bucket.config_data.name
  }
}

output "bigquery_dataset_id" {
  description = "BigQuery dataset ID for shared metrics"
  value       = google_bigquery_dataset.shared_metrics.dataset_id
}

output "bigquery_dataset_location" {
  description = "BigQuery dataset location"
  value       = google_bigquery_dataset.shared_metrics.location
}

output "redis_instance" {
  description = "Redis instance information"
  value = {
    name = google_redis_instance.cache.name
    host = google_redis_instance.cache.host
    port = google_redis_instance.cache.port
  }
  sensitive = true
}

output "scheduler_job_names" {
  description = "Names of Cloud Scheduler jobs"
  value = [
    google_cloud_scheduler_job.cache_cleanup.name
  ]
}

output "monitoring_alert_policy_name" {
  description = "Name of the monitoring alert policy"
  value       = google_monitoring_alert_policy.shared_services_health.name
}

output "budget_name" {
  description = "Name of the budget alert (if enabled)"
  value       = var.enable_budget_alerts ? google_billing_budget.shared_services_budget[0].display_name : null
}

# Configuration outputs for other services
output "shared_services_config" {
  description = "Shared Services configuration for other services"
  value = {
    service_url           = google_cloud_run_v2_service.shared_services.uri
    service_account_email = google_service_account.shared_services.email
    dataset_id           = google_bigquery_dataset.shared_metrics.dataset_id
    pubsub_topics        = {
      trading_events = google_pubsub_topic.trading_events.name
      system_alerts  = google_pubsub_topic.system_alerts.name
      data_updates   = google_pubsub_topic.data_updates.name
    }
    storage_buckets = {
      shared_data = google_storage_bucket.shared_data.name
      config_data = google_storage_bucket.config_data.name
    }
    redis_host = google_redis_instance.cache.host
    redis_port = google_redis_instance.cache.port
  }
  sensitive = false
}

# Deployment information
output "deployment_info" {
  description = "Deployment information and next steps"
  value = {
    docker_image_url = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.shared_services.repository_id}/shared-services:latest"
    health_check_url = "${google_cloud_run_v2_service.shared_services.uri}/health"
    auth_endpoint = "${google_cloud_run_v2_service.shared_services.uri}/auth"
    cache_endpoint = "${google_cloud_run_v2_service.shared_services.uri}/cache"
    config_endpoint = "${google_cloud_run_v2_service.shared_services.uri}/config"
    messaging_endpoint = "${google_cloud_run_v2_service.shared_services.uri}/messaging"
  }
}
