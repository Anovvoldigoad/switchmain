"""Real original ARM64 status5 call/data paths and helper body transcript."""
import argparse,json,struct,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/"tools"))
from portlib.native_fileload_status import (
    inspect,STATUS_CALL_WITNESSES,STATUS_HELPER,MAIN_SHA256,
    SERVICE_WINDOW,SERVICE_ENTRYPOINTS,SERVICE_TARGET_WINDOW,SERVICE_TARGETS,
    SERVICE_REQUIRED_TARGET_EDGES,_service_words,_bounded_trace
)


def synthetic_service_window():
    raw=struct.pack("<II",0xD503201F,0xD65F03C0)
    rows=_service_words(raw,0,len(raw))
    assert [(x["mnemonic"],x["operands"]) for x in rows]==[
        ("nop",""),("ret","")]
    for start,end in ((1,8),(0,9),(8,4),(-4,4),(0,12)):
        try:_service_words(raw,start,end)
        except ValueError:pass
        else:raise AssertionError(("Invalid service window accepted",start,end))



def synthetic_bounded_trace():
    # B skips an unreachable NOP and reaches MOV/RET.
    code=struct.pack("<IIII",0x14000002,0xD503201F,0xAA0003E0,0xD65F03C0)
    row=_bounded_trace(code,0,len(code),0)
    assert row["reachable_addresses"]==["0x0","0x8","0xc"]
    assert row["returns"]==["0xc"]
    assert not row["function_boundary_proven"]

    # CBZ has both a taken edge and a fallthrough edge.
    conditional=struct.pack("<IIII",0x34000040,0xD503201F,0xD503201F,0xD65F03C0)
    row=_bounded_trace(conditional,0,len(conditional),0)
    assert row["reachable_addresses"]==["0x0","0x4","0x8","0xc"]
    assert any(x["target"]=="0x8" for x in row["direct_branches"])

    # BL records a direct call but does not recursively claim the callee.
    call=struct.pack("<III",0x94000002,0xD65F03C0,0xD65F03C0)
    row=_bounded_trace(call,0,len(call),0)
    assert row["reachable_addresses"]==["0x0","0x4"]
    assert row["direct_calls"]==[{"at":"0x0","target":"0x8","kind":"BL"}]

    # Indirect BR is a terminal unresolved transfer; it is never guessed.
    indirect=struct.pack("<II",0xD61F0100,0xD65F03C0)
    row=_bounded_trace(indirect,0,len(indirect),0)
    assert row["reachable_addresses"]==["0x0"]
    assert row["indirect_branches"][0]["mnemonic"]=="br"

    # Direct branch outside the bounded window is retained as an unresolved edge.
    outside=struct.pack("<I",0x14000040)
    row=_bounded_trace(outside,0,len(outside),0)
    assert row["out_of_window_edges"]==[
        {"from":"0x0","target":"0x100","kind":"B"}
    ]

    # A valid shorter window ends after MOV and records its fallthrough as external.
    bounded=_bounded_trace(code,0,12,0)
    assert bounded["reachable_addresses"]==["0x0","0x8"]
    assert bounded["out_of_window_edges"]==[
        {"from":"0x8","target":"0xc","kind":"fallthrough"}
    ]

    # Budget and malformed geometry are explicit, never silently truncated.
    row=_bounded_trace(code,0,len(code),0,max_instructions=1)
    assert row["budget_exhausted"]
    for start,end,entry in ((1,8,1),(0,9,0),(8,4,8),(-4,4,0),(0,20,0),(0,4,4)):
        try:_bounded_trace(code,start,end,entry)
        except ValueError:pass
        else:raise AssertionError(("Invalid bounded trace accepted",start,end,entry))


