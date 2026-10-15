-- Post-load enrichment (coverage tier 3): fill mave_identifier.uniprot for human
-- protein-coding score sets that got no UniProt accession from the importer, by resolving
-- the HGNC gene symbol to the canonical UniProt accession in the genomic protein mapping table.
-- Run after the load step (step 4), before validation. See docs/coverage_analysis.md.
--
-- Effect (v4, 2026-06-12): human-PC coverage 1076/1185 (90.8%) -> 1173/1185 (99.0%).
-- The 12 that remain are non-HGNC labels (COMT_ROI1_2, "S505N MPL", "W515K MPL").
--
--  * WHERE uniprot IS NULL  -> only fills gaps, never overrides an importer-supplied acc;
--    re-running is a no-op.
--  * is_canonical + DISTINCT ON (is_mane_select tiebreak) -> one deterministic accession per gene.
--  * split_part(gene,' ',1) -> some gene labels carry a suffix (e.g. "DDX3X Exon N").
--
-- uniprotoffset is left NULL: these align to the canonical sequence at offset 0
-- (ref-AA check: 97.4% match for the offset-0 cohort).
--
-- Needs rel_2025_01_genomic_protein_mapping in the same DB (as check_ref_aa.sql).
-- Target table: edit the _v4 suffix below to enrich another version.

UPDATE mave_identifier_v4 t
SET uniprot = m.accession
FROM (
    SELECT DISTINCT ON (gene_name) gene_name, accession
    FROM rel_2025_01_genomic_protein_mapping
    WHERE is_canonical
    ORDER BY gene_name, is_mane_select DESC NULLS LAST, accession
) m
WHERE t.uniprot IS NULL
  AND t.genetaxid = 9606
  AND t.genecategory = 'protein_coding'
  AND split_part(t.gene, ' ', 1) = m.gene_name;
