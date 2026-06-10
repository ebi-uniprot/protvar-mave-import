#!/bin/bash
# Full v3 import → mave_identifier_v3 / mave_score_v3 (base tables untouched).
#   MAVE_DATA=/path/to/mave_v3 bash scripts/run_v3.sh &> data/v3/run.log
#
# MAVE_DATA must point to the v3 dataset root (the export dir containing main.json and csv/).
# Also requires PV_DB PV_DBPORT PV_DBNAME PV_DBUSER PV_DBPASS.

set -euo pipefail

: "${MAVE_DATA:?set MAVE_DATA to the v3 dataset root (containing main.json and csv/)}"
OUT=data/v3/output
mkdir -p "$OUT"

python3 scripts/extract_meta.py  --input "$MAVE_DATA/main.json" --output "$OUT/mave_identifier.csv"
python3 scripts/extract_score.py --input "$MAVE_DATA/csv/"      --output "$OUT/mave_score.csv"

export PGPASSWORD="$PV_DBPASS"
PSQL=(psql -h "$PV_DB" -p "$PV_DBPORT" -d "$PV_DBNAME" -U "$PV_DBUSER")
"${PSQL[@]}" -v idtable=mave_identifier_v3 -v sctable=mave_score_v3 -f sql/create_tables.sql
"${PSQL[@]}" -c "TRUNCATE mave_identifier_v3, mave_score_v3"
"${PSQL[@]}" -c "\copy mave_identifier_v3 FROM '$OUT/mave_identifier.csv' CSV HEADER"
"${PSQL[@]}" -c "\copy mave_score_v3 FROM '$OUT/mave_score.csv' CSV HEADER NULL 'NA'"

echo "done: mave_identifier_v3 / mave_score_v3"
