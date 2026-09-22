#pragma once

#include <cstddef>
#include <cstdint>

/*
 * GENERATED FILE — DO NOT HAND-EDIT.
 *
 * Source:
 *   /storage/emulated/0/Downloads/p81_runtime_input_recovery/ougiAwakeningParam.xfbin
 *
 * SHA256:
 *   4322e4ab30547321abc6cd24322a5ba98f8e7d0ddafa853039234c397ccfe6cb
 *
 * Raw count:
 *   1
 *
 * Unique membership count:
 *   1
 *
 * This is data, not a character-specific gameplay branch.
 */

namespace nsc {
namespace p81_data {

static constexpr uint32_t kOugiAwakeningIds[] = {
    281u
};

static constexpr std::size_t kOugiAwakeningIdCount =
    sizeof(kOugiAwakeningIds)
    / sizeof(kOugiAwakeningIds[0]);

static constexpr const char
    kOugiAwakeningSourceSha256[] =
        "4322e4ab30547321abc6cd24322a5ba98f8e7d0ddafa853039234c397ccfe6cb";

static inline bool ContainsOugiAwakeningId(
    uint32_t id
) {
    for (
        std::size_t i = 0;
        i < kOugiAwakeningIdCount;
        ++i
    ) {
        if (kOugiAwakeningIds[i] == id) {
            return true;
        }
    }

    return false;
}

} // namespace p81_data
} // namespace nsc
