# Shared Services Terraform Variables

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "bigquery_location" {
  description = "BigQuery dataset location"
  type        = string
  default     = "US"
}

variable "timezone" {
  description = "Timezone for scheduled jobs"
  type        = string
  default     = "America/New_York"
}

# Cloud Run Configuration
variable "cloud_run_cpu" {
  description = "CPU allocation for Cloud Run"
  type        = string
  default     = "1"
}

variable "cloud_run_memory" {
  description = "Memory allocation for Cloud Run"
  type        = string
  default     = "2Gi"
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

# Redis Configuration
variable "redis_tier" {
  description = "Redis tier (BASIC or STANDARD_HA)"
  type        = string
  default     = "STANDARD_HA"
}

variable "redis_memory_size_gb" {
  description = "Redis memory size in GB"
  type        = number
  default     = 4
}

# Scheduling Configuration
variable "cache_cleanup_schedule" {
  description = "Cron schedule for cache cleanup"
  type        = string
  default     = "0 2 * * *"  # 2 AM daily
}

# Monitoring Configuration
variable "notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}

# Budget Configuration
variable "enable_budget_alerts" {
  description = "Enable budget alerts"
  type        = bool
  default     = true
}

variable "billing_account_id" {
  description = "Billing account ID for budget alerts"
  type        = string
  default     = ""
}

variable "monthly_budget" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 400
}

# Security Configuration
variable "allowed_ingress" {
  description = "Allowed ingress configuration for Cloud Run"
  type        = string
  default     = "INGRESS_TRAFFIC_ALL"
}

variable "vpc_connector" {
  description = "VPC connector for private networking"
  type        = string
  default     = ""
}

# Performance Configuration
variable "concurrency" {
  description = "Maximum concurrent requests per instance"
  type        = number
  default     = 1000
}

variable "execution_environment" {
  description = "Execution environment (EXECUTION_ENVIRONMENT_GEN1 or EXECUTION_ENVIRONMENT_GEN2)"
  type        = string
  default     = "EXECUTION_ENVIRONMENT_GEN2"
}

# Data Configuration
variable "data_retention_days" {
  description = "Data retention period in days for shared buckets"
  type        = number
  default     = 365
}

variable "cache_ttl_seconds" {
  description = "Default cache TTL in seconds"
  type        = number
  default     = 3600  # 1 hour
}

# Pub/Sub Configuration
variable "pubsub_message_retention_duration" {
  description = "Pub/Sub message retention duration"
  type        = string
  default     = "604800s"  # 7 days
}

variable "pubsub_ack_deadline_seconds" {
  description = "Pub/Sub acknowledgment deadline in seconds"
  type        = number
  default     = 20
}

# Service Configuration
variable "enabled_services" {
  description = "List of enabled shared services"
  type        = list(string)
  default     = [
    "authentication",
    "authorization",
    "rate_limiting",
    "caching",
    "messaging",
    "configuration",
    "logging",
    "monitoring"
  ]
}

# Authentication Configuration
variable "jwt_secret_length" {
  description = "JWT secret key length"
  type        = number
  default     = 64
}

variable "jwt_expiration_hours" {
  description = "JWT token expiration in hours"
  type        = number
  default     = 24
}

variable "session_timeout_minutes" {
  description = "Session timeout in minutes"
  type        = number
  default     = 60
}

# Rate Limiting Configuration
variable "rate_limits" {
  description = "Rate limiting configuration"
  type = object({
    requests_per_minute = number
    burst_size         = number
    api_key_limits     = number
    ip_whitelist       = list(string)
  })
  default = {
    requests_per_minute = 1000
    burst_size         = 100
    api_key_limits     = 10000
    ip_whitelist       = []
  }
}

# Logging Configuration
variable "log_retention_days" {
  description = "Log retention period in days"
  type        = number
  default     = 90
}

variable "log_levels" {
  description = "Enabled log levels"
  type        = list(string)
  default     = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
}

# Configuration Management
variable "config_sources" {
  description = "Configuration sources"
  type        = list(string)
  default     = ["cloud_storage", "secret_manager", "firestore"]
}

variable "config_refresh_interval_seconds" {
  description = "Configuration refresh interval in seconds"
  type        = number
  default     = 300  # 5 minutes
}

# Health Check Configuration
variable "health_check_endpoints" {
  description = "Health check endpoint configurations"
  type = object({
    startup_timeout_seconds  = number
    liveness_timeout_seconds = number
    readiness_timeout_seconds = number
  })
  default = {
    startup_timeout_seconds  = 30
    liveness_timeout_seconds = 10
    readiness_timeout_seconds = 5
  }
}
