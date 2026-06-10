# mave-import

maveDB dataset import pipeline. Extracts the relevant data from a MaveDB export into two
CSVs, optionally loaded into PostgreSQL tables (for querying).

Data: https://zenodo.org/record/18511521

## Dataset

A MaveDB export contains:
- `main.json` — metadata for all experiment sets
- `csv/*.scores.csv` — variant scores, one file per score set (e.g. `urn-mavedb-00000001-a-1.scores.csv`)

Hierarchy: experiment set → experiment → **score set** (the scored dataset, one `.scores.csv`)
→ target gene (UniProt/RefSeq/Ensembl IDs + offsets) → variant.

The repo ships dev-sized copies per version under `data/vN/` (full exports from the Zenodo
link above):

```
data/vN/
  main.json        # v3: full (17M). v4: ~18M slice (full is 359M) — both LFS
  schema/          # inferred from the FULL export (json_summary.txt, json_schema.json)
  samples/csv/     # a few *.scores.csv for the score importer
  run.log          # output of the last full run_vN.sh (committed as the run record)
  LICENSE.txt
```

Sample CSVs are the four files for `urn-mavedb-00000001` (present in both versions).
Regenerate the v4 slice / schema from the full export (`<full>` = downloaded dataset dir):
```bash
python utils/sample_main_json.py --input <full>/main.json --output data/v4/main.json --max-mb 18
python utils/describe_json.py  --input <full>/main.json > data/v4/schema/json_summary.txt
python utils/infer_schema.py   --input <full>/main.json > data/v4/schema/json_schema.json
```

## Output

Two CSVs (one per importer), optionally loaded into matching PostgreSQL tables:

| CSV / table | Description |
|---|---|
| `mave_identifier` | one row per score-set target gene (usually 1 per score set) — gene, taxonomy, UniProt/RefSeq/Ensembl IDs + offsets |
| `mave_score` | one row per variant — parsed HGVS, functional score, amino acid components |

## Layout

```
scripts/  extract_meta.py, extract_score.py, run_v3.sh, run_v4.sh
sql/      create_tables.sql, validation + comparison queries
utils/    schema generation + main.json slicer
data/     vN/{main.json, schema/, samples/csv/}
```

`data/**/main.json` is tracked via Git LFS.

## Versions

v3 (original), v4 (update). MaveDB has no formal schema and `main.json` can change between
releases — so each run starts by regenerating and diffing the schema (pipeline step 1).
v4 renamed `taxonomy.taxId` → `code` (the importer reads either).

## Pipeline

1. **Schema** — describe + infer the JSON structure to `data/vN/schema/`, then `git diff`
   per release to catch new/renamed fields:
   `utils/describe_json.py` / `infer_schema.py --input <main.json>`.
2. **Field selection** *(manual)* — which fields to extract are coded in `extract_meta.py`;
   revisit when the step-1 diff surfaces something new.
3. **Import → 2 CSVs** — two stream-processing importers (memory-efficient):
   `extract_meta.py` → `mave_identifier.csv`; `extract_score.py` → `mave_score.csv`
   (parses HGVS, splits simple `p.` vs complex).
4. **Load → PostgreSQL** — create the tables (`sql/create_tables.sql`) then `\copy` the CSVs
   in; needed for validation and querying. Joined in-DB by URN.
5. **Validate** — `sql/check_hgvs.sql`; `sql/check_ref_aa.sql` checks parsed `ref_aa` vs the
   canonical residue, applying the offset (`pos + uniprotoffset`). Both target the `_v3`
   tables — edit the suffix to check another version.
6. **Export** — extract the UniProt-mapped score subset to a CSV for downstream use (see Run).

## Run

Setup: `pip install -r requirements.txt`. Importers default to the bundled `data/v4/` dev
data; pass `--input`/`--output` for full runs.

```bash
# 3. Extract → 2 CSVs
python scripts/extract_meta.py
python scripts/extract_score.py

# 4. Load → PostgreSQL: create tables, then \copy (base tables; safe to re-run)
export PV_DB=host PV_DBPORT=5432 PV_DBNAME=db PV_DBUSER=user PV_DBPASS=pass PGPASSWORD=$PV_DBPASS
PSQL="psql -h $PV_DB -p $PV_DBPORT -d $PV_DBNAME -U $PV_DBUSER"
$PSQL -v idtable=mave_identifier -v sctable=mave_score -f sql/create_tables.sql
$PSQL -c "\copy mave_identifier FROM 'data/v4/output/mave_identifier.csv' CSV HEADER"
$PSQL -c "\copy mave_score FROM 'data/v4/output/mave_score.csv' CSV HEADER NULL 'NA'"

# 5. Validate
psql -h $PV_DB -p $PV_DBPORT -d $PV_DBNAME -U $PV_DBUSER -f sql/check_hgvs.sql
psql -h $PV_DB -p $PV_DBPORT -d $PV_DBNAME -U $PV_DBUSER -f sql/check_ref_aa.sql
```

### Re-run both versions and compare

Loads the full datasets into **version-suffixed** tables (`mave_*_v3`, `mave_*_v4`), then
diffs v3 against v4.
Prerequisites: `PV_DB*` set, and `MAVE_DATA` pointing to the dataset root for the version
you're running (the export dir containing `main.json` and `csv/`). The scripts exit if
`MAVE_DATA` is unset.

```bash
MAVE_DATA=/path/to/mave_v3 bash scripts/run_v3.sh &> data/v3/run.log   # → mave_*_v3  (long-running)
MAVE_DATA=/path/to/mave_v4 bash scripts/run_v4.sh &> data/v4/run.log   # → mave_*_v4  (long-running)
psql -h $PV_DB -p $PV_DBPORT -d $PV_DBNAME -U $PV_DBUSER -f sql/compare_versions.sql
```

Each script = extract meta → extract scores → create + `\copy`-load `mave_*_<v>`. Base tables
are never touched; re-running is safe (suffixed tables truncate+reload). The `&> data/vN/run.log`
redirect captures the run output (extract counts, HGVS breakdown, load tags) — commit it as
the run record.

### Export the UniProt-mapped subset

```bash
PGPASSWORD="$PV_DBPASS" psql -h "$PV_DB" -p "$PV_DBPORT" -d "$PV_DBNAME" -U "$PV_DBUSER" -c "\copy (
    SELECT accession AS urn, variant_num, hgvs_nt, hgvs_pro, is_simple_p, score
    FROM mave_score_v3 WHERE accession IN (SELECT urn FROM mave_identifier_v3 WHERE uniprot IS NOT NULL)
) TO 'mave_score_mapped.csv' WITH CSV HEADER;"
```

## Notes

- **Coverage:** direct UniProt mapping only; RefSeq/Ensembl-only sets need an ID-conversion
  step (v4's new `targetGenes[].uniprotIdFromMappedMetadata` may help).
- **HGVS:** only simple single-residue `p.` variants are decomposed; complex kept as-is.
- **`check_ref_aa.sql`** needs external `rel_2025_01_genomic_protein_mapping` and
  `amino_acid` (3→1 letter) tables in the target DB.
