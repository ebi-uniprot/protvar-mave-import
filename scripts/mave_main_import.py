import argparse
import json
import csv
import os
from collections import defaultdict

"""
This script processes the large JSON file (`main.json`) and extracts selected fields 
from nested score set structures. The following fields are captured and written to CSV 
for downstream analysis:

Extracted fields (with JSON paths):

# ScoreSet-level metadata:
- experimentSets[].experiments[].scoreSets[].urn                  → Unique identifier for the score set
- experimentSets[].experiments[].scoreSets[].numVariants         → Number of variants in the score set
- experimentSets[].experiments[].scoreSets[].recordType          → Record classification (e.g., variant set)

# Gene-level annotations:
- experimentSets[].experiments[].scoreSets[].targetGenes[].name                          → HGNC gene name
- experimentSets[].experiments[].scoreSets[].targetGenes[].category                      → Gene category (e.g., protein-coding)
- experimentSets[].experiments[].scoreSets[].targetGenes[].targetSequence.taxonomy.taxId → NCBI Taxonomy ID (e.g., 9606 for human)

# Gene-level identifiers:
- experimentSets[].experiments[].scoreSets[].targetGenes[].externalIdentifiers[].identifier.dbName       → Source DB (e.g., UniProt, RefSeq, Ensembl)
- experimentSets[].experiments[].scoreSets[].targetGenes[].externalIdentifiers[].identifier.identifier   → Corresponding gene/protein identifier

New added:
- experimentSets[].experiments[].scoreSets[].targetGenes[].externalIdentifiers[].offset

These are the only fields from the large JSON structure that are parsed and written to CSV.
"""


# experimentSets[].experiments[].scoreSets[].urn
# experimentSets[].experiments[].scoreSets[].numVariants
# experimentSets[].experiments[].scoreSets[].targetGenes[].name
# experimentSets[].experiments[].scoreSets[].targetGenes[].category
# experimentSets[].experiments[].scoreSets[].targetGenes[].externalIdentifiers[].identifier.dbName
# experimentSets[].experiments[].scoreSets[].targetGenes[].externalIdentifiers[].identifier.identifier
# experimentSets[].experiments[].scoreSets[].targetGenes[].targetSequence.taxonomy.taxId
def extract_score_set_data(json_path, output_csv):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # main.json is a full export object {"experimentSets": [...], ...};
    # sample files (e.g. first_10.json) are bare lists produced by jq slice:
    #   jq '.experimentSets[:10]' main.json > first_10.json
    experiment_sets = data if isinstance(data, list) else data.get("experimentSets", [])
    extracted_rows = []

    # Summary counters
    human_sets = 0
    nonhuman_sets = 0
    protein_coding_sets = 0
    with_refseq = 0
    #with_ensg = 0
    ensembl_prefix_counts = defaultdict(int)
    with_gene_name = 0
    with_uniprot = 0

    for exp_set in experiment_sets:
        experiments = exp_set.get("experiments", [])
        for experiment in experiments:
            score_sets = experiment.get("scoreSets", [])
            for score in score_sets:
                # Initialize with empty identifiers
                base_row = {
                    #"recordType": score.get("recordType"),
                    "urn": score.get("urn"),
                    "numVariants": score.get("numVariants"),
                }

                # Loop through targetGenes and their externalIdentifiers
                for target_gene in score.get("targetGenes", []):
                    row = base_row.copy()
                    gene_name = target_gene.get("name", "")
                    gene_category = target_gene.get("category", "")

                    row["Gene"] = gene_name
                    row["GeneCategory"] = gene_category
                    #other_noncoding,10
                    #regulatory,35
                    #protein_coding,2686

                    row["UniProt"] = ""
                    row["UniProtOffset"] = None
                    row["RefSeq"] = ""
                    row["RefSeqOffset"] = None
                    row["Ensembl"] = ""
                    row["EnsemblOffset"] = None

                    for ext_id in target_gene.get("externalIdentifiers", []):
                        identifier = ext_id.get("identifier", {})
                        db_name = identifier.get("dbName")
                        id_value = identifier.get("identifier")

                        if db_name == "Ensembl" and id_value:
                            prefix = id_value[:4]
                            ensembl_prefix_counts[prefix] += 1
                        if db_name in row and not row[db_name]:
                            row[db_name] = id_value
                            # Handle offset - must be a whole number
                            offset = ext_id.get("offset")
                            if offset is not None and offset != "":
                                try:
                                    row[f'{db_name}Offset'] = int(str(offset))
                                except (ValueError, TypeError):
                                    # offset is not a valid integer, leave as None
                                    pass

                    target_sequence = target_gene.get("targetSequence") or {}
                    taxonomy = target_sequence.get("taxonomy") or {}
                    tax_id = str(taxonomy.get("taxId", ""))
                    row["GeneTaxId"] = tax_id

                    # Count summaries
                    if tax_id == "9606":
                        human_sets += 1
                    else:
                        nonhuman_sets += 1

                    if gene_category == "protein_coding":
                        protein_coding_sets += 1

                    if row["RefSeq"]:
                        with_refseq += 1
                    #if row["Ensembl"].startswith("ENSG"):
                    #    with_ensg += 1
                    if gene_name:
                        with_gene_name += 1
                    if row["UniProt"]:
                        with_uniprot += 1

                    extracted_rows.append(row)

    # Write to CSV
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            #"recordType",
            "urn", "numVariants", "Gene", "GeneCategory", "GeneTaxId", "UniProt", "UniProtOffset", "RefSeq", "RefSeqOffset", "Ensembl", "EnsemblOffset"
        ])
        writer.writeheader()
        writer.writerows(extracted_rows)

    # Print summary
    print(f"Extracted {len(extracted_rows)} score sets to {output_csv}")
    print("\nSummary:")
    print(f"  Human sets (taxId=9606): {human_sets}")
    print(f"  Non-human sets: {nonhuman_sets}")
    print(f"  Protein-coding sets: {protein_coding_sets}")
    print(f"  With RefSeq: {with_refseq}")
    #print(f"  With Ensembl (ENSG): {with_ensg}")
    print(f"  With Ensembl")
    for prefix, count in sorted(ensembl_prefix_counts.items()):
        print(f"     {prefix}: {count}")
    print(f"  With gene name: {with_gene_name}")
    print(f"  With UniProt: {with_uniprot}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Extract score set metadata from a MaveDB JSON export."
    )
    parser.add_argument(
        "--input",
        default="data/samples/first_10.json",
        help="Path to the MaveDB JSON file (default: data/samples/first_10.json)"
    )
    parser.add_argument(
        "--output",
        default="data/samples/output/mave_identifier_sample.csv",
        help="Path for the output CSV file (default: data/samples/output/mave_identifier_sample.csv)"
    )
    args = parser.parse_args()
    extract_score_set_data(args.input, args.output)