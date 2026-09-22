#!/usr/bin/env python3

from pathlib import Path
import re
import shutil
import struct
import hashlib

ROOT = Path(__file__).resolve().parent

CPP = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAINCPP = ROOT / "overlay/source/program/main.cpp"

P65_PREP = ROOT / "prepare_exlaunch_p65a.sh"
P66_PREP = ROOT / "prepare_exlaunch_p66a.sh"

P65_WF = ROOT / ".github/workflows/build-subsdk9-p65a.yml"
P66_WF = ROOT / ".github/workflows/build-subsdk9-p66a.yml"

VERIFY = ROOT / "verify_p66a_kit.py"

DEPLOY_MAIN = ROOT / (
    "deploy/atmosphere/contents/"
    "0100FA10190A0000/exefs/main"
)

RESTORE_MAIN = ROOT / (
    "restore/atmosphere/contents/"
    "0100FA10190A0000/exefs/main"
)


def die(s):
    raise SystemExit("FATAL: " + s)


def replace_once(s, old, new, label):
    if new in s:
        return s

    count = s.count(old)
    if count != 1:
        die(f"{label}: anchor count={count}")

    return s.replace(old, new, 1)


def backup():
    dst = ROOT / "P66A_BACKUP_P65A"

    if dst.exists():
        return

    dst.mkdir()

    for p in (
        CPP,
        HPP,
        MAINCPP,
        DEPLOY_MAIN,
        P65_PREP,
        P65_WF,
    ):
        if p.is_file():
            shutil.copy2(p, dst / p.name)

    print("P66_BACKUP=PASS")


