locals {
  api_service_name      = "${var.app_name}-api"
  frontend_service_name = "${var.app_name}-frontend"
}

resource "google_project_service" "run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secretmanager" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "iam" {
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "iamcredentials" {
  service            = "iamcredentials.googleapis.com"
  disable_on_destroy = false
}

# --- secrets ---

resource "google_secret_manager_secret" "database_url" {
  secret_id = "${var.app_name}-database-url"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = var.database_url
}

resource "google_secret_manager_secret" "sec_edgar_user_agent" {
  secret_id = "${var.app_name}-sec-edgar-user-agent"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "sec_edgar_user_agent" {
  secret      = google_secret_manager_secret.sec_edgar_user_agent.id
  secret_data = var.sec_edgar_user_agent
}

resource "google_secret_manager_secret" "clerk_secret_key" {
  secret_id = "${var.app_name}-clerk-secret-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "clerk_secret_key" {
  secret      = google_secret_manager_secret.clerk_secret_key.id
  secret_data = var.clerk_secret_key
}

# --- runtime service account for the Cloud Run services ---

resource "google_service_account" "run_sa" {
  account_id   = "${var.app_name}-run"
  display_name = "${var.app_name} Cloud Run runtime"
}

resource "google_secret_manager_secret_iam_member" "run_sa_database_url" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "run_sa_sec_edgar_user_agent" {
  secret_id = google_secret_manager_secret.sec_edgar_user_agent.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "run_sa_clerk_secret_key" {
  secret_id = google_secret_manager_secret.clerk_secret_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_sa.email}"
}

# --- api service ---

resource "google_cloud_run_v2_service" "api" {
  name                = local.api_service_name
  location            = var.gcp_region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.run_sa.email

    # Hard cap on scale-out = hard cap on worst-case bill.
    scaling {
      max_instance_count = 2
    }

    containers {
      image = var.api_image

      ports {
        container_port = 8000
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }

      env {
        name = "SEC_EDGAR_USER_AGENT"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.sec_edgar_user_agent.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "CLERK_ISSUER"
        value = var.clerk_issuer
      }

      env {
        name  = "CLERK_AUTHORIZED_PARTIES"
        value = var.clerk_authorized_parties
      }

      env {
        name  = "DAILY_EXTRACTION_QUOTA"
        value = var.daily_extraction_quota
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].containers[0].image]
  }

  depends_on = [google_project_service.run]
}

resource "google_cloud_run_v2_service_iam_member" "api_public" {
  name     = google_cloud_run_v2_service.api.name
  location = google_cloud_run_v2_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# --- frontend service ---

resource "google_cloud_run_v2_service" "frontend" {
  name                = local.frontend_service_name
  location            = var.gcp_region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.run_sa.email

    # Hard cap on scale-out = hard cap on worst-case bill.
    scaling {
      max_instance_count = 2
    }

    containers {
      image = var.frontend_image

      ports {
        container_port = 3000
      }

      env {
        name  = "API_PROXY_TARGET"
        value = google_cloud_run_v2_service.api.uri
      }

      env {
        name = "CLERK_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.clerk_secret_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
        value = var.clerk_publishable_key
      }

      env {
        name  = "NEXT_PUBLIC_CLERK_SIGN_IN_URL"
        value = "/sign-in"
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].containers[0].image]
  }

  depends_on = [google_project_service.run]
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  name     = google_cloud_run_v2_service.frontend.name
  location = google_cloud_run_v2_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
