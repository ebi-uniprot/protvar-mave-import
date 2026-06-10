# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Overview

ETL pipeline that imports full MaveDB exports into PostgreSQL.
See [`README.md`](README.md) — the single source for the pipeline, data layout, and commands.

## Repo conventions & gotchas

- **Dataset version:** currently MaveDB **v3**; v4 re-run pending. Datasets live per
  version under `data/vN/`; full exports are downloaded separately (Zenodo). v4's full
  export is ~359 MB, so the repo ships a ~18 MB slice (`utils/sample_main_json.py`).
  `main.json` shape may change between versions — regenerate and diff `data/vN/schema/`
  before importing.
- **Version tolerance:** v3→v4 renamed `taxonomy.taxId` → `taxonomy.code`; the importer
  reads either. For larger future divergence, prefer a per-version field map over stacking
  fallbacks. v4 also adds `targetGenes[].uniprotIdFromMappedMetadata` — a possible new
  UniProt-mapping source, not yet used.
- **Load:** `sql/create_tables.sql` (DDL, takes psql `-v idtable=… -v sctable=…`), then the
  CSVs go in via `psql -c "\copy <table> FROM '<path>' …"`. The `\copy` must use literal
  table/path — psql does NOT interpolate `:`-variables inside `\copy` (only in regular SQL),
  so the run scripts build it with the names baked in. `scripts/run_v3.sh` / `run_v4.sh` do
  the full per-version extract+load into `mave_*_vN`, leaving base tables untouched. They
  require `MAVE_DATA` (the version's dataset root, with `main.json` + `csv/`) and exit if unset.
- **Git LFS:** `data/**/main.json` is tracked via LFS.
- **`check_ref_aa.sql`** needs two external tables in the target DB:
  `rel_2025_01_genomic_protein_mapping` and `amino_acid` (3→1 letter lookup). It must
  apply the identifier offset (`mave_position + uniprotoffset`) — never compare raw positions.
- **Field selection is manual:** the extracted fields are hard-coded in `extract_meta.py`;
  revisit when a schema diff surfaces new fields.
- **Versioned tables, no base:** load targets `mave_*_vN`; there is no unsuffixed base table.
  `check_*.sql` / `compare_versions.sql` name a version directly (edit the `_v3` suffix) — kept
  un-parameterised on purpose (one-off scripts).
- **Grants are NOT in this (public) repo:** read grants for downstream roles live in the
  private `protvar-import-py/mave/mave_tables_grants.sql`, applied manually on prod.
