"""Original native FileOpen eight-callee corridor: two indirect dispatch objects.

At native function candidates 0x116B6E8 and 0x116B3F0, trace the base X8
that supplies indirect BR target registers. Source is strictly original
v1.70 SHA-pinned main. A syntactic X8 writer may disclose a probable virtual
method table load, but without instance class/heap/ownership proof no
concrete resolved function address, original ABI, or safe lifecycle follows.
"""
import hashlib
from .native_cpk_graph import MAIN_SHA256
from .native_fileopen_tail_abi_candidates import inspect as inspect_arguments,_reached
from .native_fileopen_callees import _decode_window,_predecessors,_writer_origins
from .nso_profile import segments

# Each address is already evidenced as reachable from the corresponding
# original native FileOpen 0x115EBD8 eight-call tail.
DISPATCHES=(
    {"target":0x116B6E8,"load":0x116B71C,"branch":0x116B724,
     "dest_reg":"x1","offset":0xC0},
    {"target":0x116B3F0,"load":0x116B424,"branch":0x116B430,
     "dest_reg":"x2","offset":0x58},
)
WINDOW=0x140

def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError("Only exact original Switch 1.70 main SHA256 is accepted")
    parent=inspect_arguments(nso)
    va,text,_=segments(nso)[0]
    if va!=0:
        raise ValueError("Unexpected original code RVA base")
    sources={int(c["callee_target"],16):c for c in parent["callsite_provenance"]}
    observations=[]
    for site in DISPATCHES:
        entry,load,branch=site["target"],site["load"],site["branch"]
        decoded,graph=_decode_window(text,entry,entry+WINDOW)
        reached,escaped=_reached(graph,entry,entry,entry+WINDOW)
        reachable={pc for pc in reached if pc in graph}
        if not {entry,load,branch}<=reachable:
            raise ValueError("Original native dispatch corridor not reachable")
        ins=decoded[load]
        br=decoded[branch]
        expected="ldr "+site["dest_reg"]+", [x8, #"+hex(site["offset"])+"]"
        if (ins.mnemonic+" "+ins.op_str)!=expected:
            raise ValueError("Original indirect dispatch offset/operand mismatch")
        if (br.mnemonic+" "+br.op_str)!="br "+site["dest_reg"]:
            raise ValueError("Original native BR register mismatch")
        if entry not in sources:
            raise ValueError("Dispatch target not in original eight-callee call graph")
        from_source=sources[entry]
        witness=from_source.get("native_indirect_br_register_sources",[])
        if not any(x.get("at")==hex(branch) and
                   x.get("branch_register")==site["dest_reg"] for x in witness):
            raise ValueError("Original predecessor BR witness differs")
        pred=_predecessors(graph,reachable,entry,entry+WINDOW)
        x8=_writer_origins(pred,decoded,load,"x8",entry=entry)
        x0=_writer_origins(pred,decoded,load,"x0",entry=entry)
        # Resolve x0 prior to a candidate vtable load site. A prior BL is
        # regarded as an unknown caller-saved clobber, not object ownership.
        derefs=[]
        for writer in x8["possible_immediate_reaching_writers"]:
            at=int(writer["at"],16)
            inst=decoded[at]
            dependent=None
            if (inst.mnemonic=="ldr" and inst.op_str=="x8, [x0]"):
                dependent=_writer_origins(pred,decoded,at,"x0",entry=entry)
            derefs.append({
                "writer":writer,
                "original_X8_writer_is_LDR_X8_object_first_word":
                    inst.mnemonic=="ldr" and inst.op_str=="x8, [x0]",
                "origin_of_X0_before_X8_object_first_word":dependent,
                "heap_instance_class_identity_proven":False
            })
        observed=[]
        for at in range(entry,branch+4,4):
            instruction=decoded.get(at)
            observed.append({
                "at":hex(at),
                "word_le":text[at:at+4].hex(),
                "instruction":(instruction.mnemonic+" "+instruction.op_str).strip()
                    if instruction else "UNDECODED"
            })
        observations.append({
            "eight_callee_direct_target":hex(entry),
            "original_load_site":hex(load),
            "original_load_word_le":text[load:load+4].hex(),
            "original_load_instruction":expected,
            "original_br_site":hex(branch),
            "original_br_word_le":text[branch:branch+4].hex(),
            "original_br_instruction":"br "+site["dest_reg"],
            "indirect_method_field_offset":site["offset"],
            "X8_nearest_syntactic_original_writers":x8,
            "X0_nearest_syntactic_original_writers_at_dispatch":x0,
            "X8_possible_object_first_word_dereference_sources":derefs,
            "original_instruction_transcript":observed,
            "out_of_analysis_window_path_targets":escaped,
            "callee_callsite":from_source["site"],
            "actual_target_code_pointer_value_observed":False,
            "actual_native_class_or_vtable_authenticated":False,
            "real_CRI_interface_dispatch_proven":False,
            "runtime_constructor_destructor_or_async_owner_proven":False,
        })
    return {
        "status":"ORIGINAL_170_NATIVE_FILEOPEN_TWO_X8_DISPATCH_OBJECT_ORIGINS_STATIC",
        "original_main_sha256":digest,
        "original_dispatch_corridor_count":len(observations),
        "dispatch_origins":observations,
        "indirect_loads_are_not_resolved_runtime_function_addresses":True,
        "no_unverified_original_main_patches":True,
        "actual_runtime_object_ownership_proven":False,
        "actual_native_archive_priority_or_unbind_proven":False,
        "actual_CRI_lock_unlock_async_completion_proven":False,
        "hook_installation_safe_proven":False,
        "native_hook_added":False,
        "gameplay_verified":False,
        "full_moddingapi":False,
        "ready_for_gameplay_test":False,
        "emulator_tested":False,
    }
