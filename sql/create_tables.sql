-- mave_identifier: score set metadata and gene annotations
CREATE TABLE IF NOT EXISTS mave_identifier (
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

-- mave_score: variant-level functional scores with parsed HGVS notation
-- Note: hgvs_pro must be VARCHAR (unbounded) — some complex HGVS strings exceed 255 chars.
CREATE TABLE IF NOT EXISTS mave_score (
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