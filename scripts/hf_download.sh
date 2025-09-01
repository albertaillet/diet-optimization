#!/usr/bin/env bash
set -euo pipefail

# Create directory for dataset
mkdir -p "data/${TARGET}"

echo "Getting latest commit SHA"
# sha="$(curl -fsSL "https://huggingface.co/api/datasets/${DATASET}/revision/main" | jq -r '.sha // .git_oid // empty')"
# sha="$(wget -qO- "https://huggingface.co/api/datasets/${DATASET}/revision/main" | jq -r '.sha // .git_oid // empty')"
sha="$(git ls-remote https://huggingface.co/datasets/${DATASET}.git refs/heads/main | awk '{print $1}')"

if [[ -z "${sha:-}" ]]; then
  echo "Failed to resolve commit SHA for ${DATASET}@main" >&2
  exit 1
fi

sha_url="https://huggingface.co/datasets/${DATASET}/resolve/${sha}/${FILENAME}.parquet"
outpath="data/${TARGET}/${sha}.parquet"

echo "Resolved:"
echo "SHA : $sha"
echo "URL : $sha_url"
echo "Out : $outpath"

if [[ -f "$outpath" ]]; then
  echo "File already exists."
else
  echo "Downloading"
  wget --no-verbose -O "$outpath" "$sha_url"
fi

ln -sfn "${TARGET}/${sha}.parquet" "data/${TARGET}.parquet"
echo "Symlink updated."
