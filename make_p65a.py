#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import shutil
import struct
import sys

try:
    import lz4.block
except Exception as e:
    raise SystemExit("FATAL: python lz4 belum tersedia: " + str(e))

ROOT = Path(__file__).resolve().parent

CPP = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAINCPP = ROOT / "overlay/source/program/main.cpp"

DEPLOY_MAIN = ROOT / "deploy/atmosphere/contents/0100FA10190A0000/exefs/main"
RESTORE_MAIN = ROOT / "restore/atmosphere/contents/0100FA10190A0000/exefs/main"

PREP64 = ROOT / "prepare_exlaunch.sh"
PREP65 = ROOT / "prepare_exlaunch_p65a.sh"

WF65 = ROOT / ".github/workflows/build-subsdk9-p65a.yml"

TARGET_BUILD_ID = "48ece454b61412b9fb46fab2be3f5ef7b2804f39"

# R72 structural homolog of PC SC1.70 A33C60.
P65_MAIN_PATCH_VA = 0x7F2A9C
P65_MAIN_EXPECTED = 0xBD001FE0   # STR S0,[SP,#0x1C]
P65_MAIN_REPLACE  = 0xD503201F   # NOP


def die(msg):
    raise SystemExit("FATAL: " + msg)


def u32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


def p32(buf, off, val):
    struct.pack_into("<I", buf, off, val)


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def read_nso_text(path):
    raw = bytearray(path.read_bytes())

    if len(raw) < 0x100 or raw[:4] != b"NSO0":
        die(f"{path}: bukan NSO0")

    build_id = raw[0x40:0x54].hex()
    if build_id.lower() != TARGET_BUILD_ID.lower():
        die(
            f"{path}: Build ID mismatch: "
            f"{build_id} != {TARGET_BUILD_ID}"
        )

    flags = u32(raw, 0x0C)

    # This target predates Zbic; fail closed if the format differs.
    if flags & (1 << 7):
        die(f"{path}: Zbic-compressed NSO tidak didukung script ini")

    text_file = u32(raw, 0x10)
    text_mem  = u32(raw, 0x14)
    text_size = u32(raw, 0x18)
    text_file_size = u32(raw, 0x60)

    if text_file <= 0 or text_size <= 0:
        die(f"{path}: invalid text header")

    payload = bytes(raw[text_file:text_file + text_file_size])

    if flags & 1:
        try:
            text = bytearray(
                lz4.block.decompress(
                    payload,
                    uncompressed_size=text_size
                )
            )
        except Exception as e:
            die(f"{path}: gagal decompress .text: {e}")
    else:
        text = bytearray(raw[text_file:text_file + text_size])

    if len(text) != text_size:
        die(
            f"{path}: text size mismatch "
            f"{len(text):x} != {text_size:x}"
        )

    return raw, text, flags, text_file, text_mem, text_size


def patch_nso_text_word(path, va, expected, replacement):
    raw, text, flags, text_file, text_mem, text_size = read_nso_text(path)

    idx = va - text_mem
    if idx < 0 or idx + 4 > len(text):
        die(
            f"{path}: VA 0x{va:X} di luar .text "
            f"(mem=0x{text_mem:X}, size=0x{text_size:X})"
        )

    got = struct.unpack_from("<I", text, idx)[0]

    if got == replacement:
        print(
            f"P65_MAIN_PATCH_ALREADY=PASS "
            f"VA=0x{va:X} word={got:08X}"
        )
        return False

    if got != expected:
        die(
            f"{path}: fingerprint 0x{va:X} mismatch: "
            f"got={got:08X} expected={expected:08X}"
        )

    struct.pack_into("<I", text, idx, replacement)

    # NSO0 text hash = SHA256 over decompressed .text.
    raw[0xA0:0xC0] = hashlib.sha256(text).digest()

    if flags & 1:
        comp = lz4.block.compress(
            bytes(text),
            mode="high_compression",
            compression=12,
            store_size=False
        )

        ro_file = u32(raw, 0x20)
        capacity = ro_file - text_file

        if capacity <= 0:
            die(f"{path}: invalid text->ro file layout")

        if len(comp) > capacity:
            die(
                f"{path}: recompressed text tidak muat: "
                f"0x{len(comp):X} > 0x{capacity:X}"
            )

        raw[text_file:text_file + len(comp)] = comp
        p32(raw, 0x60, len(comp))
    else:
        raw[text_file:text_file + len(text)] = text
        p32(raw, 0x60, len(text))

    path.write_bytes(raw)

    # Post-write hard verification.
    _, check, _, _, check_mem, _ = read_nso_text(path)
    check_idx = va - check_mem
    new = struct.unpack_from("<I", check, check_idx)[0]

    if new != replacement:
        die(
            f"{path}: postpatch mismatch "
            f"{new:08X} != {replacement:08X}"
        )

    print(
        f"P65_MAIN_PATCH=PASS "
        f"VA=0x{va:X} {expected:08X}->{replacement:08X}"
    )
    return True


