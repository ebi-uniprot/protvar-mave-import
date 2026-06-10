"""Produce a small, valid slice of a large MaveDB main.json for dev/test.

MaveDB's full export can be very large (v4 main.json is ~359 MB), too big to commit.
This takes the first N experimentSets up to a size budget, preserving the top-level
export wrapper (title/asOf/...), so the output is still a valid main.json the importers
can run on. The committed data/v4/main.json was produced this way.

Usage (run against the full downloaded export):
    python utils/sample_main_json.py --input main.json --output data/v4/main.json --max-mb 18
    python utils/sample_main_json.py --input main.json --output data/v4/main.json --sets 49
"""
import argparse
import json


def sample(data, max_bytes=None, max_sets=None):
    sets = data if isinstance(data, list) else data.get("experimentSets", [])
    out, total = [], 0
    for s in sets:
        if max_sets is not None and len(out) >= max_sets:
            break
        if max_bytes is not None:
            chunk = len(json.dumps(s))
            if out and total + chunk > max_bytes:
                break
            total += chunk
        out.append(s)
    # preserve the full-export wrapper shape if present
    if isinstance(data, dict):
        result = {k: (out if k == "experimentSets" else v) for k, v in data.items()}
    else:
        result = out
    return result, len(out), len(sets), total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Slice a MaveDB main.json down to a dev-sized sample.")
    parser.add_argument("--input", required=True, help="Path to the full main.json")
    parser.add_argument("--output", required=True, help="Path for the sliced output")
    parser.add_argument("--max-mb", type=float, default=18.0, help="Size budget in MB (default: 18)")
    parser.add_argument("--sets", type=int, default=None, help="Cap on number of experimentSets (overrides --max-mb)")
    args = parser.parse_args()

    with open(args.input, encoding='utf-8') as f:
        data = json.load(f)

    max_bytes = None if args.sets else int(args.max_mb * 1_000_000)
    result, kept, total_sets, size = sample(data, max_bytes=max_bytes, max_sets=args.sets)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f)

    print(f"Wrote {kept} of {total_sets} experimentSets (~{size/1e6:.1f}MB) to {args.output}")
