#pragma once
#include "nsc_pc_raw.hpp"
#include <cstddef>
#include <cstdint>

// A container for the nine existing source PC parameter readers.
// Input byte buffer is always CALLER-OWNED and must outlive this call.
// No pointers are cached, no heap allocation, and no original game
// parameter consumer or CRI loader is hooked.
extern "C" {
struct NSCPcPackSummary {
    std::uint32_t present_mask;
    std::uint32_t source_count;
    std::uint32_t total_bytes;
    std::uint32_t total_records;
};
using NSCPcPackValidate = int (*)(const void*,std::size_t,NSCPcPackSummary*);
using NSCPcPackRow = int (*)(const void*,std::size_t,std::uint32_t,
                              std::uint32_t,NSCPcRawRow*);
struct NSCPcPackAPI {
    std::uint32_t version;
    std::uint32_t family_count;
    NSCPcPackValidate validate;
    NSCPcPackRow row_at;
};
int nsc_pc_pack_validate(const void* data,std::size_t size,NSCPcPackSummary* out);
int nsc_pc_pack_row_at(const void* data,std::size_t size,
                       std::uint32_t family,std::uint32_t row,NSCPcRawRow* out);
const NSCPcPackAPI* nsc_pc_pack_get_api();
}
// On-wire header: 64 bytes: magic[16], u32 version=1, u32 directory_count=9,
// u32 exact_total_bytes, u32 mask; sha256[32] of bytes [0:32]+[64:end].
// Directory: 9 x 48 bytes at byte 64; each row has u32 offset, u32 size,
// sha256 source bytes [32], u32 row_count, u32 zero reserved.
// Source payloads are placed in ascending family order with zero 16-byte
// alignment padding. Absent slots are entirely zero.
