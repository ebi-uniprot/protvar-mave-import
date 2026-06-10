-- Consistency check: validates that ref_aa parsed from MAVE HGVS notation matches
-- the canonical reference amino acid in the genomic protein mapping table at the
-- same UniProt accession and position.
--
-- Scope: human (taxId=9606), protein-coding, UniProt-mapped, simple p. variants only.
--
-- Offset: uniprotoffset from mave_identifier is applied to convert MAVE residue
-- numbering to UniProt coordinates. MAVE experiments sometimes number residues
-- relative to a sub-domain rather than the full canonical UniProt sequence.
-- Formula: uniprot_position = mave_position + uniprotoffset
--
-- Index recommended on the mapping table if not already present:
-- CREATE INDEX rel_2025_01_genomic_protein_mapping_acc_pro_pos_seq_idx
--     ON rel_2025_01_genomic_protein_mapping (accession, protein_position, protein_seq);

WITH filtered_mave_id AS (
    SELECT *
    FROM mave_identifier
    WHERE uniprot IS NOT NULL
      AND genetaxid = 9606
      AND genecategory = 'protein_coding'
)
   , filtered_mave_score AS (
    SELECT *
    FROM mave_score
    WHERE is_simple_p IS TRUE
)
   , mapping AS (
    SELECT DISTINCT accession, protein_position, protein_seq
    FROM rel_2025_01_genomic_protein_mapping
)
SELECT
    DISTINCT mi.uniprot                                  AS accession,
             ms.position                                          AS mave_position,
             ms.position + COALESCE(mi.uniprotoffset, 0)          AS uniprot_position,
             mi.uniprotoffset,
             aa.one_letter                                        AS mave_ref,
             gpm.protein_seq                                      AS mapping_ref
FROM filtered_mave_id mi
JOIN filtered_mave_score ms
  ON ms.accession = mi.urn
JOIN amino_acid aa
  ON ms.ref_aa = aa.three_letter
JOIN mapping gpm
  ON  mi.uniprot = gpm.accession
      AND ms.position + COALESCE(mi.uniprotoffset, 0) = gpm.protein_position
WHERE
    gpm.protein_seq <> aa.one_letter   -- mismatches; swap <> for = to see matches
;

-- To check the offset distribution before running the full validation:
-- SELECT uniprotoffset, COUNT(*)
-- FROM mave_identifier
-- WHERE uniprot IS NOT NULL AND genetaxid = 9606
-- GROUP BY uniprotoffset
-- ORDER BY uniprotoffset;