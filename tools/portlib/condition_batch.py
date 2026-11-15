"""Multi-CPK component batch with explicit global condition owner.

Cannot establish native archive precedence, CRI async completion, or gameplay.
Rejects any inter-archive path overlap until native precedence is proven.
"""
import hashlib
import json
import re
import tempfile
from pathlib import Path

from . import condition_bundle, condition_profile, cpk_events, cpk_overlap, cpk_profile, nso_profile

HASH = re.compile(r'[0-9a-f]{64}\Z')
ENTRY = condition_bundle.ENTRY


def sha(b):
    return hashlib.sha256(b).hexdigest()


def validate_manifest(manifest):
    if not isinstance(manifest, dict) or set(manifest) != {'condition_owner', 'archives'}:
        raise ValueError('Expected condition_owner and archives')
    archives = manifest['archives']
    if not isinstance(archives, list) or not 1 <= len(archives) <= cpk_profile.CAPACITY:
        raise ValueError('Expected 1..32 archive definitions')
    rows, sources = [], []
    for item in archives:
        if not isinstance(item, dict) or set(item) != {'source','sha256','path','priority','pc_api_prms'}:
            raise ValueError('Archive requires source, sha256, path, priority, pc_api_prms')
        if type(item['source']) is not str or not item['source']:
            raise ValueError('Missing source path')
        if type(item['sha256']) is not str or not HASH.fullmatch(item['sha256']):
            raise ValueError('Explicit lowercase SHA256 required')
        selected = item['pc_api_prms']
        if not isinstance(selected, list) or any(type(p) is not str for p in selected) or len(set(selected))!=len(selected):
            raise ValueError('Expected list of unique PC API PRM paths')
        for p in selected:
            cpk_events.canonical(p)
            if p == ENTRY:
                raise ValueError('Condition companion cannot be marked as API event PRM')
        rows.append({'path':item['path'],'priority':item['priority']})
        sources.append({k:item[k] for k in ('source','sha256','path','priority')})
    cpk_profile.validate_rows(rows)
    if type(manifest['condition_owner']) is not str or manifest['condition_owner'] not in [r['path'] for r in rows]:
        raise ValueError('Explicit condition_owner must identify one runtime path')
    return archives, rows, sources


def build(manifest, manager, manager_sha256, output, module=None, module_sha256=None):
    """Hash-check all inputs before publishing an atomic, review-only component batch."""
    if type(manager_sha256) is not str or not HASH.fullmatch(manager_sha256) or sha(manager)!=manager_sha256:
        raise ValueError('PC manager hash mismatch')
    if (module is None)!=(module_sha256 is None):
        raise ValueError('Module and expected hash must be supplied together')
    if module is not None and (type(module_sha256) is not str or
                               not HASH.fullmatch(module_sha256) or sha(module)!=module_sha256):
        raise ValueError('Module hash mismatch')
    archives, rows, sources=validate_manifest(manifest)
    profile, descriptor_report=condition_profile.compile_table(manager)
    overlap=cpk_overlap.inspect({'archives':sources})
    if overlap['overlapping_paths']:
        raise ValueError('CPK entry collision; native lookup precedence unverified')
    output=Path(output)
    if output.exists() or not output.parent.is_dir():
        raise ValueError('Output must be a new directory under an existing parent')
    final_module=module
    reports=[];module_reports=[]
    with tempfile.TemporaryDirectory(prefix='.nsc-batch-',dir=output.parent) as tmp:
        staging=Path(tmp)
        for item in archives:
            path=Path(item['source'])
            if not path.is_file() or path.is_symlink():
                raise ValueError('Missing or symlinked archive source')
            original=path.read_bytes()
            if sha(original)!=item['sha256']:
                raise ValueError('Source archive changed after overlap audit')
            table=cpk_events.entries(original)
            owner=item['path']==manifest['condition_owner']
            if (ENTRY in table)!=owner:
                raise ValueError('Condition companion must occur in owner archive only')
            registration=cpk_profile.encode([{'path':item['path'],'priority':item['priority']}])
            if owner:
                converted,compiled,_,details=condition_bundle.compile_bundle(
                    manager,original,item['sha256'],item['path'],item['priority'],item['pc_api_prms'])
                if compiled!=profile:
                    raise ValueError('Global condition profile mismatch')
            elif item['pc_api_prms']:
                converted, events=cpk_events.mark(original,item['pc_api_prms'])
                details={'events':events,'has_condition_companion':False}
            else:
                converted=original
                details={'events':{'selected_prms':[],'conversion_requested':False},
                         'has_condition_companion':False}
            if final_module is not None:
                final_module,mr=condition_bundle.configure_module(
                    final_module,sha(final_module),profile,registration)
                module_reports.append(mr)
            relative=Path('component_data') / item['path'][len(cpk_profile.PREFIX):]
            dest=staging/relative
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(converted)
            reports.append({'runtime_path':item['path'],'priority':item['priority'],
                            'relative_path':relative.as_posix(),'condition_owner':owner,
                            'source_sha256':sha(original),'output_sha256':sha(converted),
                            'selected_pc_api_prms':item['pc_api_prms'],
                            'component':details})
        registration=cpk_profile.encode(rows)
        if final_module is not None:
            data=nso_profile.segments(final_module)[2][1]
            registration=condition_bundle._embedded_profile(
                data,cpk_profile.MAGIC,cpk_profile.PROFILE_SIZE,cpk_profile.decode)
            cond=condition_bundle._embedded_profile(
                data,condition_profile.MAGIC,condition_profile.PROFILE_SIZE,condition_profile.decode)
            if cond!=profile:
                raise ValueError('Module condition profile differs from requested profile')
            actual=cpk_profile.decode(registration)
            if any(r not in actual for r in rows):
                raise ValueError('Effective module CPK rows missing')
            (staging/'subsdk9.COMPONENT_NOT_GAMEPLAY_RELEASE').write_bytes(final_module)
        (staging/'condition.profile').write_bytes(profile)
        (staging/'cpk.profile').write_bytes(registration)
        result={'status':'COMPONENT_ONLY_NOT_GAMEPLAY_RELEASE',
                'manager_sha256':sha(manager),
                'condition_descriptor_report':descriptor_report,
                'condition_owner':manifest['condition_owner'],
                'archive_count':len(rows),'archives':reports,
                'effective_cpk_entries':len(cpk_profile.decode(registration)),
                'effective_cpk_profile_sha256':sha(registration),
                'module_sha256':sha(final_module) if final_module is not None else None,
                'module_reports':module_reports,
                'inter_archive_paths_disjoint':True,
                'source_origin_independently_authenticated':False,
                'raw_switch_stock_values_verified':False,
                'runtime_archive_winner_verified':False,
                'async_archive_completion_verified':False,
                'actor_lifecycle_verified':False,
                'gameplay_verified':False,'full_moddingapi':False,
                'ready_for_gameplay_test':False}
        (staging/'batch_report.json').write_text(json.dumps(result,indent=2)+'\n')
        staging.rename(output)
    return result
