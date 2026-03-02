# MaveDB JSON Schema

MaveDB does not publish a formal schema for its JSON export format. The files
in this directory were derived directly from the `main.json` export to
understand the data structure and identify which fields are relevant for
extraction.

## Files

**`json_summary.txt`** — A human-readable tree of every key, its type, and
its depth in the hierarchy, produced by `utils/describe_json.py`. 

**`json_schema.json`** — A JSON Schema inferred from the
full dataset using `genson`, produced by `utils/convert2schema.py`. Useful
for validating future exports and checking whether the structure has changed
between MaveDB releases.

## How to regenerate

If you download a newer `main.json`, regenerate both files to check for
structural changes before re-running the import:

    python utils/describe_json.py > docs/schema/json_summary.txt
    python utils/convert2schema.py > docs/schema/json_schema.json

Then diff against the committed versions:

    git diff docs/schema/

Any new keys or type changes in the diff may indicate new fields worth
extracting, or breaking changes that require updates to mave_main_import.py.