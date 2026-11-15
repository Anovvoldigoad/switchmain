#pragma once
#include <cstddef>
#include <cstdint>

// Standalone validated PC ModdingAPI raw-byte readers. No game pointer is
// retained. No original Switch engine ABI, hook, factory or CPK precedence is
// inferred. Family IDs are stable only for this internal NSC port API.
extern "C" {
struct NSCPcRawSummary {
    std::uint32_t record_count;
    std::uint32_t consumed_bytes;
    std::uint32_t ignored_terminal_bytes;
    std::uint32_t reserved;
};
struct NSCPcRawRow {
    std::uint32_t offset;
    std::uint32_t length;
    std::uint32_t source_field_0;
    std::uint32_t source_field_1;
};
using NSCPcRawValidate = int (*)(std::uint32_t, const void*, std::size_t,
                                  const std::uint8_t*, NSCPcRawSummary*);
using NSCPcRawRead = int (*)(std::uint32_t, const void*, std::size_t,
                              const std::uint8_t*, std::uint32_t, NSCPcRawRow*);
struct NSCPcRawAPI {
    std::uint32_t version;
    std::uint32_t family_count;
    NSCPcRawValidate validate;
    NSCPcRawRead row_at;
};
int nsc_pc_raw_validate(std::uint32_t family, const void* data, std::size_t size,
                        const std::uint8_t expected_sha256[32],
                        NSCPcRawSummary* out);
int nsc_pc_raw_row_at(std::uint32_t family, const void* data, std::size_t size,
                      const std::uint8_t expected_sha256[32],
                      std::uint32_t row, NSCPcRawRow* out);
const NSCPcRawAPI* nsc_pc_raw_get_api();
}
// Family enum (NOT native game type identifiers):
// 0 Susanoo 0x20; 1 Partner 0x20; 2 Ougi uint32; 3 Gudo uint32;
// 4 CharRelation count-prefixed; 5 PairSpSkill 0x18 (optional terminal byte);
// 6 BGM 0x68; 7 SpecialInteraction variable; 8 GuardEffect 0xF8.
