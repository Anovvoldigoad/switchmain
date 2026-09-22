#!/usr/bin/env python3

from pathlib import Path
import hashlib
import struct
import sys
import os

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "overlay/source/program/p81_ougi_awake_ids.hpp"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def parse_ids(path):
    data = path.read_bytes()

    if not data:
        raise ValueError("empty file")

    if len(data) % 4:
        raise ValueError(
            f"size {len(data)} is not multiple of 4"
        )

    raw = list(
        struct.unpack(
            "<" + "I" * (len(data) // 4),
            data
        )
    )

    # UltimateStormAPI ultimately uses membership semantics.
    # Make generated representation deterministic.
    ids = sorted(set(raw))

    if not ids:
        raise ValueError("no IDs")

    return data, raw, ids


explicit = None

if len(sys.argv) >= 2:
    explicit = Path(sys.argv[1]).expanduser()

env_src = os.environ.get("P81_OUGI_SRC")

if env_src:
    explicit = Path(env_src).expanduser()


if explicit is not None:
    if not explicit.is_file():
        raise SystemExit(
            "FATAL explicit P81 Ougi source missing: "
            + str(explicit)
        )

    candidates = [explicit]

else:
    roots = [
        ROOT / "runtime_inputs",
        ROOT / "deploy",
        ROOT / "All4Compiled",

        Path.home() / "All4Compiled",
        Path.home() / "All4Compiled_alpha12",
        Path.home() / "All4Compiled_alpha14b",
        Path.home() / "nsc_switch_tool",
    ]

    seen = set()
    candidates = []

    for base in roots:
        if not base.exists():
            continue

        for p in base.rglob(
            "ougiAwakeningParam.xfbin"
        ):
            try:
                key = str(p.resolve())
            except Exception:
                key = str(p)

            if key in seen:
                continue

            seen.add(key)

            try:
                size = p.stat().st_size
            except OSError:
                continue

            if size > 0 and size % 4 == 0:
                candidates.append(p)


if not candidates:
    raise SystemExit(
        "FATAL: no ougiAwakeningParam.xfbin found.\n"
        "Set explicit source with:\n"
        "  P81_OUGI_SRC=/exact/path python3 GEN_P81_OUGI_IDS.py"
    )


# Runtime-input mod_only payload is preferred over any global/ROMFS
# representation because this is the UltimateStormAPI membership delta.
preferred = [
    p for p in candidates
    if "mod_only" in {
        x.lower()
        for x in p.parts
    }
]

pool = preferred if preferred else candidates


groups = {}

for p in pool:
    try:
        data, raw, ids = parse_ids(p)
    except Exception:
        continue

    h = sha256(data)

    groups.setdefault(
        h,
        {
            "data": data,
            "raw": raw,
            "ids": ids,
            "paths": [],
        }
    )["paths"].append(p)


if not groups:
    raise SystemExit(
        "FATAL: all candidate files invalid"
    )


if len(groups) != 1:
    print("FATAL: multiple distinct P81 Ougi payloads found:")

    for h, g in sorted(groups.items()):
        print()
        print("SHA256=" + h)
        print("IDS=" + ",".join(
            str(x) for x in g["ids"]
        ))

        for p in g["paths"]:
            print("  " + str(p))

    print()
    print(
        "Choose the intended compiled runtime input explicitly:"
    )
    print(
        "P81_OUGI_SRC=/exact/path "
        "python3 GEN_P81_OUGI_IDS.py"
    )

    raise SystemExit(1)


h, g = next(iter(groups.items()))

source = sorted(
    g["paths"],
    key=lambda p: (
        len(str(p)),
        str(p),
    )
)[0]

ids = g["ids"]

items = ",\n    ".join(
    f"{x}u"
    for x in ids
)

text = f'''#pragma once

#include <cstddef>
#include <cstdint>

/*
 * GENERATED FILE — DO NOT HAND-EDIT.
 *
 * Source:
 *   {source}
 *
 * SHA256:
 *   {h}
 *
 * Raw count:
 *   {len(g["raw"])}
 *
 * Unique membership count:
 *   {len(ids)}
 *
 * This is data, not a character-specific gameplay branch.
 */

namespace nsc {{
namespace p81_data {{

static constexpr uint32_t kOugiAwakeningIds[] = {{
    {items}
}};

static constexpr std::size_t kOugiAwakeningIdCount =
    sizeof(kOugiAwakeningIds)
    / sizeof(kOugiAwakeningIds[0]);

static constexpr const char
    kOugiAwakeningSourceSha256[] =
        "{h}";

static inline bool ContainsOugiAwakeningId(
    uint32_t id
) {{
    for (
        std::size_t i = 0;
        i < kOugiAwakeningIdCount;
        ++i
    ) {{
        if (kOugiAwakeningIds[i] == id) {{
            return true;
        }}
    }}

    return false;
}}

}} // namespace p81_data
}} // namespace nsc
'''

OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

OUT.write_text(
    text,
    encoding="utf-8"
)

print("P81_OUGI_GENERATE=PASS")
print("P81_OUGI_SOURCE=" + str(source))
print("P81_OUGI_SHA256=" + h)
print("P81_OUGI_RAW_COUNT=" + str(len(g["raw"])))
print("P81_OUGI_UNIQUE_COUNT=" + str(len(ids)))
print(
    "P81_OUGI_IDS="
    + ",".join(str(x) for x in ids)
)
print("P81_OUGI_HEADER=" + str(OUT))
