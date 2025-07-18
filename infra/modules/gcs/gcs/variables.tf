variable "project_id" {
  type = string
}

variable "location" {
  type = string
}

variable "buckets" {
  type = list(string)
}

variable "iam_bindings" {
  description = "Map of bucket name to IAM binding (role/member)"
  type = map(object({
    role   = string
    member = string
  }))
  default = {}
}
