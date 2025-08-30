#!/bin/sh
export PROJECT_ID="diet-optimization-460319"
export GITHUB_ORG="albertaillet"

echo "You probably should run this step by step by pasting each command into your terminal."
exit

# Create the Cloud Run Deployer Service Account
gcloud iam service-accounts create cloud-run-deployer \
  --display-name "Service Account for GitHub Actions Cloud Run Deployments" \
  --project="${PROJECT_ID}"

# Create the Cloud Run Runtime Service Account
gcloud iam service-accounts create runtime-sa \
  --display-name "Service Account for Cloud Run Service Runtime" \
  --project="${PROJECT_ID}"

# Get your project number
gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)"

# Documentation for Workload Identity Federation
# https://github.com/google-github-actions/auth/blob/0dfce0c0f81ee698e8ca7d23b8a0b0706f6370e3/README.md#preferred-direct-workload-identity-federation

# Create a Workload Identity Pool
gcloud iam workload-identity-pools create github-actions-pool \
  --display-name "GitHub Actions WIF Pool" \
  --location="global" \
  --project="${PROJECT_ID}"

# Get the Workload Identity Pool ID
gcloud iam workload-identity-pools describe github-actions-pool \
  --project="${PROJECT_ID}" \
  --location="global" \
  --format="value(name)"

# Create a Workload Identity Provider within the pool for GitHub
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-actions-pool" \
  --display-name="My GitHub repo Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner == '${GITHUB_ORG}'" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Get the Workload Identity Provider ID
gcloud iam workload-identity-pools providers describe github-provider \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-actions-pool" \
  --format="value(name)"

# TODO:
# Grant the cloud-run-deployer service account permission to be impersonated by the GitHub provider
# gcloud iam service-accounts add-iam-policy-binding cloud-run-deployer@"${PROJECT_ID}".iam.gserviceaccount.com \
#   --role="roles/iam.workloadIdentityUser" \
#   --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${WIF_POOL_ID}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}" \
#   --project="${PROJECT_ID}"
