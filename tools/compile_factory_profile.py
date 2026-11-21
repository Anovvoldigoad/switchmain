#!/usr/bin/env python3
"""Compile audited class-selector parameters; NOT a full mod converter/release."""
import argparse
import hashlib
import json
from pathlib import Path
from portlib.factory_profile import compile_records
from portlib.nso_profile import configure


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--param', type=Path, action='append', default=[], help='Raw PC specialCondParam; repeat in mod load order')
    p.add_argument('--param-sha256', action='append', default=[],
                   help='Required SHA256 for each --param in identical order; omit only for legacy unauthenticated use')
    p.add_argument('--owner-map', type=Path, help='Explicit JSON object mapping PC owner IDs to final Switch IDs')
    p.add_argument('--conflicts', choices=('last', 'reject'), default='last',
                   help='Reject duplicate final Switch owners, including remap collisions')
    p.add_argument('--output', type=Path, required=True, help='New output directory; never an install folder')
    p.add_argument('--module', type=Path, help='Optional built subsdk9 to configure')
    p.add_argument('--expected-module-sha256', help='Exact SHA256 of the audited input module')
    a = p.parse_args()
    if bool(a.module) != bool(a.expected_module_sha256):
        p.error('--module and --expected-module-sha256 must be supplied together')
    owner_map = {}
    if a.owner_map:
        raw_map = json.loads(a.owner_map.read_text())
        if not isinstance(raw_map, dict):
            p.error('--owner-map must contain a JSON object')
        for k, v in raw_map.items():
            if str(int(k)) != k:
                p.error('Owner-map keys must be canonical decimal IDs')
            owner_map[int(k)] = v
    if a.param_sha256 and len(a.param_sha256) != len(a.param):
        p.error('Supply exactly one --param-sha256 for each --param')
    inputs, provenance = [], []
    for index, path in enumerate(a.param):
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if a.param_sha256 and (len(a.param_sha256[index]) != 64 or
                               digest != a.param_sha256[index].lower()):
            p.error(f'--param-sha256 mismatch for input {index}')
        inputs.append((str(path), raw))
        provenance.append({'source_index': index, 'sha256': digest,
                           'authenticated': bool(a.param_sha256)})
    profile, records = compile_records(inputs, owner_map, conflicts=a.conflicts)
    result, report = None, {'records': records, 'sources': provenance, 'conflicts': a.conflicts, 'gameplay_verified': False, 'full_moddingapi': False}
    if a.module:
        result, module_report = configure(a.module.read_bytes(), profile, a.expected_module_sha256)
        report['module'] = module_report
    # Validate all inputs before creating any outputs. Refuse overwrites.
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output/'factory.profile').write_bytes(profile)
    (a.output/'factory_profile_report.json').write_text(json.dumps(report, indent=2)+'\n')
    if result is not None:
        (a.output/'subsdk9.factory_component_NOT_GAMEPLAY_RELEASE').write_bytes(result)
    print(f'Compiled {len(records)} records. Factory component only; gameplay not verified.')


if __name__ == '__main__':
    main()
