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

} // namespace nsc::v2
