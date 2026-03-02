import os
import sys
import csv
import re
from pathlib import Path
from collections import Counter, defaultdict


# Regex for simple HGVS protein notation with optional reference sequence prefix
#   - Missense substitutions: p.Arg97Gly
#   - Nonsense (stop gained): p.Arg97Ter or p.Arg97*
#   - Synonymous (silent):    p.Arg97=
# Optional reference sequence: e.g., NP_009225.1:, ENSP..., P12345:
# Enforces correct HGVS capitalization (e.g., Arg not ARG/arg).
SIMPLE_P_REGEX = r"^(?:[^:]+:)?p\.([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2}|=|\*)$"

def is_simple_p_scheme(hgvs_pro):
    """
    Check if hgvs_pro is a simple single-residue HGVS protein variant.
    Allows optional reference sequence prefix (e.g., NP_009225.1:p.Cys27Tyr).
    """
    return bool(re.match(SIMPLE_P_REGEX, hgvs_pro))


def parse_simple_p(hgvs_pro):
    """
    Parse a simple HGVS protein variant into components.

    Returns:
      (ref_aa, pos, alt_aa)
      - ref_aa: 3-letter reference amino acid code (e.g., Arg)
      - pos:    integer residue position
      - alt_aa: 3-letter alternate amino acid, 'Ter', '*', or '='

    Optional reference sequence prefix is ignored in the output.
    If input does not match, returns (None, None, None).
    """
    m = re.match(SIMPLE_P_REGEX, hgvs_pro)
    if m:
        ref_aa, pos, alt_aa = m.groups()
        return ref_aa, int(pos), alt_aa
    return None, None, None


def detect_hgvs_scheme(value):
    """
    Return the HGVS scheme prefix if present (c., g., p., etc.),
    ignoring any optional reference sequence prefix (e.g., NP_009225.1:).

    Returns:
        - The scheme string (e.g., 'c.', 'g.', 'p.')
        - 'empty' if value is None or empty
        - 'unknown' if no HGVS scheme detected
    """
    if not value:
        return "empty"

    # Optional refseq prefix ending with a colon, then HGVS scheme
    match = re.match(r"^(?:[^:]+:)?([a-z]\.)", value)
    return match.group(1) if match else "unknown"


def import_scores_streaming(csv_folder, output_file):
    folder = Path(csv_folder)
    score_files = list(folder.glob("*.scores.csv"))

    header = ["accession", "variant_num",
              "hgvs_nt",
              #"hgvs_splice",
              "hgvs_pro",
              "is_simple_p",
              "ref_aa", "position", "alt_aa",
              "score"]

    # Summary containers
    scheme_counter = Counter()
    simple_complex_counter = Counter()

    with open(output_file, 'w', newline='', encoding='utf-8') as out_csv:
        writer = csv.DictWriter(out_csv, fieldnames=header)
        writer.writeheader()

        for file in score_files:
            with file.open('r', encoding='utf-8') as f:
                try:
                    reader = csv.DictReader(f)
                    for row in reader:
                        full_accession = row.get("accession", "")
                        match = re.match(r"(.+?)#(\d+)$", full_accession)
                        if match:
                            base_accession = match.group(1)
                            variant_num = int(match.group(2))
                        else:
                            base_accession = full_accession
                            variant_num = None

                        hgvs_nt = row.get("hgvs_nt", "")
                        #hgvs_splice = row.get("hgvs_splice", "")
                        hgvs_pro = row.get("hgvs_pro", "").strip()
                        scheme = detect_hgvs_scheme(hgvs_pro)
                        scheme_counter[scheme] += 1
                        ref_aa, pos, alt_aa = None, None, None

                        is_simple = False
                        if scheme == "p.":
                            is_simple = is_simple_p_scheme(hgvs_pro)
                            if is_simple:
                                simple_complex_counter["simple"] += 1
                                ref_aa, pos, alt_aa = parse_simple_p(hgvs_pro)
                            else:
                                simple_complex_counter["complex"] += 1

                        extracted_row = {
                            "accession": base_accession,
                            "variant_num": variant_num,
                            "hgvs_nt": hgvs_nt,
                            #"hgvs_splice": hgvs_splice,
                            "hgvs_pro": hgvs_pro,
                            "is_simple_p": is_simple,
                            "ref_aa": ref_aa if ref_aa else "NA",
                            "position": pos if pos is not None else "NA",
                            "alt_aa": alt_aa if alt_aa else "NA",
                            "score": row.get("score", "")
                        }

                        writer.writerow(extracted_row)

                except Exception as e:
                    print(f"Error processing {file.name}: {e}")

    print(f"Finished streaming {len(score_files)} files into {output_file}\n")
    # Print summaries
    total_rows = sum(scheme_counter.values())
    print(f"Total rows processed: {total_rows}")
    print("HGVS scheme breakdown in hgvs_pro:")
    for scheme, count in scheme_counter.items():
        print(f"  {scheme}: {count}")

    if "p." in scheme_counter:
        print("\n'p.' scheme breakdown:")
        for category, count in simple_complex_counter.items():
            print(f"  {category}: {count}")

# Resolve CSV input path from $PV environment variable
pv_base = os.environ.get("PV")
if pv_base is None:
    print("Error: Environment variable $PV is not set.")
    sys.exit(1)

csv_path = os.path.join(pv_base, "data", "mave", "csv")

# Check if the input folder exists before calling the function
if not os.path.exists(csv_path):
    print(f"Error: Input folder does not exist: {csv_path}")
    sys.exit(1)

# Proceed with importing
import_scores_streaming(csv_path, "mave_score.csv")

# Last run 03/10/2025; SQL import check in pg_import script
""" 
Finished streaming 2680 files into mave_score.csv

Total rows processed: 7469856
HGVS scheme breakdown in hgvs_pro:
  p.: 7025606
  unknown: 444250

'p.' scheme breakdown:
  complex: 3262005
  simple: 3763601
"""