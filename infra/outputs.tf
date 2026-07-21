output "api_url" {
  value = google_cloud_run_v2_service.api.uri
}

output "frontend_url" {
  value = google_cloud_run_v2_service.frontend.uri
}

output "deployer_service_account_email" {
  value = google_service_account.deployer.email
}

output "workload_identity_provider" {
  description = "Use as GCP_WORKLOAD_IDENTITY_PROVIDER in GH Actions"
  value       = google_iam_workload_identity_pool_provider.github.name
}
