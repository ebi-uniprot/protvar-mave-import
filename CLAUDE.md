# CLAUDE.md

Guidance for Claude Code in this repository. See [`README.md`](README.md) for the pipeline,
data layout, and commands — this file only records decisions an agent shouldn't quietly undo.

## Guardrails (deliberate — don't "fix" them back)

- **Load uses `psql -c "\copy <table> FROM '<path>'"` with literal names, not a parameterised
  `load.sql`.** psql does NOT interpolate `:`-variables inside `\copy` (only in regular SQL);
  a parameterised `\copy` silently fails — that bug was already hit and fixed. `create_tables.sql`
  (plain SQL) does take `-v idtable=/sctable=`.
- **`check_*.sql` / `compare_versions.sql` name a version table directly (edit the `_v3`
  suffix); kept un-parameterised on purpose** — one-off manual scripts.
- **No unsuffixed base table** — load targets `mave_*_vN`; base `mave_identifier`/`mave_score`
  were retired.
- **Grants are NOT in this (public) repo** — read grants for internal roles live in the private
  `protvar-import-py/sql/mave_tables_grants.sql`, applied manually on prod.
- **Version divergence** — v3→v4 renamed `taxonomy.taxId`→`code` (importer reads either). If a
  future release diverges more, prefer a per-version field map over stacking fallbacks.
