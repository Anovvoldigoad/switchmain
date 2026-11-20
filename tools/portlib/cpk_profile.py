"""Explicit mod CPK registration profile, standard-library only for Android."""
import hashlib
import re
import struct
from .nso_profile import configure_payload
MAGIC=b'NSC_CPK_LIST_V1\0'
CAPACITY=32
PATH_SIZE=192
RECORD_SIZE=208
PROFILE_SIZE=64+CAPACITY*RECORD_SIZE
PREFIX='sim:data/moddingapi/'


def validate_path(path):
    if not isinstance(path,str) or not path.startswith(PREFIX):
        raise ValueError('CPK path must start with '+PREFIX)
    try:raw=path.encode('ascii')
    except UnicodeEncodeError:raise ValueError('CPK paths must use ASCII') from None
    if len(raw)>=PATH_SIZE:raise ValueError('CPK path too long')
    parts=path[len(PREFIX):].split('/')
    if any(not p or p in ('.','..') or p!=p.strip(' ') or
           not re.fullmatch(r'[A-Za-z0-9_. -]+',p) for p in parts):
        raise ValueError('Invalid CPK path component')
    if len(parts[-1])<=4 or not parts[-1].lower().endswith('.cpk'):
        raise ValueError('Expected a named .cpk file')
    return raw


def validate_rows(rows):
    if not isinstance(rows,list) or len(rows)>CAPACITY:raise ValueError('Expected at most 32 CPK entries')
    paths=set();priorities=set()
    for row in rows:
        if not isinstance(row,dict) or set(row)!={'path','priority'}:
            raise ValueError('Each CPK entry requires only path and priority')
        raw=validate_path(row['path']);priority=row['priority']
        if type(priority) is not int or not 0<=priority<=0x7fffffff:
            raise ValueError('Priority must be an integer from 0 to INT32_MAX')
        if raw.lower() in paths:raise ValueError('Duplicate CPK path')
        if priority in priorities:raise ValueError('Duplicate priority; assign explicit distinct priorities')
        paths.add(raw.lower());priorities.add(priority)


def encode(rows):
    validate_rows(rows);data=bytearray(PROFILE_SIZE);data[:16]=MAGIC
    struct.pack_into('<II',data,16,1,len(rows))
    for i,row in enumerate(rows):
        off=64+i*RECORD_SIZE;struct.pack_into('<I',data,off,row['priority'])
        path=validate_path(row['path']);data[off+16:off+16+len(path)]=path
    data[24:56]=hashlib.sha256(data[:24]+data[56:]).digest()
    return bytes(data)


def decode(data):
    if len(data)!=PROFILE_SIZE or data[:16]!=MAGIC:raise ValueError('CPK profile size/magic')
    version,count=struct.unpack_from('<II',data,16)
    if version!=1 or count>CAPACITY or any(data[56:64]):raise ValueError('CPK profile header')
    if hashlib.sha256(data[:24]+data[56:]).digest()!=data[24:56]:raise ValueError('CPK profile digest')
    rows=[]
    for i in range(count):
        off=64+i*RECORD_SIZE
        if any(data[off+4:off+16]):raise ValueError('CPK profile reserved bytes')
        path=data[off+16:off+RECORD_SIZE]
        if b'\0' not in path:raise ValueError('Unterminated CPK path')
        raw,padding=path.split(b'\0',1)
        if any(padding):raise ValueError('CPK path padding')
        try:name=raw.decode('ascii')
        except UnicodeDecodeError:raise ValueError('Non-ASCII CPK path') from None
        rows.append({'path':name,'priority':struct.unpack_from('<I',data,off)[0]})
    if any(data[64+count*RECORD_SIZE:]):raise ValueError('CPK profile tail padding')
    validate_rows(rows);return rows


def configure(nso, profile, expected_sha256):
    result,report=configure_payload(nso,profile,expected_sha256,MAGIC,PROFILE_SIZE,decode)
    report['cpk_entries']=len(decode(profile))
    return result,report