def patch_cpp():
    s = CPP.read_text(encoding="utf-8")

    # ------------------------------------------------------------
    # CONSTANTS
    # ------------------------------------------------------------

    anchor = (
        "constexpr ptrdiff_t "
        "kP65ActivePlayerUjCallerReturnOffset = 0x7F46B8;\n"
    )

    add = anchor + (
        "// P66A: actual runtime UJ consumer boundary. "
        "The game loads actor->vtable+0xF58\n"
        "// into X8 and performs BLR X8 at main+0x7F46B4. "
        "P66 hooks this callsite,\n"
        "// not one concrete virtual implementation.\n"
        "constexpr ptrdiff_t "
        "kP66ActiveUjVirtualCallOffset = 0x7F46B4;\n"
        "constexpr ptrdiff_t "
        "kP66ActiveUjResultGateOffset = 0x7F46B8;\n"
    )

    s = replace_once(
        s,
        anchor,
        add,
        "P66 constants"
    )

    # ------------------------------------------------------------
    # COUNTER
    # ------------------------------------------------------------

    anchor = (
        "std::atomic<uint32_t> "
        "g_p65_active_uj_gate_logs{0};\n"
    )

    add = anchor + (
        "std::atomic<uint32_t> "
        "g_p66_virtual_uj_gate_logs{0};\n"
    )

    s = replace_once(
        s,
        anchor,
        add,
        "P66 counter"
    )

    # ------------------------------------------------------------
    # INLINE HOOK
    # ------------------------------------------------------------

    marker = (
        "// P66A: generic semantic overlay at the "
        "actual actor-specific virtual UJ call."
    )

    insert_anchor = (
        "// P65A: functional bridge at the "
        "runtime-proven player UJ F58 call."
    )

    if marker not in s:
        if insert_anchor not in s:
            die("P66 hook insertion anchor missing")

        hook = r'''
// P66A: generic semantic overlay at the actual actor-specific virtual UJ call.
//
// Static v1.70 proof:
//
//   0x7F46A4  LDR X8,[X19]
//   0x7F46A8  MOV X0,X19
//   0x7F46AC  MOV W1,WZR
//   0x7F46B0  LDR X8,[X8,#0xF58]
//   0x7F46B4  BLR X8
//   0x7F46B8  CBZ W0,0x7F4738
//
// P65 hooked one concrete F58 implementation (0x7D3138). That is
// insufficient for polymorphic/custom actors because the game dispatches
// through actor->vtable+0xF58.
//
// This inline hook replaces ONLY the BLR instruction. It explicitly calls
// the actor's ORIGINAL virtual implementation from X8, then ORs the native
// result with the source-derived MovesetPlus selector1 semantic.
//
// No character ID is special-cased and the following native CBZ remains
// untouched.
HOOK_DEFINE_INLINE(P66ActiveUjVirtualCallHook) {
    static void Callback(exl::hook::nx64::InlineCtx* ctx) {
        using VirtualUjFn =
            uint32_t (*)(void*, uint32_t, uint32_t);

        void* actor =
            reinterpret_cast<void*>(ctx->X[0]);

        const uint32_t mode =
            ctx->W[1];

        const uint32_t context =
            ctx->W[2];

        const uintptr_t virtual_target =
            static_cast<uintptr_t>(ctx->X[8]);

        uint32_t native = 0u;

        if (virtual_target != 0u) {
            auto fn =
                reinterpret_cast<VirtualUjFn>(
                    virtual_target
                );

            native = fn(
                actor,
                mode,
                context
            );
        }

        const bool semantic =
            P64QuerySemanticUltimateJutsu(actor);

        const uint32_t out =
            (native != 0u || semantic)
                ? 1u
                : 0u;

        // The original BLR would return its result in W0.
        // Since the inline hook replaces BLR, reproduce that ABI result.
        ctx->W[0] = out;

        uint32_t side = 0xFFFFFFFFu;
        uint32_t char_id = 0xFFFFFFFFu;

        const bool valid =
            ReadActorIdentity(
                actor,
                side,
                char_id
            );

        if (valid) {
            const uint32_t n =
                g_p66_virtual_uj_gate_logs.fetch_add(
                    1,
                    std::memory_order_relaxed
                );

            // Keep enough vanilla control samples while guaranteeing
            // semantic/custom calls remain visible in logs.
            if (
                n < 256u &&
                (
                    semantic ||
                    native != 0u ||
                    char_id > kVanillaMaxCharId
                )
            ) {
                const ptrdiff_t impl_off =
                    MainRelativeOffset(
                        virtual_target
                    );

                Logging.Log(
                    "[NSC:P66A] UJ_VCALL_GATE "
                    "n=%u actor=%p side=%u char=%u "
                    "impl=%p impl_off=0x%lx "
                    "mode=%u context=%u "
                    "native=%u semantic=%u ret=%u",
                    n,
                    actor,
                    side,
                    char_id,
                    reinterpret_cast<void*>(
                        virtual_target
                    ),
                    static_cast<unsigned long>(
                        impl_off
                    ),
                    mode,
                    context,
                    native,
                    semantic ? 1u : 0u,
                    out
                );
            }
        }
    }
};

'''
        s = s.replace(
            insert_anchor,
            hook + insert_anchor,
            1
        )

    # ------------------------------------------------------------
    # INSTALLER
    # ------------------------------------------------------------

    installer_marker = (
        "bool InstallP66ActiveUjVirtualCallBridge() {"
    )

    installer_anchor = (
        "bool InstallP65ActiveUjEligibilityBridge() {"
    )

    if installer_marker not in s:
        if installer_anchor not in s:
            die("P66 installer anchor missing")

        installer = r'''
bool InstallP66ActiveUjVirtualCallBridge() {
    // Strict fingerprint over the complete actor-vtable dispatch window:
    //
    // 7F46A4 LDR X8,[X19]
    // 7F46A8 MOV X0,X19
    // 7F46AC MOV W1,WZR
    // 7F46B0 LDR X8,[X8,#0xF58]
    // 7F46B4 BLR X8
    // 7F46B8 CBZ W0,7F4738
    // 7F46BC MOV X0,X19
    // 7F46C0 MOV W1,WZR
    // 7F46C4 BL  7D2DE4
    static constexpr uint32_t kExpected[] = {
        0xF9400268,
        0xAA1303E0,
        0x2A1F03E1,
        0xF947AD08,
        0xD63F0100,
        0x34000400,
        0xAA1303E0,
        0x2A1F03E1,
        0x97FF79C8,
    };

    if (!MatchWords(0x7F46A4, kExpected)) {
        LogFingerprintFail(
            "P66_UJ_VIRTUAL_CALL",
            0x7F46A4
        );
        return false;
    }

    P66ActiveUjVirtualCallHook::InstallAtOffset(
        kP66ActiveUjVirtualCallOffset
    );

    return true;
}

'''
        s = s.replace(
            installer_anchor,
            installer + installer_anchor,
            1
        )

    # ------------------------------------------------------------
    # TOP-LEVEL BUILD
    # ------------------------------------------------------------

    top_marker = (
        "void InstallP66AVirtualUjSemanticBridge() {"
    )

    top_anchor = (
        "void InstallP65ASourceParityActiveUjBridge() {"
    )

    if top_marker not in s:
        if top_anchor not in s:
            die("P66 top-level anchor missing")

        top = r'''
void InstallP66AVirtualUjSemanticBridge() {
    // Functional P66A:
    //
    // - P50 victim-safe Event236/condition/CPK core remains intact.
    // - Event236 selector1 still populates P64 semantic UJ state.
    // - P65's concrete 0x7D3138 trampoline is NOT installed.
    // - P64's inactive 0x7ABE9C semantic consumer is NOT installed.
    // - P63 F58 tracer is NOT installed.
    //
    // Instead, the actual polymorphic callsite at main+0x7F46B4 is
    // intercepted. The actor-specific native vtable+0xF58 implementation
    // is called first, and only its boolean result is ORed with selector1.
    //
    // The paired main keeps the source-parity prerequisite:
    // 0x7F2A9C BD001FE0 -> D503201F.

    InstallP50AConditionCompat();

    const bool setter =
        InstallP57CentralSetterTrace();

    const bool mode =
        InstallP59ActionModeBaseTrace();

    const bool uj_vcall =
        InstallP66ActiveUjVirtualCallBridge();

    Logging.Log(
        "[NSC:P66A] READY "
        "victim_safe_p50=1 "
        "semantic_selector1=1 "
        "virtual_uj_bridge=%d "
        "virtual_call=0x7f46b4 "
        "result_gate=0x7f46b8 "
        "slot=0xf58 "
        "main_prereq=0x7f2a9c_nop "
        "p65_concrete_f58_installed=0 "
        "p64_7abe9c_installed=0 "
        "central_setter=%d "
        "mode_base=%d "
        "no_force87=1 "
        "no_force700=1 "
        "no_selector8=1 "
        "no_char281_branch=1",
        uj_vcall ? 1 : 0,
        setter ? 1 : 0,
        mode ? 1 : 0
    );
}

'''
        s = s.replace(
            top_anchor,
            top + top_anchor,
            1
        )

    CPP.write_text(
        s,
        encoding="utf-8"
    )


