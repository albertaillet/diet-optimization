#!/bin/sh
# Script to print the HEAD commit SHA and commit date for a remote git repo, with no data blobs fetched.

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <remote-repo-url>"
  echo "Output: <sha>\t<YYYYMMDD>"
  exit 2
fi

# HEAD SHA without cloning
sha=$(git ls-remote --quiet "$1" HEAD | awk '{print $1}')

tmp=$(mktemp -d)

# fetch only that commit object (no blobs, no LFS)
git -C "$tmp" init -q
git -C "$tmp" remote add origin "$1"
GIT_LFS_SKIP_SMUDGE=1 git -C "$tmp" fetch --quiet --depth 1 --filter=blob:none origin "$sha"

# extract commit date to YYYYMMDD
date=$(git -C "$tmp" show -s --format=%cd --date=format:%Y%m%d "$sha")

rm -rf "$tmp"

printf '%s\t%s\n' "$sha" "$date"
