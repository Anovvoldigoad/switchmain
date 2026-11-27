"""Synthetic CFG path joins and SHA-pinned original FileLoad evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from portlib.native_fileload_sp_cfg import trace
from portlib.native_fileload_corridor_cfg import ENTRY, END
from portlib.native_cpk_graph import MAIN_SHA256
from portlib.nso_profile import segments

def word(x):
    return x.to_bytes(4,"little")
def run(main,out):
    # SUB SP,#16; STR X1,[SP,#8]; RET: entry-relative -8.
    linear=b"".join(map(word,[0xd10043ff,0xf90007e1,0xd65f03c0]))
    r=trace(linear,0x1000)
    assert len(r["accesses"])==1
    assert r["accesses"][0]["entry_sp_relative_offsets"]==[-8]
    # A store followed by a load of the same entry-SP-relative address is a candidate only.
    pair=b"".join(map(word,[0xd10043ff,0xf90007e1,0xf94007e2,0xd65f03c0]))
    pairs=trace(pair,0x1800)["possible_stack_write_read_pairs"]
    assert len(pairs)==1 and pairs[0]["entry_sp_relative_offset"]==-8
    assert not pairs[0]["same_executed_path_proven"] and not pairs[0]["register_value_proven"]
    assert [int(s["pc"],16) for s in pairs[0]["cfg_path_witness"]]==[0x1804,0x1808]
    # A backward branch can reach a reader at a lower address after a writer.
    # SUB SP,#16; B writer; LDR; B exit; STR; B reader; RET.
    backward=b"".join(map(word,[0xd10043ff,0x14000003,0xf94007e2,
                                  0x14000003,0xf90007e1,0x17fffffd,0xd65f03c0]))
    backwards=trace(backward,0x3800)["possible_stack_write_read_pairs"]
    assert [(p["writer_pc"],p["reader_pc"]) for p in backwards]==[("0x3810","0x3808")]
    assert [int(s["pc"],16) for s in backwards[0]["cfg_path_witness"]]==[0x3810,0x3814,0x3808]
    # A branch to a lower reader without a writer-to-reader edge is not proof.
    no_backward=b"".join(map(word,[0xd10043ff,0x14000003,0xf94007e2,
                                     0x14000003,0xf90007e1,0x14000001,0xd65f03c0]))
    assert trace(no_backward,0x3900)["possible_stack_write_read_pairs"]==[]
    # Exclusive branches: writer at +8 and reader at +16 cannot share a path.
    exclusive=b"".join(map(word,[0xd10043ff,0xb4000060,0xf90007e1,
                                 0x14000003,0xf94007e2,0x14000002,
                                 0xd503201f,0xd65f03c0]))
    assert trace(exclusive,0x4000)["possible_stack_write_read_pairs"]==[]
    # Both branches reach the reader; only the writer branch witnesses a pair.
    join=b"".join(map(word,[0xd10043ff,0xb4000060,0xf90007e1,
                            0x14000002,0xd503201f,0xf94007e2,0xd65f03c0]))
    joined=trace(join,0x5000)["possible_stack_write_read_pairs"]
    assert len(joined)==1
    assert [int(s["pc"],16) for s in joined[0]["cfg_path_witness"]]==[0x5008,0x500c,0x5014]
    # Intervening same-slot store kills the first writer on the only path.
    overwrite=b"".join(map(word,[0xd10043ff,0xf90007e1,0xf90007e3,0xf94007e2,0xd65f03c0]))
    overwritten=trace(overwrite,0x7000)["possible_stack_write_read_pairs"]
    assert [(x["writer_pc"],x["reader_pc"]) for x in overwritten]==[("0x7008","0x700c")]
    assert overwritten[0]["intervening_same_slot_write_excluded_on_witness"]
    # A write to a different slot does not kill the candidate.
    other_slot=b"".join(map(word,[0xd10043ff,0xf90007e1,0xf9000be3,0xf94007e2,0xd65f03c0]))
    unaffected=trace(other_slot,0x7100)["possible_stack_write_read_pairs"]
    assert len(unaffected)==1 and unaffected[0]["writer_pc"]=="0x7104"
    # A 32-bit store at SP+12 overlaps the upper half of an earlier X store at SP+8.
    partial=b"".join(map(word,[0xd10043ff,0xf90007e1,0xb9000fe3,
                                 0xf94007e2,0xd65f03c0]))
    partial_pairs=trace(partial,0x7200)["possible_stack_write_read_pairs"]
    assert partial_pairs==[], "A partial-width overwrite must kill the X-register candidate"
    # Adjacent 32-bit write at SP+16 does not overlap the eight bytes at SP+8.
    adjacent=b"".join(map(word,[0xd10043ff,0xf90007e1,0xb90013e3,
                                  0xf94007e2,0xd65f03c0]))
    adjacent_pairs=trace(adjacent,0x7300)["possible_stack_write_read_pairs"]
    assert len(adjacent_pairs)==1 and adjacent_pairs[0]["writer_pc"]=="0x7304"
    assert adjacent_pairs[0]["intervening_overlapping_write_excluded_on_witness"]
    # Byte-width semantics must follow the transfer opcode, not the X/W
    # destination register width (e.g. LDRSW reads four bytes into X).
    narrow=b"".join(map(word,[0xd10043ff,0xf90007e1,0xb9400fe2,
                                  0xd65f03c0]))
    widths=trace(narrow,0x7400)["accesses"]
    assert [a["byte_width"] for a in widths]==[8,4]
    assert widths[1]["entry_sp_relative_byte_range"]==[-4,0]
    assert trace(narrow,0x7400)["possible_stack_write_read_pairs"]==[]
    # A byte load from the same start address cannot establish an
    # eight-byte stored value's provenance.
    byte_load=b"".join(map(word,[0xd10043ff,0xf90007e1,0x394023e2,
                                     0xd65f03c0]))
    byte_report=trace(byte_load,0x7500)
    assert [a["byte_width"] for a in byte_report["accesses"]]==[8,1]
    assert byte_report["possible_stack_write_read_pairs"]==[]
    # A store through another base may still alias the SP slot.
    unknown_alias=b"".join(map(word,[0xd10043ff,0xf90007e1,0xf9000083,
                                      0xf94007e2,0xd65f03c0]))
    assert trace(unknown_alias,0x7600)["possible_stack_write_read_pairs"]==[]
    # Path-local ADD X3,SP,#32 proves a non-SP store is disjoint.
    disjoint_alias=b"".join(map(word,[0xd10043ff,0xf90007e1,0x910083e3,
                                      0xf9000064,0xf94007e2,0xd65f03c0]))
    assert len(trace(disjoint_alias,0x7800)["possible_stack_write_read_pairs"])==1
    # ADD X3,SP,#8 aliases the original X store exactly: reject.
    overlap_alias=b"".join(map(word,[0xd10043ff,0xf90007e1,0x910023e3,
                                     0xf9000064,0xf94007e2,0xd65f03c0]))
    assert trace(overlap_alias,0x7900)["possible_stack_write_read_pairs"]==[]
    # Clobbering the alias register before the store must fail closed.
    clobbered=b"".join(map(word,[0xd10043ff,0xf90007e1,0x910083e3,
                                 0x91000003,0xf9000064,0xf94007e2,0xd65f03c0]))
    assert trace(clobbered,0x7a00)["possible_stack_write_read_pairs"]==[]
    # SP-derived pointer provenance survives a MOV and ADD immediate chain.
    # ADD X3,SP,#32; MOV X4,X3; ADD X4,X4,#16; STR X5,[X4].
    chained=b"".join(map(word,[0xd10043ff,0xf90007e1,0x910083e3,
                                 0xaa0303e4,0x91004084,0xf9000085,
                                 0xf94007e2,0xd65f03c0]))
    assert len(trace(chained,0x7b00)["possible_stack_write_read_pairs"])==1
    # SUB X4,X3,#24 aliases the original slot at SP+8.
    subtract=b"".join(map(word,[0xd10043ff,0xf90007e1,0x910083e3,
                                  0xd1006064,0xf9000085,0xf94007e2,
                                  0xd65f03c0]))
    assert trace(subtract,0x7c00)["possible_stack_write_read_pairs"]==[]
    # A redefinition of the source before MOV must not preserve provenance.
    chain_killed=b"".join(map(word,[0xd10043ff,0xf90007e1,0x910083e3,
                                      0x91000003,0xaa0303e4,0xf9000085,
                                      0xf94007e2,0xd65f03c0]))
    assert trace(chain_killed,0x7d00)["possible_stack_write_read_pairs"]==[]
    # Alias defined before writer: disjoint, overlapping, and clobbered.
    prior_disjoint=b"".join(map(word,[0xd10043ff,0x910083e3,0xf90007e1,0xf9000064,0xf94007e2,0xd65f03c0]))
    assert len(trace(prior_disjoint,0x7e00)["possible_stack_write_read_pairs"])==1
    prior_overlap=b"".join(map(word,[0xd10043ff,0x910023e3,0xf90007e1,0xf9000064,0xf94007e2,0xd65f03c0]))
    assert trace(prior_overlap,0x7f00)["possible_stack_write_read_pairs"]==[]
    prior_clobber=b"".join(map(word,[0xd10043ff,0x910083e3,0x91000003,0xf90007e1,0xf9000064,0xf94007e2,0xd65f03c0]))
    assert trace(prior_clobber,0x8000)["possible_stack_write_read_pairs"]==[]
    # A 32-bit register write clears the corresponding X register's
    # provenance, including aliases created before the stack writer.
    # MOV W3,W0 is ORR W3,WZR,W0; its architectural result zero-extends X3.
    w_clobber=b"".join(map(word,[0xd10043ff,0x910083e3,0xf90007e1,
                                  0x2a0003e3,0xf9000064,0xf94007e2,0xd65f03c0]))
    assert trace(w_clobber,0x8100)["possible_stack_write_read_pairs"]==[]
    # Same case with alias created after writer; no stale X3 survives.
    late_w_clobber=b"".join(map(word,[0xd10043ff,0xf90007e1,0x910083e3,
                                       0x2a0003e3,0xf9000064,0xf94007e2,0xd65f03c0]))
    assert trace(late_w_clobber,0x8200)["possible_stack_write_read_pairs"]==[]
    # X-register overwrite still invalidates, and a W write to a
    # different register must leave the disjoint X3 alias intact.
    unrelated_w=b"".join(map(word,[0xd10043ff,0x910083e3,0xf90007e1,
                                    0x2a0003e5,0xf9000064,0xf94007e2,0xd65f03c0]))
    assert len(trace(unrelated_w,0x8300)["possible_stack_write_read_pairs"])==1
    # A load through another base does not overwrite stack memory.
    unrelated_read=b"".join(map(word,[0xd10043ff,0xf90007e1,0xf9400083,
                                        0xf94007e2,0xd65f03c0]))
    assert len(trace(unrelated_read,0x7700)["possible_stack_write_read_pairs"])==1
    # Register-offset addresses are not displacement-only SP addresses.
    # Words assembled with clang 17 --target=aarch64-linux-gnu:
    # STR X1,[SP,X2]; LDR X3,[SP,X2]; LDR X4,[SP,X5,LSL #3].
    indexed=b"".join(map(word,[0xd10043ff,0xf8226be1,0xf8626be3,0xd65f03c0]))
    indexed_report=trace(indexed,0x8400)
    indexed_sp=[a for a in indexed_report["accesses"] if a["pc"] in ("0x8404","0x8408")]
    assert [a["index_register"] for a in indexed_sp]==["x2","x2"]
    assert all(a["indexed_address_unresolved"] and a["path_ambiguous"] for a in indexed_sp)
    assert all(a["entry_sp_relative_byte_range"] is None and
               a["entry_sp_relative_offsets"]==[] for a in indexed_sp)
    assert indexed_report["possible_stack_write_read_pairs"]==[]
    assert [a["index_register"] for a in indexed_report["indexed_memory_operands"]]==["x2","x2"]
    shifted=b"".join(map(word,[0xd10043ff,0xf8657be4,0xd65f03c0]))
    shifted_report=trace(shifted,0x8500)
    assert shifted_report["indexed_memory_operands"][0]["index_register"]=="x5"
    assert shifted_report["indexed_memory_operands"][0]["effective_address_resolved"] is False
    # Reaching-definition evidence distinguishes register origins from values.
    origin_chain=b"".join(map(word,[0xb0021b88,0xf9453108,0xb9807058,
                                     0xf8787913,0xd65f03c0]))
    chain_report=trace(origin_chain,0x8700)
    chain_row=chain_report["indexed_register_origins"][0]
    chain_state=chain_row["state_observations"][0]
    assert chain_state["base"]["single_reaching_definition"]
    base_def=chain_state["base"]["reaching_definitions"][0]
    assert (base_def["pc"],base_def["mnemonic"])==("0x8704","ldr")
    assert base_def["source_register_origins"]["x8"][0]["pc"]=="0x8700"
    index_def=chain_state["index"]["reaching_definitions"][0]
    assert (index_def["pc"],index_def["mnemonic"])==("0x8708","ldrsw")
    assert index_def["source_register_origins"]["x2"][0]["kind"]=="entry_value"
    assert not chain_state["base"]["numeric_value_proven"]
    assert not chain_state["index"]["numeric_value_proven"]
    # No register-preservation convention is assumed across an opaque call.
    call_origin=b"".join(map(word,[0xaa0303f8,0x94000001,0xf8786904,0xd65f03c0]))
    call_row=trace(call_origin,0x8800)["indexed_register_origins"][0]
    call_index=call_row["state_observations"][0]["index"]
    assert call_index["call_clobbered"]
    assert call_index["reaching_definitions"][0]["kind"]=="call_clobber"
    # X19 is conventionally callee-saved in AAPCS64, but this target ABI is
    # not established; do not carry it across an opaque native call.
    callee_saved_origin=b"".join(map(word,[0xaa0303f3,0x94000001,0xf8736904,0xd65f03c0]))
    saved_row=trace(callee_saved_origin,0x8c00)["indexed_register_origins"][0]
    saved_index=saved_row["state_observations"][0]["index"]
    assert saved_index["call_clobbered"]
    assert saved_index["reaching_definitions"][0]["kind"]=="call_clobber"
    # A branch merge keeps both reaching definitions instead of selecting one.
    branch_origin=b"".join(map(word,[0xb4000060,0xaa0103ea,0x14000002,
                                     0xaa0203ea,0xf86a6904,0xd65f03c0]))
    branch_row=trace(branch_origin,0x8900)["indexed_register_origins"][0]
    branch_index=branch_row["state_observations"][0]["index"]
    assert not branch_index["single_reaching_definition"]
    assert [x["pc"] for x in branch_index["reaching_definitions"]]==["0x8904","0x890c"]
    # Wn writes replace the canonical Xn reaching definition (zero-extension).
    w_origin=b"".join(map(word,[0xaa0303f8,0x2a0403f8,0xf8786904,0xd65f03c0]))
    w_index=trace(w_origin,0x8a00)["indexed_register_origins"][0]["state_observations"][0]["index"]
    assert [x["pc"] for x in w_index["reaching_definitions"]]==["0x8a04"]
    assert w_index["reaching_definitions"][0]["operands"]=="w24, w4"
    # SP-derived base provenance carries the actual path SP delta at its use.
    sp_origin=b"".join(map(word,[0xd10043ff,0x910083e3,0xf8656864,0xd65f03c0]))
    sp_row=trace(sp_origin,0x8b00)["indexed_register_origins"][0]
    sp_state=sp_row["state_observations"][0]
    assert sp_state["sp_delta"]==-16
    sp_def=sp_state["base"]["reaching_definitions"][0]
    assert sp_def["source_register_origins"]["sp"][0]["pc"]=="0x8b00"
    # An indexed store through a known SP-derived base can alias any slot:
    # X3=SP+32 does not prove [X3,X5] is disjoint from SP+8.
    alias_index=b"".join(map(word,[0xd10043ff,0xf90007e1,0x910083e3,
                                    0xf8256864,0xf94007e2,0xd65f03c0]))
    assert trace(alias_index,0x8600)["possible_stack_write_read_pairs"]==[]
    # A different load displacement must not be matched.
    different=b"".join(map(word,[0xd10043ff,0xf90007e1,0xf9400be2,0xd65f03c0]))
    assert trace(different,0x1800)["possible_stack_write_read_pairs"]==[]
    # CBZ X0,+12 bypasses ADD SP,#16, creating two distinct SP offsets.
    fork=b"".join(map(word,[0xd10043ff,0xb4000060,0x910043ff,
                           0x14000002,0xd503201f,0xf90007e1,0xd65f03c0]))
    # At 0x2004 CBZ +12 goes to 0x2010; branch at 0x200c goes to 0x2014.
    # Both paths meet at 0x2014 after the NOP.
    r=trace(fork,0x2000)
    assert len(r["accesses"])==1
    assert r["accesses"][0]["path_ambiguous"]
    assert r["accesses"][0]["observed_sp_deltas"]==[-16,0]
    assert r["possible_stack_write_read_pairs"]==[]
    # A call is a hard evidence barrier, not assumed to preserve SP.
    call=b"".join(map(word,[0xd10043ff,0x94000002,0xf90007e1,0xd65f03c0]))
    r=trace(call,0x3000)
    assert r["call_barriers"]==["0x3004"]
    assert r["accesses"][0]["unknown_path"]
    # Raw callsite reaching definitions are not decoded into ABI arguments.
    direct_regs = trace(b"".join(map(word,[0xaa0103e0,0xaa0203f3,
                                           0x94000001,0xd65f03c0])),0x6200)
    direct_rows = direct_regs["callsite_register_origins"]
    assert len(direct_rows)==1
    direct_row = direct_rows[0]
    assert direct_row["pc"]=="0x6208"
    assert direct_row["direct_targets"]==["0x620c"]
    x0_defs = direct_row["register_origins"]["x0"]["reaching_definitions"]
    assert [x["pc"] for x in x0_defs]==["0x6200"]
    assert x0_defs[0]["source_register_origins"]["x1"][0]["kind"]=="entry_value"
    assert direct_row["register_origins"]["x19"]["reaching_definitions"][0]["pc"]=="0x6204"
    assert not direct_row["abi_register_semantics_assumed"]
    assert not direct_row["numeric_register_values_proven"]
    # Two exclusive definitions merge at the callsite; neither wins by ordering.
    merged_regs = trace(b"".join(map(word,[0xb4000060,0xaa0103e0,
                                            0x14000002,0xaa0303e0,
                                            0x94000001,0xd65f03c0])),0x6300)
    merged_row = merged_regs["callsite_register_origins"][0]
    merged_x0 = merged_row["register_origins"]["x0"]
    assert not merged_x0["single_reaching_definition"]
    assert [x["pc"] for x in merged_x0["reaching_definitions"]]==["0x6304","0x630c"]
    # An earlier opaque call clobbers even x19; do not import AAPCS64 preservation.
    barrier_regs = trace(b"".join(map(word,[0xaa0203f3,0x94000001,
                                             0x94000001,0xd65f03c0])),0x6400)
    second_call = next(x for x in barrier_regs["callsite_register_origins"]
                       if x["pc"]=="0x6408")
    x19_after_call = second_call["register_origins"]["x19"]
    assert x19_after_call["call_clobbered"]
    assert x19_after_call["reaching_definitions"]==[
        {"kind":"call_clobber","pc":"0x6404"}
    ]
    # No call instruction means no callsite row.
    assert trace(b"".join(map(word,[0x14000001,0xd65f03c0])),0x6600)[
        "callsite_register_origins"]==[]
    # ARMv8.3 BLRAA X9,X10: authenticated indirect call, not fallthrough.
    # Word assembled using clang --target=aarch64-linux-gnu -march=armv8.3-a+pauth.
    pac_call=b"".join(map(word,[0xd10043ff,0xf90007e1,0xd73f092a,
                                 0xf94007e2,0xd65f03c0]))
    pac_report=trace(pac_call,0x6100)
    assert pac_report["call_barriers"]==["0x6108"]
    assert pac_report["possible_stack_write_read_pairs"]==[]
    assert pac_report["accesses"][1]["unknown_path"]
    # A call between writer and reader is opaque; no cross-call witness.
    opaque=b"".join(map(word,[0xd10043ff,0xf90007e1,0x94000002,
                              0xf94007e2,0xd65f03c0]))
    assert trace(opaque,0x6000)["possible_stack_write_read_pairs"]==[]
    for bad in (linear[:-1],):
        try: trace(bad,0x1000)
        except ValueError: pass
        else: raise AssertionError("Accepted partial ARM64 word")
    try: trace(linear,0x1000,max_states=1)
    except ValueError: pass
    else: raise AssertionError("Accepted state-budget overflow")
    raw=main.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==MAIN_SHA256
    va,text,_=segments(raw)[0]
    assert va==0 and END<=len(text)
    window=text[ENTRY:END]
    report=trace(window,ENTRY)
    report["original_main_sha256"]=MAIN_SHA256
    report["window_sha256"]=hashlib.sha256(window).hexdigest()
    assert not report["consumer_abi_proven"] and not report["stack_ownership_proven"]
    origin_rows={x["pc"]:x for x in report["indexed_register_origins"]}
    assert len(origin_rows)==5
    first=origin_rows["0x116f430"]["state_observations"]
    assert len(first)==1 and first[0]["sp_delta"]==-704
    first_base=first[0]["base"]["reaching_definitions"]
    first_index=first[0]["index"]["reaching_definitions"]
    assert [x["pc"] for x in first_base]==["0x116f424"]
    assert first_base[0]["source_register_origins"]["x8"][0]["pc"]=="0x116f418"
    assert [x["pc"] for x in first_index]==["0x116f41c"]
    assert first_index[0]["mnemonic"]=="ldrsw"
    assert first_index[0]["source_register_origins"]["x2"][0]["kind"]=="entry_value"
    assert all(not side["numeric_value_proven"]
               for row in report["indexed_register_origins"]
               for state in row["state_observations"]
               for side in (state["base"],state["index"]))
    call_rows = report["callsite_register_origins"]
    assert report["callsite_register_origin_state_count"] == len(call_rows)
    for site, x0_definition, x1_definition in (
        ("0x116f520","0x116f51c","0x116f518"),
        ("0x116f5c0","0x116f5bc","0x116f5b8")
    ):
        matching = [row for row in call_rows if row["pc"] == site]
        assert matching and all(row["direct_targets"] == ["0x120661c"]
                                for row in matching)
        assert any(any(definition.get("pc") == x0_definition
                       for definition in row["register_origins"]["x0"]["reaching_definitions"])
                   for row in matching)
        assert any(any(definition.get("pc") == x1_definition
                       for definition in row["register_origins"]["x1"]["reaching_definitions"])
                   for row in matching)
        assert all(not row["abi_register_semantics_assumed"]
                   and not row["numeric_register_values_proven"]
                   for row in matching)
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileload_sp_cfg.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PINNED_FILELOAD_SP_CFG_PASS",report["reachable_states"],len(report["accesses"]),"NO_CONSUMER_ABI")
    print("PINNED_FILELOAD_REGISTER_ORIGINS_PASS",len(report["indexed_register_origins"]),"NO_NUMERIC_VALUES_OR_ABI")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    run(a.main,a.output)