def verify_main_patch():
    _, text, _, _, mem, _ = read_nso_text(DEPLOY_MAIN)
    idx = P65_MAIN_PATCH_VA - mem

    if idx < 0 or idx + 4 > len(text):
        die("P65 main VA outside text")

    got = struct.unpack_from("<I", text, idx)[0]

    if got != P65_MAIN_REPLACE:
        die(
            "P65 paired main prerequisite missing: "
            f"got={got:08X}"
        )

    print(
        "P65_MAIN_PREREQ_VERIFY=PASS "
        f"0x{P65_MAIN_PATCH_VA:X}={got:08X}"
    )


def replace_once(text, old, new, label):
    if new in text:
        return text
    if text.count(old) != 1:
        die(
            f"{label}: anchor count={text.count(old)}, expected=1"
        )
    return text.replace(old, new, 1)


def modify_cpp():
    s = CPP.read_text(encoding="utf-8")

    # ----------------------------------------------------------
    # 1) Constants
    # ----------------------------------------------------------
    anchor = (
        "constexpr ptrdiff_t kUjEligibilityGateOffset       = 0x7D3138;\n"
    )
    add = (
        anchor
        + "// P65A: runtime-proven player UJ path. P63 hardware captured\n"
        + "// F58 return LR main+0x7F46B8 on a real vanilla UJ attempt.\n"
        + "constexpr ptrdiff_t kP65ActivePlayerUjCallerReturnOffset = 0x7F46B8;\n"
    )
    s = replace_once(s, anchor, add, "P65 constants")

    # ----------------------------------------------------------
    # 2) Counter
    # ----------------------------------------------------------
    anchor = "std::atomic<uint32_t> g_p64_semantic_gate_logs{0};\n"
    add = (
        anchor
        + "std::atomic<uint32_t> g_p65_active_uj_gate_logs{0};\n"
    )
    s = replace_once(s, anchor, add, "P65 counter")

    # ----------------------------------------------------------
    # 3) Functional active-path F58 bridge
    # ----------------------------------------------------------
    hook_marker = "// P65A: functional bridge at the runtime-proven player UJ F58 call."
    p63_anchor = (
        "// P63A: pure read-only trace of the native +0xF58 eligibility implementation.\n"
    )

    if hook_marker not in s:
        if p63_anchor not in s:
            die("P65 hook insertion anchor missing")

        hook = r'''
// P65A: functional bridge at the runtime-proven player UJ F58 call.
//
// P64F proved Event236 selector1 reaches our semantic state, but its
// 0x7ABE9C consumer was not entered during the real player-input path.
// P63 hardware instead observed native F58 being called with LR
// main+0x7F46B8 during a real vanilla UJ attempt.
//
// Contract:
//   * native true always wins;
//   * semantic override is allowed ONLY for LR 0x7F46B8;
//   * semantic state belongs to the same actor;
//   * no action number, state 0x87, control selector or char ID is forced.
//
// The paired main additionally carries the source-parity awakening-UJ
// prerequisite at 0x7F2A9C (STR S0,[SP,#0x1C] -> NOP).
HOOK_DEFINE_TRAMPOLINE(P65ActiveUjEligibilityBridgeHook) {
    static uint32_t Callback(void* actor, uint32_t mode, uint32_t context) {
        uintptr_t caller_lr = 0;
        asm volatile("mov %0, x30" : "=r"(caller_lr));

        const ptrdiff_t caller_off = MainRelativeOffset(caller_lr);
        const uint32_t native = Orig(actor, mode, context);

        const bool exact_active =
            caller_off == kP65ActivePlayerUjCallerReturnOffset;

        const bool semantic =
            exact_active && P64QuerySemanticUltimateJutsu(actor);

        const uint32_t out =
            (native != 0u || semantic) ? 1u : 0u;

        uint32_t side = 0xFFFFFFFFu;
        uint32_t char_id = 0xFFFFFFFFu;
        const bool valid =
            ReadActorIdentity(actor, side, char_id);

        const bool custom =
            valid &&
            char_id > kVanillaMaxCharId &&
            char_id < 0x1000u;

        // Logging is diagnostic only; mutation is the exact_active+semantic
        // return overlay above.
        if (valid && (exact_active || custom)) {
            const uint32_t n =
                g_p65_active_uj_gate_logs.fetch_add(
                    1, std::memory_order_relaxed);

            if (n < 512) {
                Logging.Log(
                    "[NSC:P65A] UJ_ACTIVE_GATE "
                    "n=%u actor=%p side=%u char=%u "
                    "caller_off=0x%lx mode=%u context=%u "
                    "native=%u semantic=%u ret=%u",
                    n, actor, side, char_id,
                    static_cast<unsigned long>(caller_off),
                    mode, context,
                    native,
                    semantic ? 1u : 0u,
                    out
                );
            }
        }

        return out;
    }
};

'''
        s = s.replace(p63_anchor, hook + p63_anchor, 1)

    # ----------------------------------------------------------
    # 4) Installer for P65 hook.
    # Same proven entry fingerprint as P63 F58 trace.
    # ----------------------------------------------------------
    install_marker = "bool InstallP65ActiveUjEligibilityBridge() {"
    p63_install_anchor = "bool InstallP63UjRouterTrace() {"

    if install_marker not in s:
        if p63_install_anchor not in s:
            die("P65 installer insertion anchor missing")

        install = r'''
bool InstallP65ActiveUjEligibilityBridge() {
    static constexpr uint32_t kF58Expected[] = {
        0xFC1C0FE8, 0xA9015FFE, 0xA90257F6, 0xA9034FF4,
        0x5281E808, 0x72A00028, 0xB8686808, 0x2A010108,
        0x340000C8,
    };

    if (!MatchWords(kUjEligibilityGateOffset, kF58Expected)) {
        LogFingerprintFail(
            "P65_ACTIVE_UJ_F58",
            kUjEligibilityGateOffset
        );
        return false;
    }

    P65ActiveUjEligibilityBridgeHook::InstallAtOffset(
        kUjEligibilityGateOffset
    );
    return true;
}

'''
        s = s.replace(p63_install_anchor, install + p63_install_anchor, 1)

    # ----------------------------------------------------------
    # 5) P65 top-level.
    # IMPORTANT:
    #   no InstallP63UjRouterTrace() because same F58 address;
    #   no InstallP64SemanticUjBridge() because runtime did not enter it.
    # ----------------------------------------------------------
    top_marker = "void InstallP65ASourceParityActiveUjBridge() {"
    next_anchor = "void InstallP52APreUjProbe() {"

    if top_marker not in s:
        if next_anchor not in s:
            die("P65 top-level insertion anchor missing")

        top = r'''
void InstallP65ASourceParityActiveUjBridge() {
    // Functional P65A:
    //   P50 victim-safe/event/condition core
    //   + P57 central setter diagnostics
    //   + P59 action-mode diagnostics
    //   + semantic-conditioned override at the runtime-proven F58 caller.
    //
    // P64's 0x7ABE9C consumer is deliberately NOT installed.
    // P63 F58 trace is replaced by the P65 functional hook at the same entry.
    //
    // Paired main carries:
    //   0x7F2A9C BD001FE0 -> D503201F
    // which is independently static-proven as the strongest Switch
    // structural homolog of the PC SC1.70 awakening-UJ prerequisite.

    InstallP50AConditionCompat();

    const bool setter =
        InstallP57CentralSetterTrace();

    const bool mode =
        InstallP59ActionModeBaseTrace();

    const bool active_uj =
        InstallP65ActiveUjEligibilityBridge();

    Logging.Log(
        "[NSC:P65A] READY "
        "clean_p64_semantic_state=1 "
        "p64_consumer_7abe9c_installed=0 "
        "active_f58_bridge=%d "
        "active_caller=0x7f46b8 "
        "main_prereq=0x7f2a9c_nop "
        "central_setter=%d mode_base=%d "
        "victim_safe_p50=1 "
        "no_force87=1 no_force700=1 "
        "no_selector8=1 no_char281_branch=1",
        active_uj ? 1 : 0,
        setter ? 1 : 0,
        mode ? 1 : 0
    );
}

'''
        s = s.replace(next_anchor, top + next_anchor, 1)

    CPP.write_text(s, encoding="utf-8")


