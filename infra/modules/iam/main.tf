resource "google_service_account" "service_accounts" {
  for_each     = var.service_accounts
  project      = var.project_id
  account_id   = each.key
  display_name = "${each.key} service account"
  disabled     = false  # Ensure all service accounts are enabled
}

resource "google_project_iam_member" "bindings" {
  for_each = {
    for pair in flatten([
      for sa, roles in var.service_accounts : [
        for role in roles : {
          sa   = sa
          role = role
        }
      ]
    ]) : "${pair.sa}-${pair.role}" => pair
  }

  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.service_accounts[each.value.sa].email}"
}

resource "google_storage_bucket_iam_binding" "bucket_access" {
  bucket = "${var.project_id}-cleaned-data"
  role   = "roles/storage.objectViewer"
  members = [
    "user:sivaraj.malladi@gmail.com",
    "serviceAccount:${google_service_account.service_accounts["fetch-orchestrator"].email}"
  ]
}

# Add bucket admin role to service account
resource "google_storage_bucket_iam_binding" "bucket_admin" {
  bucket = "${var.project_id}-cleaned-data"
  role   = "roles/storage.admin"
  members = [
    "serviceAccount:${google_service_account.service_accounts["fetch-orchestrator"].email}"
  ]
}
