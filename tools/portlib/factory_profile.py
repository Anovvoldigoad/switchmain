"""Strict PC specialCondParam -> pinned Switch class-selector profile.

Only the class-selector part of SpecialConditionParam is implemented here.
This does not implement its PC global resets, movesets, assets, or full API.
"""
import hashlib
import json
import struct
from pathlib import Path

MAGIC = b'NSC_FACTORY_V1\0\0'
CAPACITY = 1024
PROFILE_SIZE = 64 + CAPACITY * 4
CATALOG = Path(__file__).resolve().parents[2] / 'profiles/factory_catalog_v170.json'


def catalog():
    rows = json.loads(CATALOG.read_text())['entries']
    return {row['name']: row for row in rows}


def seal(block):
    block = bytearray(block)
    if len(block) != PROFILE_SIZE:
        raise ValueError('Wrong profile size')
    block[24:56] = hashlib.sha256(block[:24] + block[56:]).digest()
    return bytes(block)


def encode(entries):
    rows = sorted(entries.items())
    supported = {row['selector'] for row in catalog().values() if row['supported']}
    if len(rows) > CAPACITY:
        raise ValueError('Too many factory mappings')
    block = bytearray(PROFILE_SIZE)
    block[:16] = MAGIC
    struct.pack_into('<II', block, 16, 1, len(rows))
    for i, (owner, selector) in enumerate(rows):
        if type(owner) is not int or not 0 <= owner < CAPACITY:
            raise ValueError(f'Owner {owner!r} outside verified loader capacity')
        if type(selector) is not int or selector not in supported:
            raise ValueError(f'Unverified Switch class selector {selector!r}')
        struct.pack_into('<HH', block, 64 + 4*i, owner, selector)
    return seal(block)


def decode(block):
    if len(block) != PROFILE_SIZE or block[:16] != MAGIC:
        raise ValueError('Wrong factory profile size/magic')
    version, count = struct.unpack_from('<II', block, 16)
    if version != 1 or count > CAPACITY or any(block[56:64]):
        raise ValueError('Invalid factory profile header')
    if seal(block) != block:
        raise ValueError('Factory profile checksum mismatch')
    rows = [struct.unpack_from('<HH', block, 64 + 4*i) for i in range(count)]
    if any(rows[i][0] >= rows[i+1][0] for i in range(len(rows)-1)):
        raise ValueError('Owner IDs must be strictly increasing')
    if any(block[64+4*count:]):
        raise ValueError('Nonzero unused profile data')
    entries = dict(rows)
    if encode(entries) != block:
        raise ValueError('Noncanonical factory profile')
    return entries


def compile_records(inputs, owner_map=None):
    """Inputs are ordered (label, raw bytes) pairs. PC last-owner-wins semantics."""
    names = catalog()
    owner_map = {} if owner_map is None else owner_map
    for old, new in owner_map.items():
        if type(old) is not int or not 0 <= old <= 65535 or type(new) is not int or not 0 <= new < CAPACITY:
            raise ValueError('Invalid explicit owner mapping')
    entries, sources = {}, []
    for label, raw in inputs:
        if raw.startswith(b'NUCC') or len(raw) % 32:
            raise ValueError(f'{label}: expected raw 32-byte PC specialCondParam records')
        for off in range(0, len(raw), 32):
            try:
                name = raw[off:off+24].split(b'\0', 1)[0].decode('ascii').upper()
            except UnicodeDecodeError as e:
                raise ValueError(f'{label}:{off}: non-ASCII condition name') from e
            if not name.startswith('COND_'):
                name = 'COND_' + name
            row = names.get(name)
            if not row:
                raise ValueError(f'{label}:{off}: unknown PC condition {name}')
            if not row['supported']:
                raise ValueError(f'{label}:{off}: {name} does not match Switch charcode {row["switch_charcode"]}; mapping is unverified')
            old = struct.unpack_from('<H', raw, off+24)[0]
            owner = owner_map.get(old, old)
            if not 0 <= owner < CAPACITY:
                raise ValueError(f'{label}:{off}: owner {owner} outside verified loader capacity')
            sources.append({'file': str(label), 'record': off//32, 'pc_owner': old,
                            'switch_owner': owner, 'name': name, 'selector': row['selector'],
                            'replaces_previous_mapping': owner in entries})
            entries[owner] = row['selector']
    return encode(entries), sources