def patch_hpp():
    s = HPP.read_text(
        encoding="utf-8"
    )

    anchor = (
        "void "
        "InstallP65ASourceParityActiveUjBridge();\n"
    )

    add = anchor + (
        "void "
        "InstallP66AVirtualUjSemanticBridge();\n"
    )

    s = replace_once(
        s,
        anchor,
        add,
        "P66 HPP"
    )

    HPP.write_text(
        s,
        encoding="utf-8"
    )


def patch_main():
    s = MAINCPP.read_text(
        encoding="utf-8"
    )

    if (
        "nsc::InstallP66AVirtualUjSemanticBridge();"
        not in s
    ):
        s = replace_once(
            s,
            "nsc::InstallP65ASourceParityActiveUjBridge();",
            "nsc::InstallP66AVirtualUjSemanticBridge();",
            "P66 main call"
        )

    s = s.replace(
        'EXL_ABORT("NSC P65A source-parity active UJ bridge exception");',
        'EXL_ABORT("NSC P66A virtual UJ semantic bridge exception");'
    )

    MAINCPP.write_text(
        s,
        encoding="utf-8"
    )


def make_prepare():
    if not P65_PREP.is_file():
        die(
            "prepare_exlaunch_p65a.sh missing"
        )

    s = P65_PREP.read_text(
        encoding="utf-8"
    )

    s = s.replace(
        "p65a_final.elf",
        "p66a_final.elf"
    )

    s = s.replace(
        "P65A",
        "P66A"
    )

    P66_PREP.write_text(
        s,
        encoding="utf-8"
    )


def disable_legacy_push(path):
    if not path.is_file():
        return

    s = path.read_text(
        encoding="utf-8"
    )

    old = (
        "on:\n"
        "  workflow_dispatch:\n"
        "  push:\n"
    )

    new = (
        "on:\n"
        "  workflow_dispatch:\n"
    )

    if old in s:
        s = s.replace(
            old,
            new,
            1
        )

        path.write_text(
            s,
            encoding="utf-8"
        )


