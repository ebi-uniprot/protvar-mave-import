# Sample data

Sample data files from the full MaveDB dataset, for testing, and verifying the pipeline without needing the
full data files.

## Contents

**`first_10.json`** — First 10 experiment sets from `main.json`, extracted with:

    jq '.experimentSets[:10]' data/main.json > data/samples/first_10.json

**`csv/`** — First 4 score CSV files taken directly
from the full CSV folder.

**`output/`** — Output files generated from the sample data above.

## Running the pipeline

**Sample run** — uses sample data by default, no arguments needed:

    python scripts/mave_main_import.py
    python scripts/mave_score_import.py

**Full run** — specify paths explicitly:

    python scripts/mave_main_import.py \
        --input data/main.json \
        --output mave_identifier.csv

    python scripts/mave_score_import.py \
        --input /path/to/full/csv/folder \
        --output mave_score.csv