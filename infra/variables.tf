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

variable "edinet_api_key" {
  description = "API key for EDINET (Japan) filing endpoints"
  type        = string
  sensitive   = true
}

variable "database_url" {
  description = "Neon Postgres connection string (postgresql+psycopg://...)"
  type        = string
  sensitive   = true
}

variable "clerk_secret_key" {
  description = "Clerk secret key (sk_...) used by the Next.js middleware"
  type        = string
  sensitive   = true
}

variable "clerk_publishable_key" {
  description = "Clerk publishable key (pk_..., public by nature); must match the value baked into the frontend image at build time"
  type        = string
}

variable "clerk_issuer" {
  description = "Clerk issuer URL the api verifies JWTs against, e.g. https://your-slug.clerk.accounts.dev"
  type        = string
}

variable "clerk_authorized_parties" {
  description = "Comma-separated origins allowed as azp claim; fill with the frontend URL after first apply (referencing it directly would create an api<->frontend cycle)"
  type        = string
  default     = ""
}

variable "daily_extraction_quota" {
  description = "Extraction rows a user may create per UTC day"
  type        = string
  default     = "20"
}
