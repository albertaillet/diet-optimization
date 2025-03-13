#!/bin/bash
# Navigate to the directory with the cProfile outputs
# if 1 is not provided take the latest file in the tmp/benchmark directory
folder=$1
if [ -z "$1" ]; then
    folder=tmp/benchmark/$(ls -t tmp/benchmark | head -n1)
    echo "No argument provided. Using latest folder: $folder"
fi

# Convert all .out files to .svg
for file in "$folder"/*.out; do
    echo "Converting $file..."
    svg_file="${file%.out}.svg"
    uvx gprof2dot -f pstats "$file" | dot -Tsvg -o "$svg_file"
    echo "Converted $svg_file"
done

# Run a python webserver to serve only the .svg files
echo "Serving .svg files in $folder..."
uvx python -m http.server --directory $folder 8000
