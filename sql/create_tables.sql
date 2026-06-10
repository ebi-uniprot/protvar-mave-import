-- create_tables.sql — create the mave tables (pre-step; run before \copy-loading the CSVs).
--
-- Pass table names as psql variables:
--   psql ... -v idtable=mave_identifier -v sctable=mave_score -f sql/create_tables.sql
-- For a versioned run, name suffixed tables, e.g. -v idtable=mave_identifier_v4 ...

-- mave_identifier: score-set metadata and gene annotations (one row per target gene)
CREATE TABLE IF NOT EXISTS :"idtable" (
    urn           VARCHAR(50),
    numVariants   INT,
    Gene          VARCHAR(255),
    GeneCategory  VARCHAR(255),
    GeneTaxId     INT,
    UniProt       VARCHAR(255),
    UniProtOffset INT,
    RefSeq        VARCHAR(255),
    RefSeqOffset  INT,
    Ensembl       VARCHAR(255),
    EnsemblOffset INT
);

-- mave_score: variant-level functional scores with parsed HGVS notation.
-- hgvs_pro must be unbounded VARCHAR — some complex HGVS strings exceed 255 chars.
CREATE TABLE IF NOT EXISTS :"sctable" (
    accession   VARCHAR(50),
    variant_num INT,
    hgvs_nt     VARCHAR,
    hgvs_pro    VARCHAR,
    is_simple_p BOOLEAN,
    ref_aa      VARCHAR(3),
    position    INTEGER,
    alt_aa      VARCHAR(3),
    score       DOUBLE PRECISION
);
