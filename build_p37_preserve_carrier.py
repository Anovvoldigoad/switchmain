#!/usr/bin/env python3
"""P37: build a Tobi carrier variant preserving original stored encoding.

Does not touch either original CPK or an installed RomFS. This is an offline
engineering candidate, not a validated gameplay fix.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from audit_p35_carrier import HEAD, list_archive
from cpk_p37_compat import (
    get_cpk_sorted, set_cpk_sorted, staged_raw_storage,
    assert_original_stored_unchanged,
)

EXPECTED_STOCK_SHA256 = "a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27"
BATTLE_GLOBALS = (
    "data/spc/conditionprm.bin.xfbin",
    "data/spc/damageprm.bin.xfbin",
    "data/spc/privateCamera.bin.xfbin",
)
EXPECTED_STOCK_COUNT = 728
EXPECTED_CARRIER_COUNT = 93


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_checked(argv: list[str]) -> None:
    subprocess.run(argv, check=True, timeout=1800)


def parse_template_alignment(list_output: str) -> int:
    """Read the carrier CPK alignment from FastCPK, not pack's 0x800 default."""
    match = HEAD.search(list_output)
    if match is None:
        raise ValueError("Carrier CPK alignment missing from listing")
    alignment = int(match.group(3), 0)
    if not (0 < alignment <= 65535):
        raise ValueError("Invalid CPK template alignment")
    return alignment


def read_template_alignment(carrier: Path, fastcpk: Path) -> int:
    listing = subprocess.run(
        [str(fastcpk), "--list", str(carrier)],
        capture_output=True, text=True, timeout=180, check=True
    )
    return parse_template_alignment(listing.stdout)


def inside(path: Path, directory: Path) -> bool:
    return path == directory or directory in path.parents


def preflight(stock: Path, carrier: Path, output: Path, fastcpk: Path,
              rebuilder: Path, skip_stock_pin: bool) -> tuple[dict, dict, str, str]:
    stock, carrier, output = stock.resolve(), carrier.resolve(), output.resolve()
    if stock == carrier:
        raise ValueError("Stock and carrier must be two different CPK files")
    for file in (stock, carrier):
        if not file.is_file() or file.is_symlink():
            raise ValueError("Missing, invalid or symlink input CPK: " + str(file))
        with file.open("rb") as handle:
            if handle.read(4) != b"CPK ":
                raise ValueError("Invalid CPK header: " + str(file))
    if output.exists():
        raise ValueError("Output folder already exists; choose a new path")
    if inside(output, stock.parent) or inside(output, carrier.parent):
        raise ValueError("Output must be outside both source CPK directories")
    if not output.parent.is_dir():
        raise ValueError("Create output parent first: " + str(output.parent))
    for binary in (fastcpk, rebuilder):
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise ValueError("Required FastCPK executable missing: " + str(binary))
    stock_hash, carrier_hash = sha256(stock), sha256(carrier)
    if not skip_stock_pin and stock_hash != EXPECTED_STOCK_SHA256:
        raise ValueError(
            "Stock CPK SHA256 does not match previously verified patch/170 source: " + stock_hash
        )
    stock_index = list_archive(stock, fastcpk)
    carrier_index = list_archive(carrier, fastcpk)
    if len(stock_index) != EXPECTED_STOCK_COUNT or len(carrier_index) != EXPECTED_CARRIER_COUNT:
        raise ValueError("Unexpected CPK entry counts; refusing to guess content layout")
    for path in BATTLE_GLOBALS:
        if path not in stock_index or path not in carrier_index:
            raise ValueError("Missing battle-global entry in one input archive: " + path)
    return stock_index, carrier_index, stock_hash, carrier_hash


def hashes(root: Path, names: list[str]) -> dict[str, str]:
    result = {}
    for name in names:
        target = root.joinpath(*name.split("/"))
        if target.is_symlink() or not target.is_file() or not inside(target.resolve(), root.resolve()):
            raise ValueError("Missing/unsafe extracted entry: " + name)
        result[name] = sha256(target)
    return result


def select_stock_global_replacements(
    carrier_decoded: dict[str, str], stock_decoded: dict[str, str]
) -> list[str]:
    """Fail closed if a stock restore would have no decoded-content effect."""
    missing = set(BATTLE_GLOBALS) - set(carrier_decoded) | (set(BATTLE_GLOBALS) - set(stock_decoded))
    if missing:
        raise ValueError("Global decoded hashes missing: " + ", ".join(sorted(missing)))
    selected = [path for path in BATTLE_GLOBALS if carrier_decoded[path] != stock_decoded[path]]
    if not selected:
        raise ValueError("All three decoded globals already equal stock: no P36 candidate warranted")
    return selected