def write_verifier():
    VERIFY.write_text(r'''#!/usr/bin/env python3

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

TARGET_BID = (
    "48ece454b61412b9fb46fab2be3f5ef"
    "7b2804f39"
)


def die(s):
    raise SystemExit("FAIL: " + s)


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load_text(path):
    raw = path.read_bytes()

    if raw[:4] != b"NSO0":
        die(f"{path}: not NSO0")

    bid = raw[0x40:0x54].hex()

    if bid.lower() != TARGET_BID.lower():
        die(
            f"{path}: Build ID mismatch "
            f"{bid}"
        )

    flags = u32(raw, 0x0C)

    fileoff = u32(raw, 0x10)
    memoff = u32(raw, 0x14)
    size = u32(raw, 0x18)
    csize = u32(raw, 0x60)

    src = raw[
        fileoff:
        fileoff + csize
    ]

    if flags & 1:
        text = lz4.block.decompress(
            src,
            uncompressed_size=size
        )
    else:
        text = raw[
            fileoff:
            fileoff + size
        ]

    if len(text) != size:
        die("text size mismatch")

    return raw, text, memoff


def word(text, mem, va):
    off = va - mem

    if off < 0 or off + 4 > len(text):
        die(f"VA 0x{va:X} outside text")

    return struct.unpack_from(
        "<I",
        text,
        off
    )[0]


cpp = CPP.read_text(
    encoding="utf-8"
)

hpp = HPP.read_text(
    encoding="utf-8"
)

maincpp = MAINCPP.read_text(
    encoding="utf-8"
)

required = [
    "P66ActiveUjVirtualCallHook",
    "InstallP66ActiveUjVirtualCallBridge",
    "InstallP66AVirtualUjSemanticBridge",
    "[NSC:P66A] UJ_VCALL_GATE",
    "kP66ActiveUjVirtualCallOffset = 0x7F46B4",
    "P64QuerySemanticUltimateJutsu(actor)",
    "ctx->W[0] = out",
]

for x in required:
    if x not in cpp:
        die(
            "missing source marker: " + x
        )

if (
    "void InstallP66AVirtualUjSemanticBridge();"
    not in hpp
):
    die("missing HPP declaration")

if (
    "nsc::InstallP66AVirtualUjSemanticBridge();"
    not in maincpp
):
    die("main does not call P66")

if (
    "nsc::InstallP65ASourceParityActiveUjBridge();"
    in maincpp
):
    die("main still calls P65")

a = cpp.find(
    "void InstallP66AVirtualUjSemanticBridge()"
)

b = cpp.find(
    "void InstallP65ASourceParityActiveUjBridge()",
    a
)

if a < 0 or b < 0:
    die(
        "cannot isolate P66 top-level"
    )

body = cpp[a:b]

for forbidden in (
    "InstallP65ActiveUjEligibilityBridge()",
    "InstallP64SemanticUjBridge()",
    "InstallP63UjRouterTrace()",
):
    if forbidden in body:
        die(
            "P66 active path contains "
            + forbidden
        )

if (
    "InstallP66ActiveUjVirtualCallBridge()"
    not in body
):
    die("P66 bridge not active")

for pat in (
    r"char_id\s*==\s*281",
    r"char_id\s*!=\s*281",
    r"char_id\s*==\s*0x119",
    r"char_id\s*!=\s*0x119",
):
    if re.search(pat, cpp):
        die(
            "character-specific branch: "
            + pat
        )

raw, text, mem = load_text(DEPLOY)

if (
    word(text, mem, 0x7F2A9C)
    != 0xD503201F
):
    die(
        "paired main missing "
        "0x7F2A9C NOP"
    )

expected = {
    0x7F46A4: 0xF9400268,
    0x7F46A8: 0xAA1303E0,
    0x7F46AC: 0x2A1F03E1,
    0x7F46B0: 0xF947AD08,
    0x7F46B4: 0xD63F0100,
    0x7F46B8: 0x34000400,
    0x7F46BC: 0xAA1303E0,
    0x7F46C0: 0x2A1F03E1,
    0x7F46C4: 0x97FF79C8,
}

for va, exp in expected.items():
    got = word(
        text,
        mem,
        va
    )

    if got != exp:
        die(
            f"callsite fingerprint "
            f"0x{va:X}: "
            f"{got:08X} != {exp:08X}"
        )

_, restore_text, restore_mem = (
    load_text(RESTORE)
)

if (
    word(
        restore_text,
        restore_mem,
        0x7F2A9C
    )
    != 0xBD001FE0
):
    die(
        "restore main is not pristine "
        "at 0x7F2A9C"
    )

print("P66_SOURCE_VERIFY=PASS")
print("P66_VCALL_FINGERPRINT=PASS")
print(
    "P66_MAIN_PREREQ_VERIFY=PASS "
    "0x7F2A9C=D503201F"
)
print(
    "DEPLOY_MAIN_SHA256="
    + hashlib.sha256(
        raw
    ).hexdigest()
)
print("P66A_STATIC_VERIFY=PASS")
''', encoding="utf-8")


