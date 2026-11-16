"""Read-only same-size CPK verification CLI."""
import argparse
import json
from pathlib import Path
from portlib.cpk_same_size_verify import verify_same_size_output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('output')
    parser.add_argument('source_sha256')
    parser.add_argument('output_sha256')
    parser.add_argument('selected', nargs='+')
    args = parser.parse_args()
    proof = verify_same_size_output(Path(args.source).read_bytes(), Path(args.output).read_bytes(), args.source_sha256, args.output_sha256, args.selected)
    print(json.dumps(proof, sort_keys=True))


if __name__ == '__main__':
    main()
