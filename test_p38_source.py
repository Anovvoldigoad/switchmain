#!/usr/bin/env python3
"""P38 static guard tests. Native compilation is checked separately by Actions."""
from pathlib import Path
import re
import unittest

BRIDGE = Path("overlay/source/program/nsc_cpk_bridge.cpp").read_text(encoding="utf-8")
MAIN = Path("overlay/source/program/main.cpp").read_text(encoding="utf-8")


class P38StaticGuards(unittest.TestCase):
    def test_keeps_proven_loader_entrypoint(self):
        self.assertIn("nsc::InstallP32Trace();", MAIN)
        self.assertIn('kModCpkPath = "sim:data/moddingapi/Tobi_Switch.cpk"', BRIDGE)
        self.assertIn("CpkBindHook::InstallAtOffset(kCpkBindOffset)", BRIDGE)

    def test_arms_only_after_actual_mtob_char281(self):
        self.assertIn('id == kFirstCustomCharId && BoundedEqual(code, "mtob")', BRIDGE)
        self.assertIn('g_p38_armed.exchange(1u', BRIDGE)

    def test_old_r266_hardcoded_model_id_not_ported(self):
        self.assertNotIn("identity38 == 46u", BRIDGE)
        self.assertIn('original_model_id_46_filter_removed=1', BRIDGE)

    def test_three_read_only_hooks_call_orig(self):
        for key in ("P38ModelChildCreateHook", "P38RegBridgeHook", "P38RenderProducerHook"):
            self.assertEqual(BRIDGE.count(f"HOOK_DEFINE_TRAMPOLINE({key})"), 1)
            block = BRIDGE.split(f"HOOK_DEFINE_TRAMPOLINE({key})", 1)[1].split("\n};", 1)[0]
            self.assertEqual(block.count("Orig("), 1, key)
            self.assertNotRegex(block, r"\breturn\s+(0|1)\s*;", key)

    def test_fingerprint_all_or_nothing_guard(self):
        self.assertIn("if (!child || !bridge || !producer)", BRIDGE)
        self.assertIn('reason=fingerprint_mismatch hooks=0', BRIDGE)
        self.assertIn("const bool render_probe = cpk && trace && InstallP38RenderRegistrationProbe();", BRIDGE)
        guard, installs = BRIDGE.split('reason=fingerprint_mismatch hooks=0', 1)[1].split("bool InstallCpkBridge()", 1)[0].split("return false;", 1)
        self.assertTrue(all(x in installs for x in (
            "P38ModelChildCreateHook::InstallAtOffset",
            "P38RegBridgeHook::InstallAtOffset",
            "P38RenderProducerHook::InstallAtOffset"
        )))

    def test_signature_offsets_from_historical_r266(self):
        self.assertIn("kP38ModelChildCreateOffset = 0x6ECEE8;", BRIDGE)
        self.assertIn("kP38RegBridgeOffset        = 0x6ED110;", BRIDGE)
        self.assertIn("kP38RenderProducerOffset   = 0x594D8;", BRIDGE)

    def test_trace_budget_and_no_gameplay_override(self):
        self.assertIn("if (seq >= 512u) return;", BRIDGE)
        self.assertGreaterEqual(BRIDGE.count("if (seq < 512u)"), 2)
        for name in ("P38ModelChildCreateHook", "P38RegBridgeHook", "P38RenderProducerHook"):
            block = BRIDGE.split(f"HOOK_DEFINE_TRAMPOLINE({name})", 1)[1].split("\n};", 1)[0]
            self.assertNotIn("RandomAccessPatcher", block)
            self.assertNotIn("Write<", block)


if __name__ == "__main__":
    unittest.main()