def modify_hpp():
    s = HPP.read_text(encoding="utf-8")

    old = "void InstallP64FUjSemanticBridge();\n"
    new = (
        old
        + "void InstallP65ASourceParityActiveUjBridge();\n"
    )

    s = replace_once(s, old, new, "hpp P65 declaration")
    HPP.write_text(s, encoding="utf-8")


def modify_maincpp():
    s = MAINCPP.read_text(encoding="utf-8")

    if "InstallP65ASourceParityActiveUjBridge();" not in s:
        s = replace_once(
            s,
            "nsc::InstallP64FUjSemanticBridge();",
            "nsc::InstallP65ASourceParityActiveUjBridge();",
            "main P65 call"
        )

    s = s.replace(
        'EXL_ABORT("NSC P64F UJ semantic bridge exception");',
        'EXL_ABORT("NSC P65A source-parity active UJ bridge exception");'
    )

    MAINCPP.write_text(s, encoding="utf-8")


def make_prepare_script():
    if not PREP64.is_file():
        die("prepare_exlaunch.sh missing")

    s = PREP64.read_text(encoding="utf-8")
    s = s.replace("p64f_final.elf", "p65a_final.elf")
    s = s.replace("P64F", "P65A")
    PREP65.write_text(s, encoding="utf-8")


