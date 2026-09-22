#!/usr/bin/env python3

from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent

CPP = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAIN = ROOT / "overlay/source/program/main.cpp"

P65_PREP = ROOT / "prepare_exlaunch_p65a.sh"
P67_PREP = ROOT / "prepare_exlaunch_p67a.sh"

P65_WF = ROOT / ".github/workflows/build-subsdk9-p65a.yml"
P66_WF = ROOT / ".github/workflows/build-subsdk9-p66a.yml"
P67_WF = ROOT / ".github/workflows/build-subsdk9-p67a.yml"


def die(s):
    raise SystemExit("FATAL: " + s)


def replace_once(s, old, new, label):
    if new in s:
        return s

    n = s.count(old)

    if n != 1:
        die(f"{label}: anchor count={n}")

    return s.replace(old, new, 1)


def backup():
    d = ROOT / "P67A_BACKUP_PREVIOUS"

    if d.exists():
        return

    d.mkdir()

    for p in (
        CPP,
        HPP,
        MAIN,
        P65_PREP,
        P65_WF,
        P66_WF,
    ):
        if p.is_file():
            shutil.copy2(p, d / p.name)

    print("P67_BACKUP=PASS")


def patch_cpp():
    s = CPP.read_text(encoding="utf-8")

    # ----------------------------------------------------------
    # 1. Add exact active-player caller of 0x7ABE9C.
    # ----------------------------------------------------------

    anchor = (
        "constexpr ptrdiff_t "
        "kUjSemanticCaller2ReturnOffset = 0xC78D4;\n"
    )

    add = anchor + (
        "// P67A: direct active-player input caller of "
        "the same selector1 consumer.\n"
        "// main+0x7F4728 MOV X0,X19\n"
        "// main+0x7F472C BL  main+0x7ABE9C\n"
        "// return LR = main+0x7F4730\n"
        "constexpr ptrdiff_t "
        "kUjSemanticActivePlayerReturnOffset = 0x7F4730;\n"
    )

    s = replace_once(
        s,
        anchor,
        add,
        "P67 active caller constant"
    )

    # ----------------------------------------------------------
    # 2. Extend P64 exact semantic caller policy.
    # ----------------------------------------------------------

    if (
        "caller_off == "
        "kUjSemanticActivePlayerReturnOffset"
        not in s
    ):
        old = (
            "caller_off == "
            "kUjSemanticCaller2ReturnOffset;"
        )

        new = (
            "caller_off == "
            "kUjSemanticCaller2ReturnOffset ||\n"
            "                                  "
            "caller_off == "
            "kUjSemanticActivePlayerReturnOffset;"
        )

        if s.count(old) != 1:
            die(
                "P64 semantic exact_router tail "
                "not uniquely found"
            )

        s = s.replace(
            old,
            new,
            1
        )

    # ----------------------------------------------------------
    # 3. P67 guarded installer.
    #
    # This validates that the active input function really calls
    # 0x7ABE9C before enabling the semantic bridge.
    # ----------------------------------------------------------

    marker = (
        "bool InstallP67ActiveSelector1ConsumerBridge() {"
    )

    insert_anchor = (
        "bool InstallP64SemanticUjBridge() {"
    )

    if marker not in s:
        if insert_anchor not in s:
            die("P64 semantic installer anchor missing")

        block = r'''
bool InstallP67ActiveSelector1ConsumerBridge() {
    // Active player input consumer:
    //
    // 0x7F4728  MOV X0,X19
    // 0x7F472C  BL  0x7ABE9C
    // 0x7F4730  CBNZ W0,0x7F44F8
    // 0x7F4734  B 0x7F4520
    //
    // 0x7ABE9C is independently proven to query native
    // control selector1 through 0x7C6280.
    static constexpr uint32_t kActiveExpected[] = {
        0xAA1303E0,
        0x97FEDDDC,
        0x35FFEE40,
        0x17FFFF7B,
    };

    if (!MatchWords(0x7F4728, kActiveExpected)) {
        LogFingerprintFail(
            "P67_ACTIVE_SELECTOR1_CONSUMER",
            0x7F4728
        );
        return false;
    }

    return InstallP64SemanticUjBridge();
}

'''
        s = s.replace(
            insert_anchor,
            block + insert_anchor,
            1
        )

    # ----------------------------------------------------------
    # 4. Functional P67 top-level.
    #
    # NO P65 F58 hook.
    # NO P66 inline BLR hook.
    # Only:
    # Event236 semantic state -> native selector1 consumer.
    # ----------------------------------------------------------

    marker = (
        "void InstallP67AActiveSelector1ConsumerBridge() {"
    )

    insert_anchor = (
        "void InstallP66AVirtualUjSemanticBridge() {"
    )

    if insert_anchor not in s:
        insert_anchor = (
            "void InstallP65ASourceParityActiveUjBridge() {"
        )

    if marker not in s:
        if insert_anchor not in s:
            die("P67 top-level insertion anchor missing")

        block = r'''
void InstallP67AActiveSelector1ConsumerBridge() {
    // P67A architecture:
    //
    // Event236 / MovesetPlus selector1
    //        ↓
    // P64 per-actor semantic state
    //        ↓
    // active input call @ main+0x7F472C
    //        ↓
    // native helper main+0x7ABE9C
    //        ↓
    // native control getter selector1
    //
    // Native return is ALWAYS preserved:
    //   out = native || semantic
    //
    // Semantic overlay is allowed only at exact proven callers,
    // now including active player LR main+0x7F4730.
    //
    // P65 concrete F58 hook: NOT installed.
    // P66 BLR inline hook: NOT installed.

    InstallP50AConditionCompat();

    const bool setter =
        InstallP57CentralSetterTrace();

    const bool mode =
        InstallP59ActionModeBaseTrace();

    const bool semantic =
        InstallP67ActiveSelector1ConsumerBridge();

    Logging.Log(
        "[NSC:P67A] READY "
        "victim_safe_p50=1 "
        "semantic_selector1=1 "
        "selector1_consumer=%d "
        "consumer=0x7abe9c "
        "active_call=0x7f472c "
        "active_return=0x7f4730 "
        "native_selector1_call=0x7abf30 "
        "main_prereq=0x7f2a9c_nop "
        "p65_f58_installed=0 "
        "p66_inline_vcall_installed=0 "
        "no_force87=1 "
        "no_force700=1 "
        "no_selector8=1 "
        "no_char281_branch=1 "
        "central_setter=%d "
        "mode_base=%d",
        semantic ? 1 : 0,
        setter ? 1 : 0,
        mode ? 1 : 0
    );
}

'''
        s = s.replace(
            insert_anchor,
            block + insert_anchor,
            1
        )

    CPP.write_text(
        s,
        encoding="utf-8"
    )


