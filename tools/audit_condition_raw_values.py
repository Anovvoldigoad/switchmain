#!/usr/bin/env python3
"""Review stock and candidate conditionprm raw176 payload bytes, without field guesses."""
import argparse
import json
from pathlib import Path
from portlib.condition_raw_audit import compare


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-manager', type=Path, required=True, help='Pinned PC 112-byte manager records')
    p.add_argument('--stock-raw', type=Path, required=True, help='Extracted stock Switch conditionprm XFBIN')
    p.add_argument('--expected-stock-sha256', required=True)
    p.add_argument('--candidate-raw', type=Path, required=True, help='Candidate mod conditionprm XFBIN')
    p.add_argument('--expected-candidate-sha256', required=True)
    p.add_argument('--output', type=Path, required=True, help='New report directory')
    a = p.parse_args()
    report = compare(a.pc_manager.read_bytes(), a.stock_raw.read_bytes(),
                     a.expected_stock_sha256, a.candidate_raw.read_bytes(),
                     a.expected_candidate_sha256)
    # No directory is created if a hash, source format, ordinal, or count fails.
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output/'condition_raw_value_audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Raw condition byte audit complete; source provenance/effect semantics/gameplay unverified.')


if __name__ == '__main__':
    main()
