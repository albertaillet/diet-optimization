#!/bin/bash
# check if the data.csv file exists
link="https://raw.githubusercontent.com/openfoodfacts/openfoodfacts-server/refs/heads/main/external-data/ciqual/calnut/CALNUT.csv.1";
if [ ! -f calnut.csv ]; then
    curl $link > calnut.csv
fi
python -m http.server
