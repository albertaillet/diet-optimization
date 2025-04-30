#!/bin/sh

# If watching, use trap to clean up on Ctrl+C
if [ "$1" = "watch" ]; then
  trap "kill 0" EXIT
  esbuild js/index.js --outfile=../static/bundle.js --bundle --format=esm --platform=browser --watch=forever &
  esbuild styles.css --outfile=../static/bundle.css --watch=forever &
  wait
else
  esbuild js/index.js --outfile=../static/bundle.js --bundle --format=esm --platform=browser --minify
  esbuild styles.css --outfile=../static/bundle.css --minify
fi