def validate_repack(
    original_ids: dict[str, int],
    built_ids: dict[str, int],
    original_hashes: dict[str, str],
    rebuilt_hashes: dict[str, str],
    stock_hashes: dict[str, str],
) -> dict:
    """Every path/ID must survive; 90+ other decoded entries remain identical."""
    if original_ids != built_ids or list(original_ids) != list(built_ids):
        raise ValueError("CPK template path order or numeric IDs changed")
    if set(original_hashes) != set(rebuilt_hashes):
        raise ValueError("Decoded carrier file set changed")
    modified = []
    for name in original_hashes:
        if name in BATTLE_GLOBALS:
            if rebuilt_hashes[name] != stock_hashes[name]:
                raise ValueError("Rebuilt battle global differs from decoded stock: " + name)
            if original_hashes[name] != rebuilt_hashes[name]:
                modified.append(name)
        elif original_hashes[name] != rebuilt_hashes[name]:
            raise ValueError("Unrelated decoded payload changed: " + name)
    if not modified:
        raise ValueError("No decoded battle global changed")
    return {
        "modified_entries": modified,
        "unchanged_entries": len(original_hashes) - len(modified),
        "all_paths_ids_and_decoded_contents_checked": True,
    }


def build(args: argparse.Namespace) -> dict:
    stock = args.stock.expanduser().resolve()
    carrier = args.carrier.expanduser().resolve()
    out = args.output.expanduser().resolve()
    fastcpk = args.fastcpk.expanduser().resolve()
    rebuilder = args.rebuilder.expanduser().resolve()
    stock_idx, carrier_idx, original_stock_sha, original_carrier_sha = preflight(
        stock, carrier, out, fastcpk, rebuilder, args.skip_stock_pin
    )
    template_alignment = read_template_alignment(carrier, fastcpk)
    template_sorted = get_cpk_sorted(carrier)
    # A new output folder is never an installed mod. Creating it is the only
    # persistent mutation until the fully verified candidate is copied here.
    out.mkdir(exist_ok=False)
    verified_candidate = out / "Tobi_Switch_P37_PRESERVED_ENCODING_UNTESTED.cpk"
    report_path = out / "P37_BUILD_REPORT.json"

    with tempfile.TemporaryDirectory(prefix="p37_", dir=out) as scratch:
        work = Path(scratch)
        candidate = work / "candidate_unverified.cpk"
        decoded_stock = work / "stock"
        decoded_carrier = work / "carrier"
        staged = work / "staging"
        decoded_built = work / "verify"
        for directory in (decoded_stock, decoded_carrier, staged, decoded_built):
            directory.mkdir()
        run_checked([str(fastcpk), "--game", "cc2-storm", "-o", str(decoded_stock), str(stock)])
        run_checked([str(fastcpk), "--game", "cc2-storm", "-o", str(decoded_carrier), str(carrier)])
        original_hashes = hashes(decoded_carrier, list(carrier_idx))
        stock_hashes = hashes(decoded_stock, list(BATTLE_GLOBALS))
        selected = select_stock_global_replacements(original_hashes, stock_hashes)
        for name in BATTLE_GLOBALS:
            for root in (decoded_stock, decoded_carrier):
                with root.joinpath(*name.split("/")).open("rb") as handle:
                    if handle.read(4) != b"NUCC":
                        raise ValueError("Expected decoded NUCC XFBIN, got unknown payload: " + name)
        # Preserve the full carrier entry set; replacing or deleting paths in
        # the template risks changing the engine's TOC/ID lookup behavior.
        shutil.copytree(decoded_carrier / "data", staged / "data")
        for name in selected:
            destination = staged.joinpath(*name.split("/"))
            shutil.copyfile(decoded_stock.joinpath(*name.split("/")), destination)
        stage_hashes = hashes(staged, list(carrier_idx))
        if set(stage_hashes) != set(original_hashes):
            raise ValueError("Stage has unexpected path set")
        for name in original_hashes:
            desired = stock_hashes[name] if name in BATTLE_GLOBALS else original_hashes[name]
            if stage_hashes[name] != desired:
                raise ValueError("Unexpected stage payload: " + name)

        # P36 booted unsuccessfully after changing packaging of all 93 entries:
        # it CRILAYLA-compressed 81 and encrypted 93. P37 preserves the
        # original stored bytes of ALL nonselected resources, including
        # the single originally CC2-encrypted resource. Changed globals
        # are stored as plaintext decoded stock NUCC without new compression.
        staged_raw_storage(carrier, carrier_idx, staged, set(selected))

        # FastCPK template mode preserves paths, ordering and numeric IDs.
        # Deliberately OMIT --crilayla and --encrypt-storm. Original
        # stored payloads are already in the format expected by the loader.
        run_checked([
            str(rebuilder), "pack", str(staged / "data"),
            "--output", str(candidate), "--template", str(carrier),
            "--threads", "2", "--align", str(template_alignment)
        ])
        # Current FastCPK pack() always writes Sorted=1 for templates even
        # when the original unsorted carrier has Sorted=0. Correct only
        # the disposable candidate's header before any verification.
        packed_sorted_before, packed_sorted_after = set_cpk_sorted(candidate, template_sorted)
        built_idx = list_archive(candidate, fastcpk)
        unchanged_stored = assert_original_stored_unchanged(
            carrier, carrier_idx, candidate, built_idx, set(selected)
        )
        run_checked([str(fastcpk), "--game", "cc2-storm", "-o", str(decoded_built), str(candidate)])
        built_hashes = hashes(decoded_built, list(built_idx))
        integrity = validate_repack(
            {k: v["id"] for k, v in carrier_idx.items()},
            {k: v["id"] for k, v in built_idx.items()},
            original_hashes, built_hashes, stock_hashes
        )
        # Never expose a failed/unverified CPK as a final candidate.
        candidate_digest = sha256(candidate)
        if sha256(stock) != original_stock_sha or sha256(carrier) != original_carrier_sha:
            raise ValueError("Source input hash changed during operation: investigate filesystem")
        os.replace(candidate, verified_candidate)
        if sha256(verified_candidate) != candidate_digest:
            verified_candidate.unlink(missing_ok=True)
            raise ValueError("Verified CPK changed while moving to the output directory")
    # Check both inputs still match the initial SHA256 after all operations.
    if sha256(stock) != original_stock_sha or sha256(carrier) != original_carrier_sha:
        raise ValueError("Source input hash changed during operation: investigate filesystem")
    report = {
        "status": "BUILT_AND_VERIFIED_OFFLINE_NOT_GAMEPLAY_TESTED",
        "stock_source_sha256": original_stock_sha,
        "stock_pin_override": bool(args.skip_stock_pin),
        "carrier_source_sha256": original_carrier_sha,
        "candidate_sha256": sha256(verified_candidate),
        "candidate_path": str(verified_candidate),
        "carrier_entry_count": len(carrier_idx),
        "carrier_sorted_original": template_sorted,
        "carrier_sorted_packer_generated": packed_sorted_before,
        "carrier_sorted_restored": packed_sorted_after,
        "stored_payloads_identical_to_original_count": unchanged_stored,
        "per_entry_payload_compression": "preserve_original_stored_bytes; no_new_compression",
        "per_entry_payload_encryption": "preserve_original_stored_bytes; no_new_encryption",
        "carrier_template_alignment": template_alignment,
        "stock_entry_count": len(stock_idx),
        "changed_decoded_globals": integrity["modified_entries"],
        "unchanged_decoded_entries": integrity["unchanged_entries"],
        "same_93_paths_and_numeric_ids": integrity["all_paths_ids_and_decoded_contents_checked"],
        "warning": (
            "P37 preserves all unchanged entries in their exact original stored encoding "
            "and restores the original carrier Sorted metadata. The model/actor "
            "render failure is not yet proven fixed, and mounting still requires "
            "the existing subsdk9 loader."
        ),
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock", type=Path, required=True)
    parser.add_argument("--carrier", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="new output folder outside RomFS")
    parser.add_argument("--fastcpk", type=Path, default=Path.home()/".cache/naruto-fastcpk/target/release/fastcpk")
    parser.add_argument("--rebuilder", type=Path, default=Path.home()/".cache/naruto-fastcpk/target/release/fastcpk-rebuild")
    parser.add_argument("--skip-stock-pin", action="store_true",
                        help="research builds only; disables Switch patch/170 SHA256 provenance guard")
    args = parser.parse_args()
    try:
        report = build(args)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(2, "P37 ABORTED (no source CPK modified): " + str(error) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