def write_docs():
    (ROOT / "README_P66A.txt").write_text(
        """NSC P66A — VIRTUAL UJ SEMANTIC BRIDGE

CORE CHANGE

P65 hooked concrete F58 implementation 0x7D3138.

Static disassembly proves the real player-UJ consumer is polymorphic:

7F46A4 LDR X8,[X19]
7F46A8 MOV X0,X19
7F46AC MOV W1,WZR
7F46B0 LDR X8,[X8,#0xF58]
7F46B4 BLR X8
7F46B8 CBZ W0,7F4738

P66 hooks 0x7F46B4.

The inline callback:
1. obtains original actor-specific function pointer from X8;
2. calls it with the original X0/W1/W2 arguments;
3. queries the existing selector1 semantic for the same actor;
4. writes W0 = native || semantic;
5. leaves the native CBZ at 0x7F46B8 untouched.

Paired main retains:
0x7F2A9C BD001FE0 -> D503201F

FORBIDDEN / ABSENT
- no char281 branch
- no force action700
- no force state0x87
- no selector8
- no 445->700
- no raw Event236 restoration
- no old 0x7E1404 Ougi tail
""",
        encoding="utf-8"
    )

    (ROOT / "P66A_STATIC_AUDIT.txt").write_text(
        """P66A STATIC AUDIT

PROVEN STATIC
- 0x7F46B4 = BLR X8.
- X8 is loaded immediately from actor vtable+0xF58.
- 0x7F46B8 is CBZ W0, reject path 0x7F4738.
- success path calls 0x7D2DE4 at 0x7F46C4.
- paired main keeps 0x7F2A9C NOP.

PROVEN RUNTIME FROM P65
- selector1 semantic reaches custom actor.
- P65 concrete 0x7D3138 hook logs vanilla char91.
- custom Tobi remains on ordinary 445 path.

P66A CHANGE
Move semantic overlay from one concrete F58 implementation
to the actual actor-polymorphic virtual-call boundary.

HARDWARE STATUS
Not proven until fresh P66A run.
""",
        encoding="utf-8"
    )

    (ROOT / "R75_P66A_CHECKPOINT.md").write_text(
        """# R75 / P66A

P65A established that hooking concrete implementation 0x7D3138 is
insufficient.

P66A uses the statically proven callsite:

actor -> vtable -> +0xF58 -> BLR X8 @ 0x7F46B4

The original actor-specific function is called first.

Return policy:

native true -> true
native false + selector1 false -> false
native false + selector1 true -> true

No character-specific executable branch.
""",
        encoding="utf-8"
    )