def patch_hpp():
    s = HPP.read_text(encoding="utf-8")

    decl = (
        "void "
        "InstallP67AActiveSelector1ConsumerBridge();\n"
    )

    if decl not in s:
        candidates = [
            (
                "void "
                "InstallP66AVirtualUjSemanticBridge();\n"
            ),
            (
                "void "
                "InstallP65ASourceParityActiveUjBridge();\n"
            ),
        ]

        for anchor in candidates:
            if anchor in s:
                s = s.replace(
                    anchor,
                    anchor + decl,
                    1
                )
                break
        else:
            die("HPP installer anchor missing")

    HPP.write_text(
        s,
        encoding="utf-8"
    )


def patch_main():
    s = MAIN.read_text(encoding="utf-8")

    target = (
        "nsc::InstallP67AActiveSelector1ConsumerBridge();"
    )

    if target not in s:
        replaced = False

        for old in (
            "nsc::InstallP66AVirtualUjSemanticBridge();",
            "nsc::InstallP65ASourceParityActiveUjBridge();",
            "nsc::InstallP64FUjSemanticBridge();",
        ):
            if old in s:
                s = s.replace(
                    old,
                    target,
                    1
                )
                replaced = True
                break

        if not replaced:
            die("active installer call not found")

    s = re.sub(
        r'EXL_ABORT\("NSC P(?:64F|65A|66A)[^"]*"\);',
        'EXL_ABORT("NSC P67A active selector1 consumer bridge exception");',
        s
    )

    MAIN.write_text(
        s,
        encoding="utf-8"
    )


def make_prepare():
    if not P65_PREP.is_file():
        die("prepare_exlaunch_p65a.sh missing")

    s = P65_PREP.read_text(encoding="utf-8")

    s = s.replace(
        "p65a_final.elf",
        "p67a_final.elf"
    )

    s = s.replace(
        "P65A",
        "P67A"
    )

    P67_PREP.write_text(
        s,
        encoding="utf-8"
    )


def disable_push(path):
    if not path.is_file():
        return

    s = path.read_text(encoding="utf-8")

    s = s.replace(
        "on:\n"
        "  workflow_dispatch:\n"
        "  push:\n",
        "on:\n"
        "  workflow_dispatch:\n",
        1
    )

    path.write_text(
        s,
        encoding="utf-8"
    )


