# mave-import

MaveDB import pipeline: extracts a MaveDB export into two CSVs, loads them into PostgreSQL,
maps target genes to UniProt and validates the variants against the UniProt sequence.

Data: https://zenodo.org/record/18511521 · Coverage and quality results:
[`docs/coverage_analysis.md`](docs/coverage_analysis.md)

## Dataset

A MaveDB export has `main.json` (metadata for all experiment sets) and `csv/*.scores.csv`
(one file per score set). Hierarchy: experiment set → experiment → **score set** → target gene
(UniProt/RefSeq/Ensembl IDs + offsets) → variant.

## Output

| CSV / table | Description |
|---|---|
| `mave_identifier_vN` | one row per score-set target gene — gene, taxonomy, UniProt/RefSeq/Ensembl IDs + offsets |
| `mave_score_vN` | one row per variant — HGVS, score; simple `p.` variants split into ref AA / position / alt AA |

## Layout

```
scripts/  extract_meta.py, extract_score.py, run_v3.sh, run_v4.sh
sql/      create_tables.sql, enrich_uniprot_by_gene.sql, check_hgvs.sql, check_ref_aa.sql, compare_versions.sql
utils/    schema generation + main.json slicer
data/vN/  main.json (Git LFS; v3 full, v4 18M slice of 359M), schema/, samples/csv/, run.log (record of the last full run)
```

## Pipeline

1. **Schema** — MaveDB has no formal schema, so regenerate `data/vN/schema/` per release and
   `git diff` it to catch new/renamed fields (v4 renamed `taxonomy.taxId` → `code`; the
   importer reads either).
2. **Field selection** *(manual)* — coded in `extract_meta.py`; revisit when step 1 shows changes.
3. **Extract** — `extract_meta.py` → `mave_identifier.csv`, `extract_score.py` → `mave_score.csv`
   (streaming; parses HGVS).
4. **Load** — `create_tables.sql` + `\copy` into `mave_*_vN` (truncate + reload, safe to re-run).
5. **Enrich** — `enrich_uniprot_by_gene.sql` fills missing UniProt accessions from the gene symbol.
6. **Validate** — `check_hgvs.sql` (HGVS breakdown), `check_ref_aa.sql` (ref AA vs UniProt,
   offset applied).
7. **Export** — the UniProt-mapped score subset as CSV.

## Run

Requires `pip install -r requirements.txt`, `PV_DB PV_DBPORT PV_DBNAME PV_DBUSER PV_DBPASS`, and
`MAVE_DATA` = the export dir (containing `main.json` and `csv/`). Steps 5–6 need
`rel_2025_01_genomic_protein_mapping` (and `amino_acid`, 3→1 letter, for `check_ref_aa.sql`)
in the same DB. SQL scripts name `_v4` tables; edit the suffix for another version.

```bash
export PGPASSWORD=$PV_DBPASS
PSQL="psql -h $PV_DB -p $PV_DBPORT -d $PV_DBNAME -U $PV_DBUSER"

MAVE_DATA=/path/to/mave_v4 bash scripts/run_v4.sh &> data/v4/run.log    # steps 3-4
$PSQL -f sql/enrich_uniprot_by_gene.sql                                  # step 5
$PSQL -f sql/check_hgvs.sql; $PSQL -f sql/check_ref_aa.sql               # step 6
$PSQL -c "\copy (
    SELECT accession AS urn, variant_num, hgvs_nt, hgvs_pro, is_simple_p, score
    FROM mave_score_v4 WHERE accession IN (SELECT urn FROM mave_identifier_v4 WHERE uniprot IS NOT NULL)
) TO 'mave_score_mapped.csv' WITH CSV HEADER"                           # step 7
$PSQL -f sql/compare_versions.sql                                        # optional: v3 vs v4
```

Commit `data/vN/run.log` as the run record. Without arguments the extractors run on the bundled
`data/v4/` dev slice.

Regenerate the dev slice and schema from a full export:

```bash
python utils/sample_main_json.py --input $MAVE_DATA/main.json --output data/v4/main.json --max-mb 18
python utils/describe_json.py  --input $MAVE_DATA/main.json > data/v4/schema/json_summary.txt
python utils/infer_schema.py   --input $MAVE_DATA/main.json > data/v4/schema/json_schema.json
```