def write_workflow():
    WF65.parent.mkdir(parents=True, exist_ok=True)

    workflow = r'''name: Build NSC P65A Source-Parity Active UJ Bridge

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
      - name: Checkout P65A build kit
        uses: actions/checkout@v4

      - name: Verify repository layout
        shell: bash
        run: |
          set -euxo pipefail
          test -f .github/workflows/build-subsdk9-p65a.yml
          test -f make_p65a.py
          test -f prepare_exlaunch_p65a.sh
          test -f overlay/source/program/nsc_cpk_bridge.cpp
          test -f deploy/atmosphere/contents/0100FA10190A0000/exefs/main
          test -f restore/atmosphere/contents/0100FA10190A0000/exefs/main

      - name: Verify devkitPro and Python
        shell: bash
        run: |
          set -euxo pipefail
          export PATH="$DEVKITPRO/tools/bin:$DEVKITA64/bin:$PATH"
          test -x "$DEVKITA64/bin/aarch64-none-elf-g++"
          "$DEVKITA64/bin/aarch64-none-elf-g++" --version
          python3 --version
          python3 -m pip install --quiet lz4

      - name: Verify P65A source and paired main
        shell: bash
        run: |
          set -euxo pipefail
          python3 generate_condition_table.py \
            condition_compat_manifest.json \
            /tmp/condition_compat_generated.hpp

          cmp \
            /tmp/condition_compat_generated.hpp \
            overlay/source/program/condition_compat_generated.hpp

          python3 make_p65a.py --verify-only

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
            git -C "$GITHUB_WORKSPACE/exlaunch" rev-parse --short HEAD
          )" = "229bbd6"

      - name: Overlay P65A sources
        shell: bash
        run: |
          set -euxo pipefail
          sed -i 's/\r$//' prepare_exlaunch_p65a.sh || true
          chmod +x prepare_exlaunch_p65a.sh

          bash ./prepare_exlaunch_p65a.sh \
            "$GITHUB_WORKSPACE/exlaunch"

          grep -F \
            'ELF_EXTRACT := $(PWD)/p65a_final.elf' \
            "$GITHUB_WORKSPACE/exlaunch/config.mk"

      - name: Build subsdk9
        shell: bash
        run: |
          set -euxo pipefail
          export PATH="$DEVKITPRO/tools/bin:$DEVKITA64/bin:$PATH"
          cd "$GITHUB_WORKSPACE/exlaunch"
          make -j2

      - name: Verify linked P65A and collect artifact
        shell: bash
        run: |
          set -euxo pipefail
          cd "$GITHUB_WORKSPACE"

          OUT="exlaunch/deploy/subsdk9"
          ELF="exlaunch/p65a_final.elf"

          test -s "$OUT"
          test -s "$ELF"

          grep -aFq '[NSC:P65A] READY' "$ELF"
          grep -aFq '[NSC:P65A] UJ_ACTIVE_GATE' "$ELF"
          grep -aFq '[NSC:P64F] UJ_SEM_SET' "$ELF"
          grep -aFq '[NSC:P50A] READY' "$ELF"
          grep -aFq '[NSC:P59A] PLAY_CALL' "$ELF"

          python3 - "$OUT" <<'PY2'
          from pathlib import Path
          import sys

          p = Path(sys.argv[1])
          b = p.read_bytes()

          assert len(b) > 10000, len(b)
          assert b[:4] == b'NSO0', b[:4]

          print("P65A_NSO_VERIFY=PASS")
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
            README_P65A.txt \
            P65A_STATIC_AUDIT.txt \
            R74_P65A_CHECKPOINT.md \
            artifact/

          (
            cd artifact
            find . -type f -print0 \
              | sort -z \
              | xargs -0 sha256sum \
              > SHA256SUMS.txt
          )

          sha256sum "$OUT" "$ELF"

      - name: Upload P65A artifact
        uses: actions/upload-artifact@v4
        with:
          name: NSC-P65A-source-parity-active-uj-bridge
          path: artifact/
          compression-level: 9
'''
    WF65.write_text(workflow, encoding="utf-8")


