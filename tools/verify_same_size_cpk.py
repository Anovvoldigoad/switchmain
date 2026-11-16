"""Read-only same-size CPK verification CLI."""
import argparse
import json
import mmap
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
    # Map both archives read-only: a 360+ MiB CPK need not be copied into RAM.
    with Path(args.source).open('rb') as source_file, Path(args.output).open('rb') as output_file:
        with mmap.mmap(source_file.fileno(), 0, access=mmap.ACCESS_READ) as source:
            with mmap.mmap(output_file.fileno(), 0, access=mmap.ACCESS_READ) as output:
                proof = verify_same_size_output(source, output, args.source_sha256, args.output_sha256, args.selected)
    print(json.dumps(proof, sort_keys=True))


if __name__ == '__main__':
    main()
