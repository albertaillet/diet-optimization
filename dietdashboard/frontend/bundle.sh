#!/bin/sh

# If watching, use trap to clean up on Ctrl+C
if [ "$1" = "watch" ]; then
  trap "kill 0" EXIT
  esbuild ts/index.ts --outfile=../static/bundle.js --bundle --platform=browser --watch=forever &
  esbuild styles.css --outfile=../static/bundle.css --watch=forever &
  wait
else
  esbuild ts/index.ts --outfile=../static/bundle.js --bundle --minify --platform=browser
  esbuild styles.css --outfile=../static/bundle.css --minify
fi
