# MAVE → UniProt coverage and quality

How well MaveDB target genes map to a UniProt accession, and whether the mapped variants agree
with the UniProt sequence. Measured on the full **v4** export (2026-06, ref-AA re-run 2026-10-15).

## Scope

Only **human (`taxId 9606`) protein-coding** targets can map to UniProt: **1,185** of 2,790
score sets in v4 (1,226 human). For reference, v3 mapped ~64% of *all* targets (1,745 / 2,731).

## Coverage (human protein-coding, n = 1,185)

| Tier | Source | Adds | Cumulative |
|---|---|--:|--:|
| 1 | UniProt `externalIdentifier` (curator, with offset) | 933 | 78.7% |
| 2 | `targetGenes[].uniprotIdFromMappedMetadata` (new in v4) — `extract_meta.py` fallback | +143 | 90.8% |
| 3 | gene symbol → canonical accession — `sql/enrich_uniprot_by_gene.sql` | +97 | **99.0%** |
| 4 | sequence → UniProt (not done) | ≤12 | ~100% |

- **Tier 2** is a fallback only: where both IDs exist (626 genes) they agree 98%, but some differ
  (e.g. BRAF curator `P15056` vs mapped `H7C560`, a TrEMBL entry).
- **Tier 3** keys the first token of the gene label (e.g. `DDX3X Exon N` → `DDX3X`) on
  `rel_2025_01_genomic_protein_mapping` (`is_canonical`, `is_mane_select` tiebreak). Every
  resolvable symbol mapped to exactly one canonical accession. It only fills `uniprot IS NULL`.
- **Unmapped (12 score sets):** non-HGNC labels `COMT_ROI1_2`, `S505N MPL`, `W515K MPL`.
- Tiers 2–3 carry no offset; both align to the canonical sequence at offset 0 (see below).

## Reference amino-acid check

`sql/check_ref_aa.sql`: parsed `ref_aa` of simple `p.` variants vs the canonical UniProt residue
at `position + uniprotoffset`. v4 after tier 3, distinct positions:

| Cohort | Match | Positions | Rate |
|---|--:|--:|--:|
| Offset 0 (incl. all tier 2–3 fills) | 19,802 | 20,325 | 97.4% |
| Curator offset ≠ 0 | 30,529 | 31,774 | 96.1% |
| **All** | **50,331** | **52,099** | **96.6%** |

Residual mismatches are offset quality, not parsing: concentrated in a few sets with suspect
curator offsets (CXCR4 `P61073` / CCR5 `P51681` at offset 1 ~56% wrong; offsets 44 and 6608
>90% wrong; BRCA1 `P38398` ~60% wrong).

## Open items

1. Tier 4: sequence-map the 12 unmapped score sets.
2. Auto-correct suspect offsets (pick the offset that maximises ref-AA match).
3. `main.json` gives only the target accession, not per-variant mapped coordinates; precise
   per-variant UniProt positions would need MaveDB's mapped-variants endpoint.
