#!/bin/bash
# pg_import.sh
# Creates the mave_identifier and mave_score tables and loads data from CSV files.
#
# Usage:
#   bash scripts/pg_import.sh                                     # default paths
#   bash scripts/pg_import.sh /path/to/mave_identifier.csv \
#                             /path/to/mave_score.csv             # explicit paths
#
# Required environment variables:
#   PV_DB      PostgreSQL host
#   PV_DBPORT  PostgreSQL port
#   PV_DBNAME  Database name
#   PV_DBUSER  Database user
#   PV_DBPASS  Database password

set -euo pipefail

IDENTIFIER_CSV="${1:-mave_identifier.csv}"
SCORE_CSV="${2:-mave_score.csv}"

# Validate inputs
if [ ! -f "$IDENTIFIER_CSV" ] || [ ! -f "$SCORE_CSV" ]; then
    echo "Required CSV files not found"
    exit 1
fi

export PGPASSWORD="$PV_DBPASS"

PSQL=(psql -h "$PV_DB" -p "$PV_DBPORT" -d "$PV_DBNAME" -U "$PV_DBUSER")

echo "Test connection..."
"${PSQL[@]}" -c "SELECT version();"

echo "Creating tables..."
"${PSQL[@]}" -f sql/create_tables.sql

echo "Truncating tables..."
"${PSQL[@]}" -c "TRUNCATE mave_identifier, mave_score;"

echo "Loading mave_identifier from $IDENTIFIER_CSV..."
"${PSQL[@]}" -c "\copy mave_identifier FROM '$IDENTIFIER_CSV' CSV HEADER"

echo "Loading mave_score from $SCORE_CSV..."
# NULL 'NA' required: score column contains literal "NA" for missing values
"${PSQL[@]}" -c "\copy mave_score FROM '$SCORE_CSV' CSV HEADER NULL 'NA'"

echo "Import complete"
echo ""
echo "Next steps:"
echo "  Verify HGVS breakdown:  psql ... -f sql/check_hgvs.sql"
echo "  Validate ref amino acids: psql ... -f sql/check_ref_aa.sql"