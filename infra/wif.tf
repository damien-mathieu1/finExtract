# Keyless auth for GitHub Actions: no long-lived SA JSON keys.

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "${var.app_name}-github"
  display_name              = "GitHub Actions"

  depends_on = [google_project_service.iam, google_project_service.iamcredentials]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "GitHub"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "assertion.repository == \"${var.github_repo}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "deployer" {
  account_id   = "${var.app_name}-deployer"
  display_name = "${var.app_name} CI deployer"
}

resource "google_service_account_iam_member" "deployer_wif_binding" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

resource "google_project_iam_member" "deployer_run_admin" {
  project = var.gcp_project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

# lets the deployer set the Cloud Run runtime service account on deploy
resource "google_service_account_iam_member" "deployer_actas_run_sa" {
  service_account_id = google_service_account.run_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deployer.email}"
}
