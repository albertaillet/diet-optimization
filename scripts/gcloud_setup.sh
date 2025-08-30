#!/bin/sh
export PROJECT_ID="diet-optimization-460319"
export GITHUB_ORG="albertaillet"
export GITHUB_REPO="diet-optimization"

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

# Grant the Cloud Run Deployer Service Account permissions
# Allows deploying to Cloud Run
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:cloud-run-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Allows pushing images to Artifact Registry
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:cloud-run-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Grant the Cloud Run Runtime Service Account the invoker role
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:runtime-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# Documentation for Workload Identity Federation
# https://github.com/google-github-actions/auth/blob/0dfce0c0f81ee698e8ca7d23b8a0b0706f6370e3/README.md#preferred-direct-workload-identity-federation

# Create a Workload Identity Pool
gcloud iam workload-identity-pools create github-actions-pool \
  --display-name "GitHub Actions WIF Pool" \
  --location="global" \
  --project="${PROJECT_ID}"

# Get the Workload Identity Pool ID
gcloud iam workload-identity-pools describe github-actions-pool --project="${PROJECT_ID}" --location="global" --format="value(name)"

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
gcloud iam workload-identity-pools providers describe github-provider --location="global" --workload-identity-pool="github-actions-pool" --project="${PROJECT_ID}" --format="value(name)"

# Grant the cloud-run-deployer service account permission to be impersonated by the GitHub provider
export PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
gcloud iam service-accounts add-iam-policy-binding "cloud-run-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions-pool/subject/repo:${GITHUB_ORG}/${GITHUB_REPO}:ref:refs/heads/main" # Or whichever branch you want to use

# Create a Artifact Registry repository (this needs billing enabled)
export GCP_REGION="europe-west9"
export GCP_AR_REPO_NAME="diet-optimization-ar"

gcloud artifacts repositories create "${GCP_AR_REPO_NAME}" \
  --repository-format=docker \
  --location="${GCP_REGION}" \
  --description="Docker repository for GitHub Actions" \
  --project="${PROJECT_ID}"
