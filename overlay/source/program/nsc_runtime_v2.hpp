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

// Resolve the current game's native targets by signature. V2C remains in
// coexistence with P128 while active hook entries consume runtime-resolved
// offsets instead of compile-time main+offset constants.
void InstallResolverHookMigrationProbe();

// Fail-closed accessor. Returns false unless the anchor resolved uniquely in
// the current process image during InstallResolverHookMigrationProbe().
bool GetResolvedOffset(Anchor anchor, std::ptrdiff_t& out_offset);
const char* AnchorName(Anchor anchor);

// Derived from a unique BL xref to resolved UJ_SESSION_OUTER with the proven
// native corridor shape. Returns the instruction immediately after the BL.
bool GetDerivedUjSessionPostOffset(std::ptrdiff_t& out_offset);

} // namespace nsc::v2
