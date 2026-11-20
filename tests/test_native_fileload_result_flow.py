"""CI: bounded original FileOpen branch -> native status setter arguments."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "tools"))
from portlib.native_fileload_result_flow import inspect, _walk, MAIN_SHA256


def test_small_graph():
    # A reachable status site is not an unconditional transition.
    graph = {
        0: [("conditional", 4), ("fallthrough", 8)],
        4: [("call", 200), ("fallthrough_after_call", 12)],
        8: [("return_or_indirect_terminator", None)],
    }
    flow = _walk(graph, 0, {12, 16}, 0, 20)
    assert flow["paths"][12] == [0, 4, 12]
    assert flow["paths"][16] is None
    assert flow["visited"] == 4
    assert any(x["kind"] == "return_or_indirect_terminator" for x in flow["exits"])
    loop = {0: [("fallthrough", 4)], 4: [("unconditional", 0)]}
    flow = _walk(loop, 0, {8}, 0, 12)
    assert flow["visited"] == 2 and flow["paths"][8] is None


def run(main, out):
    test_small_graph()
    raw = main.read_bytes()
    proof = inspect(raw)
    assert proof["original_main_sha256"] == MAIN_SHA256
    assert proof["status5_first_reachable_syntactically"] is True
    assert proof["status5_second_reachable_syntactically"] is False
    assert proof["first_status5_shortest_syntactic_path"][0] == "0x116f4d8"
    assert proof["first_status5_shortest_syntactic_path"][-1] == "0x116f520"
    assert len(proof["native_status_helper_original_body"]["exact_word_witnesses"]) == 10
    for key in ("original_CRI_FileOpen_returned_zero_in_runtime",
                "zero_result_to_status5_unconditional_execution_proven",
                "real_lock_and_async_lifecycle_proven",
                "archive_precedence_and_unbind_proven",
                "safe_hook_or_trampoline_ABI_proven",
                "native_hook_written", "gameplay_verified", "full_moddingapi"):
        assert proof[key] is False
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        src = root / "main"
        src.write_bytes(raw)
        cmd = [sys.executable, str(R / "tools/audit_native_fileload_result_flow.py"),
               "--main", str(src), "--output", str(root / "ok")]
        subprocess.run(cmd, check=True, capture_output=True)
        assert json.loads((root / "ok/native_fileload_result_flow.json").read_text()) == proof
        damaged = bytearray(raw)
        damaged[255] ^= 1
        src.write_bytes(damaged)
        cmd[-1] = str(root / "rejected")
        assert subprocess.run(cmd, capture_output=True).returncode != 0
        assert not (root / "rejected").exists()
    out.mkdir(parents=True, exist_ok=True)
    (out / "native_fileload_result_flow.json").write_text(
        json.dumps(proof, indent=2) + "\n"
    )
    print("FILELOAD_ORIGINAL_RESULT_FLOW_PASS",
          "zero_path", len(proof["first_status5_shortest_syntactic_path"]),
          "decisions", len(proof["first_status5_path_conditional_decisions"]),
          "NO_REAL_CRI_FAILURE_OR_GAMEPLAY")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--main", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    run(args.main, args.output)
