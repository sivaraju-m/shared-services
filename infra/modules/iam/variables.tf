variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "service_accounts" {
  description = "Map of service account names to roles"
  type        = map(list(string))
}

variable "bucket_access" {
  description = "Map of bucket name to IAM bindings"
  type = map(object({
    role   = string
    member = string
  }))
  default = {
    cleaned_data_viewer = {
      role   = "roles/storage.objectViewer"
      member = "user:sivaraj.malladi@gmail.com"
    }
  }
}
