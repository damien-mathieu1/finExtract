# Infra (OpenTofu, GCP Cloud Run)

Provisions: 2 Cloud Run services (api, frontend), Secret Manager secrets
(`DATABASE_URL`, `SEC_EDGAR_USER_AGENT`), a runtime service account, and
Workload Identity Federation so GitHub Actions can deploy without a static
key.

DB is Neon (managed Postgres, outside this config) — just paste its
connection string into `database_url`.

## First-time setup

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars   # fill in real values
tofu init
tofu apply
```

Then set these as GitHub repo secrets (from `tofu output`):

- `GCP_PROJECT_ID`
- `GCP_WORKLOAD_IDENTITY_PROVIDER` -> `workload_identity_provider` output
- `GCP_DEPLOYER_SA_EMAIL` -> `deployer_service_account_email` output

One-time: after the first `deploy.yml` run builds the images, mark both
GHCR packages (`<repo>-api`, `<repo>-frontend`) public (Cloud Run pulls
ghcr.io images unauthenticated). Package settings -> Change visibility.

## Deploying

`.github/workflows/deploy.yml` runs on GitHub Release publish (or manual
dispatch): builds+pushes both images to ghcr.io, then `gcloud run deploy`
each service with the new image tag. OpenTofu owns the service shell/secrets/
IAM; it isn't re-applied on every deploy (`lifecycle.ignore_changes` on the
image so `tofu apply` won't fight the CI-deployed revision).

## State

No backend configured — state is local by default. Before using this for
real, move it to a GCS bucket (`terraform { backend "gcs" {...} }`) so it
isn't only on one laptop.
