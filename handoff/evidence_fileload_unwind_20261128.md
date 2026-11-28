# FileLoad unwind metadata and caller coverage

Date: 2026-11-28
Branch: \`port/full-api-v170\`
Implementation parent: \`d308501da0641b7393ffeab1b9c12484b9b34c8f\`
State: IMPLEMENTED_AWAITING_CI

## Research-first primary sources

| Source | Exact ref / blob | Relevance and result |
|---|---|---|
| [NSC-ModManager latest release](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1) | Tag commit \`502c38d3ee832509f9ee3951b7d3339826538fec\`; \`XfbinParser.cs\` blob \`faf79d588fd8beb3f5761faebedd2252853b2f2b\` | Latest release is 2.1.2.1 (2026-08-30). The inspected parser is the same blob already pinned by the project; no parser bump is warranted. |
| [NSC-Toolbox latest release](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1) | Tag commit \`789fe96f99cdaa77f952b90b563c6e3f49b6d697\`; \`XfbinParser.cs\` blob \`86c63708edf2698b5bc1c2a54c0480cce014b525\`; \`SkillEditorModel.cs\` blob \`e165471682e4a7aed91094ef07f92df271f31639\` | Latest release is 2.1.2.1 (2026-08-30). XFBIN parser/editor source is already pinned at this release level. |
| [UltimateStormAPI PC source](https://github.com/TheLeonX/UltimateStormAPI/tree/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc) | Commit \`a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc\`; \`MovesetPlus.cpp\` blob \`d7c5dbbebd60415f8d304321f083897658a86146\` | Command 29 and projectile deflection use Windows mutexes, atomics, cached PC pointers and time-window state. These are PC implementation details, not Switch AArch64 ABI evidence. |
| [PyCriCodecs CPK implementation](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111) | Commit \`755055ee7b056c9c1aefc6505a3daa3e45e2e111\`; \`PyCriCodecs/cpk.py\` blob \`2ed2cbb2c6112124013ab52755dba8a443e91306\`; \`utf.py\` blob \`d1662d140a48cae37a6696213ee441aed4076edb\` | Independent CRI CPK/UTF parser reference for archive chunks and @UTF tables. It does not establish this game's runtime archive precedence or FileLoad ownership. |
| [REA binary diagnostics](https://github.com/morluto/rea/blob/0386efd1e1dfa41af41f804a6be56c6f5b7615d4/docs/binary-diagnostics.md) | Commit \`0386efd1e1dfa41af41f804a6be56c6f5b7615d4\`; doc blob \`b58b8d04dc799813d0ebe0dcd4889560c707553c\` | The pinned profile explicitly rejects AArch64. It is not used as an ARM64 decoder. |
| [Linux Standard Base DWARF EH encoding](https://www.linuxbase.org/betaspecs/lsb/LSB-Core-generic/LSB-Core-generic/dwarfext.html) | Section 10.5, DW_EH_PE value/application encodings | Defines pointer formats and pcrel/datarel/textrel application bases used by .eh_frame and .eh_frame_hdr. |
| [DWARF .eh_frame record reference](https://reverseengineering.wiki/index.php/Format%3ADWARF/.eh_frame) | Current reference page, consulted 2026-11-28 | Describes length-prefixed CIE/FDE records, backward CIE pointers, CIE R encoding, and sorted .eh_frame_hdr search table. Used as a format cross-check, not as a game-specific source. |
| Pinned Switch v1.70 original main | Git blob \`8af900db0d7003255b4ddb3cbd1289cd5a15458e\`, 27,701,509 bytes | Required SHA256 \`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9\`; the dedicated GitHub Actions job reads this exact tracked file and rechecks the hash. |

## Existing local evidence reused

- Caller census implementation \`tools/portlib/native_fileload_helper_callers.py\`, blob \`3195876aa280cf7c4f21d1e04cee4221e5df1796\`.
- Caller census regression \`tests/test_native_fileload_helper_callers.py\`, blob \`808fc14caae33cfe525793cb3a5ef442b274b7af\`.
- Caller census CI run \`46094178280\`, job \`140821654312\`, COMPLETED SUCCESS; raw log inspected. It reports 114 direct B/BL words (111 BL, 3 B), all 114 Capstone-confirmed, 86 bounded-prelude clusters. The two table-path calls are \`0x116b8a4\` and \`0x116b928\`.
- The broad foundation workflow \`46094178264\`, job \`140821654144\`, COMPLETED SUCCESS; raw log inspected. It is not repeated for this isolated metadata parser.

## New vertical slice

- \`tools/portlib/native_fileload_unwind.py\`: read-only parser for bounded DWARF .eh_frame_hdr tables and conservative linear CIE/FDE sequences in the non-text NSO segments. It validates record lengths, CIE back-references, pointer encodings, sorted header entries, FDE starts/ranges and executable-text bounds.
- \`tests/test_native_fileload_unwind.py\`: synthetic valid header/linear sequence, malformed version/encoding/count, unsorted table, bad CIE reference, out-of-text range, truncated table, range-boundary mapping and original-main SHA regressions.
- \`.github/workflows/verify-fileload-unwind.yml\`: isolated push workflow reads the pinned original main and uploads machine-readable JSON.

## Falsifiable hypotheses and limits

1. If a valid .eh_frame_hdr exists, every table entry must resolve to an in-segment FDE whose CIE back-reference is valid and whose decoded initial location equals the sorted table key.
2. If no header is found, a linear sequence is accepted only when at least eight consecutive FDE records reference one structurally valid CIE and every decoded code range lies inside the pinned executable text.
3. Each of the 114 known direct helper callers is mapped only when exactly one validated FDE range covers its callsite. Zero or multiple matches remain unmapped/ambiguous.
4. The two table-path callsites are reported independently; no register prelude is upgraded to a reaching definition.
5. An FDE range proves unwind coverage only. It does not prove a C++ function's identity, entrypoint, complete CFG, callback target, ownership, lifetime, lock/unlock, async completion, rollback/unbind, destructor, archive precedence, consumer ABI, emulated ARM64 behavior, or Uzuy gameplay.

No runtime hook or game write is added. Release flags remain false.
