-- compare_versions.sql
-- Compare the MaveDB v3 vs v4 imported tables (and the base backup).
-- Run after:  run_v3.sh  &&  run_v4.sh
--
--   psql -h $PV_DB -p $PV_DBPORT -d $PV_DBNAME -U $PV_DBUSER -f sql/compare_versions.sql

-- 1. Row counts: base backup vs v3 vs v4
SELECT 'mave_identifier' AS tbl, 'base' AS ver, count(*) FROM mave_identifier
UNION ALL SELECT 'mave_identifier', 'v3', count(*) FROM mave_identifier_v3
UNION ALL SELECT 'mave_identifier', 'v4', count(*) FROM mave_identifier_v4
UNION ALL SELECT 'mave_score',      'base', count(*) FROM mave_score
UNION ALL SELECT 'mave_score',      'v3', count(*) FROM mave_score_v3
UNION ALL SELECT 'mave_score',      'v4', count(*) FROM mave_score_v4
ORDER BY tbl, ver;

-- 2. Score-set / human / UniProt-mapped breakdown per version
SELECT 'v3' AS ver,
       count(*)                                       AS score_sets,
       count(*) FILTER (WHERE genetaxid = 9606)       AS human,
       count(*) FILTER (WHERE uniprot IS NOT NULL)    AS with_uniprot
FROM mave_identifier_v3
UNION ALL
SELECT 'v4',
       count(*),
       count(*) FILTER (WHERE genetaxid = 9606),
       count(*) FILTER (WHERE uniprot IS NOT NULL)
FROM mave_identifier_v4;

-- 3. Score-set URNs added / removed between v3 and v4
SELECT 'only_in_v3' AS delta, urn FROM mave_identifier_v3
  WHERE urn NOT IN (SELECT urn FROM mave_identifier_v4)
UNION ALL
SELECT 'only_in_v4', urn FROM mave_identifier_v4
  WHERE urn NOT IN (SELECT urn FROM mave_identifier_v3)
ORDER BY delta, urn;

-- 4. Shared score sets whose number of score rows changed (top 50 by magnitude)
WITH v3 AS (SELECT accession, count(*) n FROM mave_score_v3 GROUP BY accession),
     v4 AS (SELECT accession, count(*) n FROM mave_score_v4 GROUP BY accession)
SELECT v3.accession AS urn, v3.n AS v3_rows, v4.n AS v4_rows, v4.n - v3.n AS delta
FROM v3 JOIN v4 ON v3.accession = v4.accession
WHERE v3.n <> v4.n
ORDER BY abs(v4.n - v3.n) DESC
LIMIT 50;