def write_verifier():
    p = ROOT / "verify_p67a_kit.py"

    p.write_text(r'''#!/usr/bin/env python3

from pathlib import Path
import re
import struct
import hashlib
import lz4.block

ROOT = Path(__file__).resolve().parent

CPP = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAINCPP = ROOT / "overlay/source/program/main.cpp"

DEPLOY = ROOT / (
    "deploy/atmosphere/contents/"
    "0100FA10190A0000/exefs/main"
)

RESTORE = ROOT / (
    "restore/atmosphere/contents/"
    "0100FA10190A0000/exefs/main"
)

BID = (
    "48ece454b61412b9fb46fab2be3f5ef"
    "7b2804f39"
)


def die(s):
    raise SystemExit("FAIL: " + s)


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load(path):
    raw = path.read_bytes()

    if raw[:4] != b"NSO0":
        die(f"{path}: not NSO0")

    bid = raw[0x40:0x54].hex()

    if bid.lower() != BID.lower():
        die(
            f"{path}: Build ID mismatch {bid}"
        )

    flags = u32(raw, 0x0C)
    foff = u32(raw, 0x10)
    mem = u32(raw, 0x14)
    size = u32(raw, 0x18)
    csize = u32(raw, 0x60)

    src = raw[foff:foff+csize]

    if flags & 1:
        text = lz4.block.decompress(
            src,
            uncompressed_size=size
        )
    else:
        text = raw[foff:foff+size]

    if len(text) != size:
        die("text size mismatch")

    return raw, text, mem


def word(text, mem, va):
    off = va - mem

    if off < 0 or off + 4 > len(text):
        die(f"VA 0x{va:X} outside text")

    return struct.unpack_from(
        "<I",
        text,
        off
    )[0]


def bl_target(pc, w):
    if (w & 0xFC000000) != 0x94000000:
        return None

    imm = w & 0x03FFFFFF

    if imm & 0x02000000:
        imm -= 0x04000000

    return pc + (imm << 2)


cpp = CPP.read_text(encoding="utf-8")
hpp = HPP.read_text(encoding="utf-8")
maincpp = MAINCPP.read_text(encoding="utf-8")

required = [
    "kUjSemanticActivePlayerReturnOffset = 0x7F4730",
    "caller_off == kUjSemanticActivePlayerReturnOffset",
    "InstallP67ActiveSelector1ConsumerBridge",
    "InstallP67AActiveSelector1ConsumerBridge",
    "[NSC:P67A] READY",
]

for x in required:
    if x not in cpp:
        die("missing source marker: " + x)

if (
    "void InstallP67AActiveSelector1ConsumerBridge();"
    not in hpp
):
    die("P67 HPP declaration missing")

if (
    "nsc::InstallP67AActiveSelector1ConsumerBridge();"
    not in maincpp
):
    die("main does not call P67")

for forbidden in (
    "nsc::InstallP66AVirtualUjSemanticBridge();",
    "nsc::InstallP65ASourceParityActiveUjBridge();",
    "nsc::InstallP64FUjSemanticBridge();",
):
    if forbidden in maincpp:
        die(
            "legacy installer still active: "
            + forbidden
        )

# Make sure the P67 top-level itself does NOT install
# P65/P66/F58 routes.
a = cpp.find(
    "void InstallP67AActiveSelector1ConsumerBridge()"
)

if a < 0:
    die("P67 body missing")

next_candidates = [
    x for x in (
        cpp.find(
            "void InstallP66AVirtualUjSemanticBridge()",
            a + 1
        ),
        cpp.find(
            "void InstallP65ASourceParityActiveUjBridge()",
            a + 1
        ),
        cpp.find(
            "void InstallP52APreUjProbe()",
            a + 1
        ),
    )
    if x >= 0
]

b = min(next_candidates) if next_candidates else len(cpp)

body = cpp[a:b]

for forbidden in (
    "InstallP65ActiveUjEligibilityBridge()",
    "InstallP66ActiveUjVirtualCallBridge()",
    "InstallP63UjRouterTrace()",
):
    if forbidden in body:
        die(
            "P67 body installs forbidden route: "
            + forbidden
        )

if (
    "InstallP67ActiveSelector1ConsumerBridge()"
    not in body
):
    die("P67 functional installer missing")

for pat in (
    r"char_id\s*==\s*281",
    r"char_id\s*!=\s*281",
    r"char_id\s*==\s*0x119",
    r"char_id\s*!=\s*0x119",
):
    if re.search(pat, cpp):
        die(
            "character-specific branch found: "
            + pat
        )

raw, text, mem = load(DEPLOY)

# Source parity NOP remains.
if (
    word(text, mem, 0x7F2A9C)
    != 0xD503201F
):
    die(
        "paired main missing "
        "0x7F2A9C NOP"
    )

# Active player call to semantic/native selector1 helper.
if (
    word(text, mem, 0x7F4728)
    != 0xAA1303E0
):
    die("0x7F4728 fingerprint")

w = word(text, mem, 0x7F472C)

if (
    bl_target(0x7F472C, w)
    != 0x7ABE9C
):
    die(
        "0x7F472C does not call 0x7ABE9C"
    )

if (
    word(text, mem, 0x7F4730)
    != 0x35FFEE40
):
    die("0x7F4730 fingerprint")

# Inside helper: selector1 must be loaded immediately
# before native control getter.
if (
    word(text, mem, 0x7ABF2C)
    != 0x52800021
):
    die(
        "0x7ABF2C is not MOV W1,#1"
    )

w = word(text, mem, 0x7ABF30)

if (
    bl_target(0x7ABF30, w)
    != 0x7C6280
):
    die(
        "0x7ABF30 does not call "
        "native control getter"
    )

_, restore_text, restore_mem = load(RESTORE)

if (
    word(
        restore_text,
        restore_mem,
        0x7F2A9C
    )
    != 0xBD001FE0
):
    die(
        "restore main not pristine "
        "at 0x7F2A9C"
    )

print("P67_SOURCE_VERIFY=PASS")
print(
    "P67_ACTIVE_CALL_VERIFY=PASS "
    "0x7F472C->0x7ABE9C"
)
print(
    "P67_SELECTOR1_VERIFY=PASS "
    "0x7ABF2C=W1#1 "
    "0x7ABF30->0x7C6280"
)
print(
    "P67_MAIN_PREREQ_VERIFY=PASS "
    "0x7F2A9C=D503201F"
)
print(
    "DEPLOY_MAIN_SHA256="
    + hashlib.sha256(raw).hexdigest()
)
print("P67A_STATIC_VERIFY=PASS")
''', encoding="utf-8")


