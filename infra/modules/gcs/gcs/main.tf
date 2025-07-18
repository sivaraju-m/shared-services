terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

# gcs logic goes here

resource "google_storage_bucket" "buckets" {
  for_each = { for name in var.buckets : name => name }

  name          = each.key
  location      = var.location
  force_destroy = true
  project       = var.project_id
}

resource "google_storage_bucket_iam_member" "bucket_iam" {
  for_each = {
    for bucket, bindings in var.iam_bindings :
    bucket => bindings
  }

  bucket     = google_storage_bucket.buckets[each.key].name
  role       = each.value.role
  member     = each.value.member
  depends_on = [google_storage_bucket.buckets]
}
