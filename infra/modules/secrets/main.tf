# GCP Secret Manager for AI Trading Machine
# Securely stores trading API credentials and sensitive configuration

resource "google_secret_manager_secret" "kite_api_key" {
  secret_id = "kite-api-key"

  labels = {
    app         = "ai-trading-machine"
    environment = var.environment
    type        = "api-credential"
  }

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "kite_api_secret" {
  secret_id = "kite-api-secret"

  labels = {
    app         = "ai-trading-machine"
    environment = var.environment
    type        = "api-credential"
  }

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "kite_access_token" {
  secret_id = "kite-access-token"

  labels = {
    app         = "ai-trading-machine"
    environment = var.environment
    type        = "api-credential"
    temporary   = "true" # This token expires and needs refresh
  }

  replication {
    auto {}
  }
}

# Trading configuration secrets
resource "google_secret_manager_secret" "trading_config" {
  secret_id = "trading-config"

  labels = {
    app         = "ai-trading-machine"
    environment = var.environment
    type        = "configuration"
  }

  replication {
    auto {}
  }
}

# Database credentials (if needed for future expansion)
resource "google_secret_manager_secret" "db_connection_string" {
  secret_id = "db-connection-string"

  labels = {
    app         = "ai-trading-machine"
    environment = var.environment
    type        = "database"
  }

  replication {
    auto {}
  }
}

# IAM binding for Compute Engine to access secrets
resource "google_secret_manager_secret_iam_binding" "secret_accessor" {
  for_each = {
    kite_api_key      = google_secret_manager_secret.kite_api_key.secret_id
    kite_api_secret   = google_secret_manager_secret.kite_api_secret.secret_id
    kite_access_token = google_secret_manager_secret.kite_access_token.secret_id
    trading_config    = google_secret_manager_secret.trading_config.secret_id
    db_connection     = google_secret_manager_secret.db_connection_string.secret_id
  }

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"

  members = [
    "serviceAccount:${var.compute_service_account}",
    "serviceAccount:${var.cloud_run_service_account}",
  ]
}

# Output the secret names for use in applications
output "secret_names" {
  value = {
    kite_api_key      = google_secret_manager_secret.kite_api_key.secret_id
    kite_api_secret   = google_secret_manager_secret.kite_api_secret.secret_id
    kite_access_token = google_secret_manager_secret.kite_access_token.secret_id
    trading_config    = google_secret_manager_secret.trading_config.secret_id
    db_connection     = google_secret_manager_secret.db_connection_string.secret_id
  }
  description = "Secret Manager secret names for the AI Trading Machine"
}
