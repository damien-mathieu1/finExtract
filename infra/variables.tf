variable "gcp_project_id" {
  description = "GCP project id to deploy into"
  type        = string
}

variable "gcp_region" {
  description = "GCP region for Cloud Run services"
  type        = string
  default     = "europe-west1"
}

variable "app_name" {
  description = "Base name used to prefix resources"
  type        = string
  default     = "finextract"
}

variable "github_repo" {
  description = "GitHub repo allowed to assume the deploy identity, format: owner/repo"
  type        = string
}

variable "api_image" {
  description = "Placeholder image for the api Cloud Run service; CI overwrites the revision on deploy"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "frontend_image" {
  description = "Placeholder image for the frontend Cloud Run service; CI overwrites the revision on deploy"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "sec_edgar_user_agent" {
  description = "User-Agent required by SEC EDGAR endpoints, format: 'AppName you@example.com'"
  type        = string
}

variable "database_url" {
  description = "Neon Postgres connection string (postgresql+psycopg://...)"
  type        = string
  sensitive   = true
}