def write_docs():
    (ROOT / "README_P65A.txt").write_text(
        """NSC P65A — SOURCE-PARITY ACTIVE UJ BRIDGE

Parent:
P64F semantic selector1 state + P50 victim-safe core.

Functional changes:
1. P64 0x7ABE9C consumer is NOT installed.
2. Event236 selector1 semantic state remains active.
3. F58 main+0x7D3138 is functionally overlaid only when:
   - native result is false,
   - caller LR is exactly main+0x7F46B8,
   - selector1 semantic is enabled for the same actor.
4. Paired main:
   main+0x7F2A9C
   BD001FE0 -> D503201F
   STR S0,[SP,#0x1C] -> NOP.

No char281 branch.
No force action700.
No force state0x87.
No selector8 mapping.
No raw native Event236 restoration.
No old 0x7E1404 wrapper.

Hardware gate:
- Tobi XXA
- vanilla UJ control
- Tobi victim of enemy UJ
""",
        encoding="utf-8"
    )

    (ROOT / "P65A_STATIC_AUDIT.txt").write_text(
        """P65A STATIC AUDIT

PROVEN RUNTIME INPUT:
- P64 Event236 selector1 semantic SET reaches custom actor.
- P64 0x7ABE9C semantic consumer did not log in prior player-input session.
- Vanilla UJ F58 was observed with caller LR main+0x7F46B8.

PROVEN STATIC:
- F58 entry main+0x7D3138 fingerprint inherited from P63.
- 0x7F2A9C expected BD001FE0.
- R72 multi-anchor work identifies 0x7F2A9C as strongest Switch
  structural homolog of PC SC1.70 A33C60.

P65A FUNCTIONAL HYPOTHESIS:
source-parity 0x7F2A9C prerequisite
+
selector1 semantic
+
runtime-proven player F58 caller 0x7F46B8
may restore UJ admission while awakened.

NOT FINAL PROOF until hardware result.
""",
        encoding="utf-8"
    )

    (ROOT / "R74_P65A_CHECKPOINT.md").write_text(
        """# R74 / P65A checkpoint

P64F result:
semantic selector1 state works, but 0x7ABE9C consumer was not entered.

P65A:
- preserves P50 victim safety;
- preserves Event236 semantic selector1 state;
- removes P64 consumer from active install path;
- applies 0x7F2A9C source-parity paired-main prerequisite;
- overlays F58 only at runtime-proven player caller 0x7F46B8;
- preserves native true;
- no char-specific gameplay branch.

Expected decisive log:
`[NSC:P65A] UJ_ACTIVE_GATE`
""",
        encoding="utf-8"
    )


