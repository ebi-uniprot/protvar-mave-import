-- Post-import HGVS protein variant breakdown for mave_score.
-- Run after pg_import.sh to verify the distribution matches expected counts.
-- Expected counts are from the 2025-03-10 import; see runs/2025-03-10.json.

-- Single amino acid change: missense, nonsense, synonymous (with optional refseq prefix)
SELECT COUNT(*) FROM mave_score
WHERE hgvs_pro ~ '^(?:[^:]+:)?p\.([A-Z][a-z]{2})([0-9]+)([A-Z][a-z]{2}|=|\*)$'; -- 3,763,601
--    hgvs_pro ~ '^p\.([A-Z][a-z]{2})([0-9]+)([A-Z][a-z]{2}|=|\*)$' -- 3,745,360

-- Explicit synonymous only (p.=)
SELECT COUNT(*) FROM mave_score
WHERE hgvs_pro = 'p.='; -- 41,254

-- Deletions
SELECT COUNT(*) FROM mave_score
WHERE hgvs_pro LIKE '%del'; -- 87,652

-- Insertions
SELECT COUNT(*) FROM mave_score
WHERE hgvs_pro LIKE '%ins%'; -- 204,813

-- Deletion-insertions
SELECT COUNT(*) FROM mave_score
WHERE hgvs_pro LIKE '%delins%'; -- 40,279

-- Frameshifts
SELECT COUNT(*) FROM mave_score
WHERE hgvs_pro ~ 'fs'; -- 2,324

-- Uncertain residue at position (e.g. p.Met1?)
SELECT COUNT(*) FROM mave_score
WHERE hgvs_pro ~ '^p\.[A-Z][a-z]{2}\d+\?$'; -- 58

-- Unknown protein (p.?)
SELECT COUNT(*) FROM mave_score
WHERE hgvs_pro = 'p.?'; -- 6

-- Entries not starting with p. (includes refseq-prefixed entries e.g. NP_009225.1:p.Cys27Tyr)
SELECT COUNT(*) FROM mave_score
WHERE hgvs_pro !~ '^(?:[^:]+:)?p\.'; -- 77

-- Null or empty
SELECT COUNT(*) FROM mave_score
WHERE hgvs_pro IS NULL OR hgvs_pro = ''; -- 444,173

-- Summary of complex variant sub-types (~820,836 total):
--
--   Synonymous (p.=):            41,254
--   Deletions:                   87,652
--   Insertions:                 204,813
--   Deletion-insertions:         40,279
--   Frameshifts:                  2,324
--   Uncertain residue:               58
--   Unknown protein (p.?):            6
--   Non-p. notation:                 77
--   Null/empty:                 444,173