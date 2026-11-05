"""Byte-authenticated public NSC Mod Manager 2.1.2.1 PC manager512.

Source is TheLeonX/NSC-ModManager commit 276116ebf5ba398a867793cb02ee6c33c0927645,
path ModdingAPIFiles/moddingapi/param/NSC/conditionprmManager.xfbin.
The pinned public Git blob SHA-1 and independent payload SHA-256 prove binary
identity for this PC template only; they do NOT authenticate modded manager517
or original Switch CPK/game data.
"""
import hashlib
from .condition_profile import PC_RECORD_SIZE,PC_BASELINE_SHA256,NATIVE_COUNT

SOURCE_REPO="TheLeonX/NSC-ModManager"
SOURCE_COMMIT="276116ebf5ba398a867793cb02ee6c33c0927645"
SOURCE_PATH="ModdingAPIFiles/moddingapi/param/NSC/conditionprmManager.xfbin"
SOURCE_GIT_BLOB_SHA1="0e7133223f10eb2dbbb39d2166fdca9352e84c3e"
SOURCE_BYTES=NATIVE_COUNT*PC_RECORD_SIZE

def inspect(raw):
    if not isinstance(raw,bytes) or len(raw)!=SOURCE_BYTES:
        raise ValueError("Expected public PC 512x112 byte original template")
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=PC_BASELINE_SHA256:
        raise ValueError("Public manager512 SHA256 differs")
    git_obj=b"blob "+str(len(raw)).encode("ascii")+b"\x00"+raw
    git_sha1=hashlib.sha1(git_obj).hexdigest()
    if git_sha1!=SOURCE_GIT_BLOB_SHA1:
        raise ValueError("Original NSC Mod Manager Git object SHA-1 differs")
    return {
        "status":"PUBLIC_NSC_MOD_MANAGER_PC_512_TEMPLATE_BYTES_AUTHENTICATED",
        "original_repo":SOURCE_REPO,"source_commit":SOURCE_COMMIT,
        "source_path":SOURCE_PATH,"original_git_blob_sha1":git_sha1,
        "raw_sha256":digest,"size":len(raw),"rows_112_bytes":NATIVE_COUNT,
        "merged_PC_517_authenticated":False,
        "stock_Switch_v170_CPK_authenticated":False,
        "native_Switch_factory_or_CRI_ABI_verified":False,
        "full_moddingapi":False,"emulator_tested":False,
        "ready_for_gameplay_test":False
    }
