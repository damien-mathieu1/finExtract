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

Run the **Create Release** workflow by hand from `main`: it runs CI, tags a
CalVer version (`vYYYY.M.N`), writes the changelog, then calls
`.github/workflows/deploy.yml`, which builds+pushes both images to ghcr.io
(tagged with the version and `latest`) and `gcloud run deploy`s each service.
To roll back, run **Deploy** by hand with an older tag. `GET /health` on the
api returns the running version. OpenTofu owns the service shell/secrets/
IAM; it isn't re-applied on every deploy (`lifecycle.ignore_changes` on the
image so `tofu apply` won't fight the CI-deployed revision).

## State

No backend configured — state is local by default. Before using this for
real, move it to a GCS bucket (`terraform { backend "gcs" {...} }`) so it
isn't only on one laptop.
