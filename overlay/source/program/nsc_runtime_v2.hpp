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

// Apply 33 words: four R180 baseline prerequisites, four descriptor count,
// one P67 prerequisite, 24 P128 UJ corridor words. Runtime memory only.
bool InstallOriginalMainRuntimePatches();
bool RuntimeMainPatchesReady();
bool GetDerivedUjGateLoadOffset(std::ptrdiff_t& out_offset);

// R181 full eligibility rollback: restore the pre-R178 baseline by keeping
// the original Switch v1.70 E54/124 gate intact and making Event236 opcode13
// shadow-only. This function writes zero gate words and opcode13 writes zero
// F20/F30 state.
bool InstallR181DpadFullEligibilityRollback();

} // namespace nsc::v2
