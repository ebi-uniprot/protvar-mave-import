# MAVE → UniProt coverage analysis

Analysis (2026-06-10) of how well MAVE target genes map to a UniProt accession, and which
currently-unextracted fields could improve it. Input: full v3 and v4 `main.json` + their
inferred schemas. Informs future `extract_meta.py` work.

## Scope

We only care about **human (`taxId 9606`) protein-coding** target genes — the rest can't map
to a UniProt accession. In v4 that's **1,185** genes (of 2,790 total / 1,226 human).

100% was never reached: v3 mapped only ~64% of *all* target genes (1,745 / 2,731); 907 had no
external identifier at all.

## Relevant v3 → v4 schema changes

| Field (`targetGenes[]…`) | v3 | v4 | Note |
|---|---|---|---|
| `targetSequence.taxonomy.taxId` | int | renamed **`code`** | already handled in importer |
| `uniprotIdFromMappedMetadata` | — | **new** (str) | MaveDB's auto-derived UniProt acc |
| `mappedHgncName` | — | new (str) | **null everywhere** — useless for now |
| `mappingState` / `mappingErrors` | — | new | whether/how MaveDB mapped the set |
| `targetSequence.sequence` | present | present | the residue sequence (not extracted) |

## Coverage by tier (human protein-coding, n = 1,185)

| Tier | Source | Adds | Cumulative |
|---|---|--:|--:|
| 1 (current) | UniProt `externalIdentifier` | 933 | **78.7%** |
| 2 | **+ `uniprotIdFromMappedMetadata`** | +143 | **90.8%** |
| 3 | + Ensembl/RefSeq → UniProt id conversion | +75 (74 Ensembl, 1 RefSeq) | **97.1%** |
| 4 | + sequence → UniProt (the 34 with no ID) | +≤34 | ~100% |

**The cheap, high-value win is tier 2** — extracting one new field lifts coverage 78.7% → 90.8%.
Tiers 3–4 need external lookups (ID-mapping / sequence alignment).

## Candidate fields / routes

- **`uniprotIdFromMappedMetadata`** (tier 2) — 769 populated in v4; +143 human-PC genes that
  have no UniProt `externalIdentifier`. Where both exist (626 genes) they agree 98% — but 11
  differ, e.g. BRAF curator `P15056` vs mapped `H7C560` (a TrEMBL entry). So use it **only as a
  fallback** after `externalIdentifier`, and consider resolving to canonical SwissProt.
- **RefSeq / Ensembl → UniProt conversion** (tier 3) — for the 74 Ensembl-only + 1 RefSeq-only
  genes (UniProt ID-mapping service, or a local xref table). "Go via another id to accession."
- **`targetSequence.sequence`** (tier 4) — align to UniProt to recover the 34 genes with no
  identifier at all.
- **`mappingState`** — worth capturing as a diagnostic (did MaveDB map this set).
- `mappedHgncName` (null everywhere) and `targetAccession` (sparse, 46 populated) — low value.

## Open questions before coding

1. **Offset.** `externalIdentifiers` carry an `offset` (MAVE→reference coordinate shift);
   `uniprotIdFromMappedMetadata` does **not**. Mapping via it needs an offset from somewhere —
   likely aligning `targetSequence.sequence` to the canonical UniProt, or MaveDB's per-variant
   mapped-variants data. **This is the main thing to resolve for correct position mapping.**
2. `main.json` exposes only the *derived* accession + `mappingState`, **not** per-variant mapped
   coordinates. Precise per-variant UniProt positions would need MaveDB's mapped-variants endpoint.

## Suggested next steps

1. Extract `uniprotIdFromMappedMetadata` (fallback after UniProt `externalIdentifier`) and
   capture `mappingState` — immediate +12 pts for human protein-coding.
2. Settle the offset strategy for mapped-metadata genes (sequence alignment vs mapped-variants).
3. Add Ensembl/RefSeq → UniProt conversion (tier 3).
4. Optional: sequence-based mapping for the remaining ID-less genes (tier 4).
