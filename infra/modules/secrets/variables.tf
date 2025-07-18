variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "compute_service_account" {
  description = "Service account email for Compute Engine instances"
  type        = string
}

variable "cloud_run_service_account" {
  description = "Service account email for Cloud Run services"
  type        = string
}

variable "secrets_map" {
  description = "Map of secret names to their values for initial setup"
  type        = map(string)
  default     = {}
  sensitive   = true
}
