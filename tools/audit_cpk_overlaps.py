#!/usr/bin/env python3
"""Review CPK path collisions with pinned source SHA256; no runtime winner claim."""
import argparse
import json
from pathlib import Path
from portlib.cpk_overlap import inspect


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True,
                   help='JSON {archives:[{source,path,priority,sha256}]}')
    p.add_argument('--output', type=Path, required=True, help='New directory, review report only')
    p.add_argument('--reject-unresolved', action='store_true',
                   help='Fail without writing if case/content conflicts are unresolved')
    a = p.parse_args()
    result = inspect(json.loads(a.manifest.read_text()))
    if a.reject_unresolved and result['divergent_or_unresolved_paths']:
        p.error('Unresolved CPK path/content collisions; report not published')
    # Do not create output on malformed source/hash, or unresolved strict mode.
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output/'cpk_overlap_report.json').write_text(json.dumps(result, indent=2)+'\n')
    print('CPK path audit only: runtime archive precedence and async load NOT verified.')


if __name__ == '__main__':
    main()
