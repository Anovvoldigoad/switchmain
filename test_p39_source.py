#!/usr/bin/env python3
"""P39 static invariants; native compiler is exercised by GitHub Actions."""
from pathlib import Path
import unittest

SRC = Path("overlay/source/program/nsc_cpk_bridge.cpp").read_text(encoding="utf-8")
MAIN = Path("overlay/source/program/main.cpp").read_text(encoding="utf-8")

class P39SourceTests(unittest.TestCase):
    def test_loader_kept(self):
        self.assertIn("nsc::InstallP32Trace();", MAIN)
        self.assertIn("const bool cpk = InstallCpkBridge();", SRC)
        self.assertIn("const bool trace = InstallTraceHooks();", SRC)

    def test_original_renderer_checkpoints(self):
        self.assertIn("kP39DrawOffset             = 0x54ADA0;", SRC)
        self.assertIn("kP39DrawSubmitOffset       = 0x5B3AC;", SRC)
        self.assertIn("MatchWords(kP39DrawOffset, kDrawExpected)", SRC)
        self.assertIn("MatchWords(kP39DrawSubmitOffset, kSubmitExpected)", SRC)

    def test_hooks_are_once_only_and_no_gameplay_mutation(self):
        for name in ("P39DrawHook", "P39DrawSubmitHook"):
            marker = f"HOOK_DEFINE_TRAMPOLINE({name})"
            self.assertEqual(SRC.count(marker), 1)
            block = SRC.split(marker, 1)[1].split("\n};", 1)[0]
            self.assertEqual(block.count("Orig("), 1)
            self.assertNotIn("RandomAccessPatcher", block)
            self.assertNotIn("Write<", block)

    def test_failclosed_if_either_signature_fails(self):
        self.assertIn("if (!draw || !submit)", SRC)
        self.assertIn("[NSC:P39] READY installed=0 reason=fingerprint_mismatch hooks=0", SRC)
        self.assertIn("const bool draw_probe = cpk && trace && InstallP39DrawDispatchProbe();", SRC)

    def test_marker_is_bounded_and_after_arm(self):
        self.assertIn("g_p38_armed.load(std::memory_order_relaxed)", SRC)
        self.assertGreaterEqual(SRC.count("seq < 192u"), 2)
        for marker in ("[NSC:P39] DRAW", "[NSC:P39] SUBMIT", "[NSC:P39] STATUS"):
            self.assertIn(marker, SRC)

    def test_p38_kept_and_identity46_not_forced(self):
        for name in ("P38ModelChildCreateHook", "P38RegBridgeHook", "P38RenderProducerHook"):
            self.assertIn(name, SRC)
        self.assertNotIn("identity38 == 46u", SRC)

if __name__ == "__main__":
    unittest.main()