def verify_sources():
    cpp = CPP.read_text(encoding="utf-8")
    hpp = HPP.read_text(encoding="utf-8")
    main = MAINCPP.read_text(encoding="utf-8")

    required_cpp = [
        "P65ActiveUjEligibilityBridgeHook",
        "InstallP65ActiveUjEligibilityBridge",
        "InstallP65ASourceParityActiveUjBridge",
        "[NSC:P65A] UJ_ACTIVE_GATE",
        "kP65ActivePlayerUjCallerReturnOffset = 0x7F46B8",
        "P64QuerySemanticUltimateJutsu(actor)",
    ]

    for x in required_cpp:
        if x not in cpp:
            die("source marker missing: " + x)

    if "void InstallP65ASourceParityActiveUjBridge();" not in hpp:
        die("P65 HPP declaration missing")

    if "nsc::InstallP65ASourceParityActiveUjBridge();" not in main:
        die("main does not call P65")

    if "nsc::InstallP64FUjSemanticBridge();" in main:
        die("main still calls P64F")

    # Validate P65 body specifically.
    a = cpp.find("void InstallP65ASourceParityActiveUjBridge()")
    b = cpp.find("void InstallP52APreUjProbe()", a)

    if a < 0 or b < 0:
        die("cannot isolate P65 top-level body")

    body = cpp[a:b]

    if "InstallP64SemanticUjBridge()" in body:
        die("P65 active path still installs 0x7ABE9C consumer")

    if "InstallP63UjRouterTrace()" in body:
        die("P65 would double-hook F58 with P63")

    if "InstallP65ActiveUjEligibilityBridge()" not in body:
        die("P65 active F58 bridge missing")

    # Reject explicit char281 gameplay branches.
    bad_patterns = [
        r"char_id\s*==\s*281",
        r"char_id\s*!=\s*281",
        r"char_id\s*==\s*0x119",
        r"char_id\s*!=\s*0x119",
    ]

    for pat in bad_patterns:
        if re.search(pat, cpp):
            die("character-specific gameplay branch found: " + pat)

    print("P65_SOURCE_VERIFY=PASS")


def backup_once():
    out = ROOT / "P65A_BACKUP_P64F"

    if out.exists():
        return

    out.mkdir()

    for p in [
        CPP,
        HPP,
        MAINCPP,
        DEPLOY_MAIN,
        PREP64,
        ROOT / ".github/workflows/build-subsdk9-p64f.yml",
    ]:
        if p.is_file():
            shutil.copy2(p, out / p.name)

    print("P65_BACKUP_CREATED=" + str(out))


def main():
    verify_only = "--verify-only" in sys.argv

    if not all(p.is_file() for p in [CPP, HPP, MAINCPP, DEPLOY_MAIN]):
        die("run script dari root repo Downloads")

    if not verify_only:
        backup_once()

        modify_cpp()
        modify_hpp()
        modify_maincpp()
        make_prepare_script()
        write_workflow()
        write_docs()

        patch_nso_text_word(
            DEPLOY_MAIN,
            P65_MAIN_PATCH_VA,
            P65_MAIN_EXPECTED,
            P65_MAIN_REPLACE
        )

    verify_sources()
    verify_main_patch()

    print("P65A_STATIC_VERIFY=PASS")
    print("DEPLOY_MAIN_SHA256=" + sha256(DEPLOY_MAIN.read_bytes()))

    if RESTORE_MAIN.is_file():
        print(
            "RESTORE_MAIN_SHA256="
            + sha256(RESTORE_MAIN.read_bytes())
        )


if __name__ == "__main__":
    main()