def write_docs():
    (ROOT / "README_P67A.txt").write_text(
        """NSC P67A — ACTIVE SELECTOR1 CONSUMER BRIDGE

P66 RESULT
P66 inline-hooked BLR X8 at 0x7F46B4 and caused a
vanilla UJ regression. That architecture is removed.

STATIC PROOF
Active input function contains:

0x7F4728 MOV X0,X19
0x7F472C BL  0x7ABE9C
0x7F4730 CBNZ W0,...

Inside 0x7ABE9C:

0x7ABF2C MOV W1,#1
0x7ABF30 BL  0x7C6280

Thus the helper is a direct native selector1 consumer.

P67 CHANGE
Existing semantic selector1 overlay is enabled at exact
active-player return address 0x7F4730 in addition to the
previous proven router callers.

Native result is always preserved.

NO:
- char281 branch
- F58 forcing
- action700 forcing
- state87 forcing
- selector8 mapping
- P66 inline BLR replacement
""",
        encoding="utf-8"
    )


def write_workflow():
    P67_WF.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    P67_WF.write_text(r'''name: Build NSC P67A Active Selector1 Consumer Bridge

on:
  workflow_dispatch:
  push:

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest

    container:
      image: devkitpro/devkita64:latest

    env:
      DEVKITPRO: /opt/devkitpro
      DEVKITA64: /opt/devkitpro/devkitA64

    steps:
      - name: Checkout P67A
        uses: actions/checkout@v4

      - name: Verify layout
        shell: bash
        run: |
          set -euxo pipefail

          test -f verify_p67a_kit.py
          test -f prepare_exlaunch_p67a.sh
          test -f overlay/source/program/nsc_cpk_bridge.cpp
          test -f overlay/source/program/main.cpp
          test -f deploy/atmosphere/contents/0100FA10190A0000/exefs/main
          test -f restore/atmosphere/contents/0100FA10190A0000/exefs/main

      - name: Verify toolchain
        shell: bash
        run: |
          set -euxo pipefail

          export PATH="$DEVKITPRO/tools/bin:$DEVKITA64/bin:$PATH"

          "$DEVKITA64/bin/aarch64-none-elf-g++" --version
          python3 --version

          if python3 -c 'import lz4.block' 2>/dev/null; then
            echo "python lz4 already available"
          elif command -v apt-get >/dev/null 2>&1; then
            apt-get update
            DEBIAN_FRONTEND=noninteractive \
              apt-get install -y python3-lz4
          elif command -v apk >/dev/null 2>&1; then
            apk add --no-cache py3-lz4
          else
            echo "FATAL: no package manager for python lz4"
            exit 1
          fi

          python3 -c \
            'import lz4.block; print("PYTHON_LZ4=PASS")'

      - name: Verify P67A
        shell: bash
        run: |
          set -euxo pipefail

          python3 generate_condition_table.py \
            condition_compat_manifest.json \
            /tmp/condition_compat_generated.hpp

          cmp \
            /tmp/condition_compat_generated.hpp \
            overlay/source/program/condition_compat_generated.hpp

          python3 verify_p67a_kit.py

      - name: Clone pinned exlaunch
        shell: bash
        run: |
          set -euxo pipefail

          git clone \
            https://github.com/shadowninja108/exlaunch.git \
            "$GITHUB_WORKSPACE/exlaunch"

          git -C "$GITHUB_WORKSPACE/exlaunch" \
            checkout --detach 229bbd6

          git -C "$GITHUB_WORKSPACE/exlaunch" \
            submodule update --init --recursive

          test "$(
            git -C "$GITHUB_WORKSPACE/exlaunch" \
              rev-parse --short HEAD
          )" = "229bbd6"

      - name: Overlay P67A
        shell: bash
        run: |
          set -euxo pipefail

          sed -i 's/\r$//' \
            prepare_exlaunch_p67a.sh || true

          chmod +x \
            prepare_exlaunch_p67a.sh

          bash ./prepare_exlaunch_p67a.sh \
            "$GITHUB_WORKSPACE/exlaunch"

          grep -F \
            'ELF_EXTRACT := $(PWD)/p67a_final.elf' \
            "$GITHUB_WORKSPACE/exlaunch/config.mk"

      - name: Build subsdk9
        shell: bash
        run: |
          set -euxo pipefail

          export PATH="$DEVKITPRO/tools/bin:$DEVKITA64/bin:$PATH"

          cd "$GITHUB_WORKSPACE/exlaunch"
          make -j2

      - name: Collect P67A
        shell: bash
        run: |
          set -euxo pipefail

          cd "$GITHUB_WORKSPACE"

          OUT="exlaunch/deploy/subsdk9"
          ELF="exlaunch/p67a_final.elf"

          test -s "$OUT"
          test -s "$ELF"

          grep -aFq '[NSC:P67A] READY' "$ELF"
          grep -aFq '[NSC:P64F] UJ_SEM_GATE' "$ELF"
          grep -aFq '[NSC:P64F] UJ_SEM_SET' "$ELF"
          grep -aFq '[NSC:P50A] READY' "$ELF"

          python3 - "$OUT" <<'PY2'
          from pathlib import Path
          import sys

          b = Path(sys.argv[1]).read_bytes()

          assert len(b) > 10000
          assert b[:4] == b'NSO0'

          print("P67A_NSO_VERIFY=PASS")
          PY2

          rm -rf artifact

          mkdir -p \
            artifact/atmosphere/contents/0100FA10190A0000/exefs

          cp "$OUT" \
            artifact/atmosphere/contents/0100FA10190A0000/exefs/subsdk9

          cp \
            deploy/atmosphere/contents/0100FA10190A0000/exefs/main \
            artifact/atmosphere/contents/0100FA10190A0000/exefs/main

          mkdir -p \
            artifact/restore/atmosphere/contents/0100FA10190A0000/exefs

          cp \
            restore/atmosphere/contents/0100FA10190A0000/exefs/main \
            artifact/restore/atmosphere/contents/0100FA10190A0000/exefs/main

          cp \
            README_P67A.txt \
            artifact/

          (
            cd artifact
            find . -type f -print0 \
              | sort -z \
              | xargs -0 sha256sum \
              > SHA256SUMS.txt
          )

      - name: Upload P67A artifact
        uses: actions/upload-artifact@v4
        with:
          name: NSC-P67A-active-selector1-consumer-bridge
          path: artifact/
          compression-level: 9
''', encoding="utf-8")


def main():
    for p in (CPP, HPP, MAIN):
        if not p.is_file():
            die("missing " + str(p))

    backup()

    patch_cpp()
    patch_hpp()
    patch_main()
    make_prepare()

    disable_push(P65_WF)
    disable_push(P66_WF)

    write_verifier()
    write_docs()
    write_workflow()

    print("P67A_SOURCE_PATCH=PASS")


if __name__ == "__main__":
    main()
