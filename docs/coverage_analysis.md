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

| Tier | Source | Adds | Cumulative | Status |
|---|---|--:|--:|---|
| 1 | UniProt `externalIdentifier` | 933 | **78.7%** | baseline |
| 2 | **+ `uniprotIdFromMappedMetadata`** | +143 | **90.8%** | ✅ done (2026-06-11) |
| 3 | + Ensembl/RefSeq → UniProt id conversion | +75 (74 Ensembl, 1 RefSeq) | **97.1%** | next |
| 4 | + sequence → UniProt (the 34 with no ID) | +≤34 | ~100% | optional |

**Tier 2 implemented & validated (2026-06-11).** `extract_meta.py` now falls back to
`uniprotIdFromMappedMetadata`; v4 re-imported. Measured human-PC coverage **1,076/1,185 = 90.8%**
(was 78.7%), total UniProt 1,753 → 1,896. The ref-AA check held at **96.5%** overall — the 143
newly-mapped genes contributed ~10,183 checked positions matching at **96.3% at offset 0**, i.e.
they align 1:1 with the canonical UniProt and need **no offset**. Tiers 3–4 need external
lookups (ID-mapping / sequence alignment).

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

## Ref-AA mismatch characterisation (2026-06-11)

The residual ~1,746 mismatched positions (96.5% match) are **offset quality**, not a bug:
- **Not** position-1/Met (only 8 mismatches at pos 1) — the offset fix killed that old problem.
- Spread over 46 accessions (only 2 wholly mismatched), dominated by **suspect curator offsets**:
  `off=0` matches 98.3% (8,085/142), but `off=1` is ~56% wrong (CXCR4 `P61073`, CCR5 `P51681`),
  `off=44` 95% wrong (Q330K2), `off=6608` 93% wrong (P20929); BRCA1 `P38398` (off NULL) is 60% wrong.
- Likely auto-detectable later (pick the offset that maximises match). Not blocking.

## Tier 3 — resolvable locally (2026-06-11)

`rel_2025_01_genomic_protein_mapping` already carries `accession` + `gene_name` / `ensg` / `ensp`
/ `enst` + `is_canonical` (all indexed) — so tier 3 is a **local JOIN, no external API**. Of the
109 still-unmapped human-PC rows, **`gene_name` → canonical accession resolves 97** (subsumes the
56 ensp + 16 ensg hits) → would lift coverage **90.8% → 99.0%**. Only 3 labels fail
(`COMT_ROI1_2`, `S505N`, `W515K` — not HGNC symbols; underlying genes COMT/MPL/MPL).

Decisions for implementing tier 3:
- It must be a **post-load DB step** (the Python extractor has no DB access) — an enrichment
  `UPDATE … SET uniprot = <canonical accession> WHERE uniprot IS NULL` joined on gene_name/ensp.
- It **depends on a ProtVar-internal table** (`rel_2025_01_genomic_protein_mapping`), so — like the
  grants — it may belong in private import-py, not the public mave-import repo.
- **Offset re-validation needed:** these accessions would go in at offset 0 like umm; some MAVE
  sets use non-canonical numbering (e.g. `DDX3X Exon N`), so re-run the ref-AA check after.

## Open questions

1. **Offset — RESOLVED for tier 2.** Concern was that `uniprotIdFromMappedMetadata` carries no
   `offset` (unlike `externalIdentifiers`). The re-import showed the mapped genes match the
   canonical residue at **offset 0** (96.3%), i.e. they're full-length 1:1 alignments — no offset
   needed. (Still relevant if tier 4 sequence-mapping is added: sub-domain targets would need one.)
2. `main.json` exposes only the *derived* accession + `mappingState`, **not** per-variant mapped
   coordinates. Precise per-variant UniProt positions would need MaveDB's mapped-variants endpoint.

## Next steps

1. ~~Extract `uniprotIdFromMappedMetadata` as a UniProt fallback~~ ✅ done (2026-06-11).
2. **Tier 3:** Ensembl/RefSeq → UniProt conversion for the 74 Ensembl-only + 1 RefSeq-only genes.
3. Optional tier 4: sequence-based mapping for the remaining ~34 ID-less genes.
4. Optional: characterise the residual ~1,746 ref-AA mismatches (concentrated sets / offsets).