def write_workflow():
    P66_WF.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    P66_WF.write_text(r'''name: Build NSC P66A Virtual UJ Semantic Bridge

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
      - name: Checkout P66A
        uses: actions/checkout@v4

      - name: Verify repository layout
        shell: bash
        run: |
          set -euxo pipefail

          test -f .github/workflows/build-subsdk9-p66a.yml
          test -f prepare_exlaunch_p66a.sh
          test -f verify_p66a_kit.py
          test -f overlay/source/program/nsc_cpk_bridge.cpp
          test -f overlay/source/program/main.cpp
          test -f deploy/atmosphere/contents/0100FA10190A0000/exefs/main
          test -f restore/atmosphere/contents/0100FA10190A0000/exefs/main

      - name: Verify toolchain
        shell: bash
        run: |
          set -euxo pipefail

          export PATH="$DEVKITPRO/tools/bin:$DEVKITA64/bin:$PATH"

          test -x "$DEVKITA64/bin/aarch64-none-elf-g++"
          "$DEVKITA64/bin/aarch64-none-elf-g++" --version
          python3 --version

          if python3 -c 'import lz4.block' 2>/dev/null; then
            echo "python lz4 already available"
          elif command -v apt-get >/dev/null 2>&1; then
            apt-get update
            DEBIAN_FRONTEND=noninteractive apt-get install -y python3-lz4
          elif command -v apk >/dev/null 2>&1; then
            apk add --no-cache py3-lz4
          else
            echo "FATAL: no supported package manager for python lz4"
            exit 1
          fi

          python3 -c 'import lz4.block; print("PYTHON_LZ4=PASS")'

      - name: Verify P66A source and paired main
        shell: bash
        run: |
          set -euxo pipefail

          python3 generate_condition_table.py \
            condition_compat_manifest.json \
            /tmp/condition_compat_generated.hpp

          cmp \
            /tmp/condition_compat_generated.hpp \
            overlay/source/program/condition_compat_generated.hpp

          python3 verify_p66a_kit.py

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

      - name: Overlay P66A
        shell: bash
        run: |
          set -euxo pipefail

          sed -i 's/\r$//' prepare_exlaunch_p66a.sh || true
          chmod +x prepare_exlaunch_p66a.sh

          bash ./prepare_exlaunch_p66a.sh \
            "$GITHUB_WORKSPACE/exlaunch"

          grep -F \
            'ELF_EXTRACT := $(PWD)/p66a_final.elf' \
            "$GITHUB_WORKSPACE/exlaunch/config.mk"

      - name: Build subsdk9
        shell: bash
        run: |
          set -euxo pipefail

          export PATH="$DEVKITPRO/tools/bin:$DEVKITA64/bin:$PATH"

          cd "$GITHUB_WORKSPACE/exlaunch"
          make -j2

      - name: Verify linked P66A and collect artifact
        shell: bash
        run: |
          set -euxo pipefail

          cd "$GITHUB_WORKSPACE"

          OUT="exlaunch/deploy/subsdk9"
          ELF="exlaunch/p66a_final.elf"

          test -s "$OUT"
          test -s "$ELF"

          grep -aFq '[NSC:P66A] READY' "$ELF"
          grep -aFq '[NSC:P66A] UJ_VCALL_GATE' "$ELF"
          grep -aFq '[NSC:P64F] UJ_SEM_SET' "$ELF"
          grep -aFq '[NSC:P50A] READY' "$ELF"
          grep -aFq '[NSC:P59A] PLAY_CALL' "$ELF"

          python3 - "$OUT" <<'PY2'
          from pathlib import Path
          import sys

          b = Path(sys.argv[1]).read_bytes()

          assert len(b) > 10000
          assert b[:4] == b'NSO0'

          print("P66A_NSO_VERIFY=PASS")
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
            README_P66A.txt \
            P66A_STATIC_AUDIT.txt \
            R75_P66A_CHECKPOINT.md \
            artifact/

          (
            cd artifact
            find . -type f -print0 \
              | sort -z \
              | xargs -0 sha256sum \
              > SHA256SUMS.txt
          )

          sha256sum "$OUT" "$ELF"

      - name: Upload P66A artifact
        uses: actions/upload-artifact@v4
        with:
          name: NSC-P66A-virtual-uj-semantic-bridge
          path: artifact/
          compression-level: 9
''', encoding="utf-8")


def main():
    for p in (
        CPP,
        HPP,
        MAINCPP,
        DEPLOY_MAIN,
        RESTORE_MAIN,
    ):
        if not p.is_file():
            die("missing " + str(p))

    backup()

    patch_cpp()
    patch_hpp()
    patch_main()
    make_prepare()

    # P65 remains available manually but must not auto-run
    # after main.cpp switches to P66.
    disable_legacy_push(P65_WF)

    write_verifier()
    write_docs()
    write_workflow()

    print("P66A_SOURCE_PATCH=PASS")


if __name__ == "__main__":
    main()