def run(main,out):
    synthetic_service_window()
    synthetic_bounded_trace()
    raw=main.read_bytes()
    report=inspect(raw)
    assert report["main_sha256"]==MAIN_SHA256
    assert len(report["verified_status_argument_and_callsite_words"])==len(STATUS_CALL_WITNESSES)
    assert report["status_setter_candidate_target"]==f"0x{STATUS_HELPER:x}"
    assert report["second_sequence_read_error_field_offset"]==0x1d8
    assert report["second_sequence_compares_error_field_to"]==1
    assert not report["status_helper_object_field_write_verified"]
    assert not report["file_open_failed_path_to_status_helper_verified"]
    assert not report["ABI_safe_new_hook_proven"]
    assert not report["gameplay_verified"]
    service=report["service_code_window"]
    service_by_at={int(x["at"],16):x for x in service["instructions"]}
    for caller,kind,target in SERVICE_REQUIRED_TARGET_EDGES:
        row=service_by_at[caller]
        assert row["direct_branch_kind"]==kind
        assert row["direct_branch_target"]==hex(target)
    assert service["start"]==hex(SERVICE_WINDOW[0])
    assert service["end_exclusive"]==hex(SERVICE_WINDOW[1])
    assert service["window_bytes"]==SERVICE_WINDOW[1]-SERVICE_WINDOW[0]
    assert service["bounded_window_not_function_extent"]
    assert [int(x["at"],16) for x in service["entrypoints"]]==list(SERVICE_ENTRYPOINTS)
    assert len(service["instructions"])==service["window_bytes"]//4
    assert all(len(x["word_le"])==8 for x in service["instructions"])
    assert not service["lock_unlock_semantics_verified"]
    assert not service["service_function_boundaries_verified"]
    target_window=report["service_target_code_window"]
    assert target_window["start"]==hex(SERVICE_TARGET_WINDOW[0])
    assert target_window["end_exclusive"]==hex(SERVICE_TARGET_WINDOW[1])
    assert target_window["window_bytes"]==SERVICE_TARGET_WINDOW[1]-SERVICE_TARGET_WINDOW[0]
    assert target_window["bounded_window_not_function_extent"]
    assert len(target_window["instructions"])==target_window["window_bytes"]//4
    assert [int(x["at"],16) for x in target_window["entrypoints"]]==list(SERVICE_TARGETS)
    assert len(target_window["bounded_traces"])==len(SERVICE_TARGETS)
    for trace in target_window["bounded_traces"]:
        assert trace["reachable_instruction_count"]>0
        assert not trace["budget_exhausted"]
        assert not trace["function_boundary_proven"]
        assert all(SERVICE_TARGET_WINDOW[0]<=int(x,16)<SERVICE_TARGET_WINDOW[1]
                   for x in trace["reachable_addresses"])
    target_edges=report["service_target_incoming_direct_edges"]
    for caller,kind,target in SERVICE_REQUIRED_TARGET_EDGES:
        assert any(x["caller"]==hex(caller) and x["kind"]==kind
                   for x in target_edges[hex(target)])
    for key in ("service_target_semantics_verified",
                "service_target_lock_unlock_implementation_verified",
                "service_target_function_boundaries_verified",
                "service_target_ownership_lifecycle_verified",
                "service_target_async_completion_verified",
                "service_semantics_verified",
                "mutex_lock_unlock_implementation_verified",
                "service_function_boundaries_verified",
                "service_runtime_binding_verified"):
        assert report[key] is False
    with tempfile.TemporaryDirectory() as td:
        d=Path(td);src=d/"main";src.write_bytes(raw)
        cmd=[sys.executable,str(R/"tools/audit_native_fileload_status.py"),
             "--main",str(src),"--output",str(d/"ok")]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((d/"ok/native_fileload_status.json").read_text())==report
        altered=bytearray(raw);altered[255]^=1;src.write_bytes(altered)
        cmd[-1]=str(d/"bad")
        assert subprocess.run(cmd,capture_output=True).returncode
        assert not (d/"bad").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileload_status.json").write_text(json.dumps(report,indent=2)+"\n")
    print("NATIVE_STATUS5_CALLS_PASS",report["verified_status_argument_and_callsite_words"],
          "no gameplay or API hook")
    print("PINNED_FILELOAD_STATUS_SERVICE_WINDOW_PASS",
          service["start"],service["end_exclusive"],service["window_sha256"],
          "ENTRYPOINTS",[(x["at"],x["mnemonic"],x["operands"])
                         for x in service["entrypoints"]],
          "NO_LOCK_UNLOCK_SEMANTICS")
    target_window=report["service_target_code_window"]
    print("PINNED_FILELOAD_STATUS_TARGET_BODIES_PASS",
          target_window["start"],target_window["end_exclusive"],
          target_window["window_sha256"],"TRACES",
          [(x["entry"],x["reachable_instruction_count"],len(x["direct_calls"]),
            len(x["indirect_calls"]),len(x["returns"]),len(x["out_of_window_edges"]))
           for x in target_window["bounded_traces"]],"NO_FUNCTION_OR_LOCK_CLAIM")
    for target,edges in report["service_target_incoming_direct_edges"].items():
        print("PINNED_FILELOAD_SERVICE_TARGET_XREFS",target,edges)
    for group in ("helper_code","file_open_return_handling_near_call"):
        for ins in report[group]["instructions"]:
            print("NATIVE_STATUS_PATH_WORD",group,ins["at"],ins["mnemonic"],ins["operands"])


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();run(a.main,a.output)
