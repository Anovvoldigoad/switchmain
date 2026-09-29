#pragma once
#include <cstddef>

namespace nsc::v2 {

enum class Anchor : unsigned {
    CharacodeGetter = 0,
    CpkBind,
    Event236,
    PlayAction,
    CentralSetter,
    UjSessionOuter,
    State137Controller,
    Count,
};

// Resolve the current game's native targets by signature. V2D runs against an
// original on-disk main and then recreates the proven paired-main instruction
// edits in writable runtime memory only after full-plan validation.
void InstallResolverHookMigrationProbe();

// Fail-closed accessor. Returns false unless the anchor resolved uniquely in
// the current process image during InstallResolverHookMigrationProbe().
bool GetResolvedOffset(Anchor anchor, std::ptrdiff_t& out_offset);
const char* AnchorName(Anchor anchor);

// Derived from a unique BL xref to resolved UJ_SESSION_OUTER with the proven
// native corridor shape. Returns the instruction immediately after the BL.
bool GetDerivedUjSessionPostOffset(std::ptrdiff_t& out_offset);

// Apply the exact 30-word functional main delta (5 condition count + 1 P67
// prerequisite + 24 P128 UJ corridor words) to runtime memory only. Fail closed.
bool InstallOriginalMainRuntimePatches();
bool RuntimeMainPatchesReady();
bool GetDerivedUjGateLoadOffset(std::ptrdiff_t& out_offset);

// R180 rollback-only recovery: retire the failed R178/R179 PC-style D-pad
// native gate rewrite and verify the original Switch v1.70 E54/124 words are
// intact. Event236 opcode13 remains on actor+0xF30; this function writes zero
// gameplay words and exists only as a fail-closed native-gate fingerprint.
bool InstallR180DpadNativeGateRollback();

} // namespace nsc::v2
