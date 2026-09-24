#pragma once

#include <cstddef>
#include <cstdint>

/*
 * GENERATED FILE — DO NOT HAND-EDIT.
 *
 * Proven compiled specialCondParam records:
 *   charID 276 -> COND_9ISH -> dispatcher selector 276
 *   charID 281 -> COND_2DNZ -> dispatcher selector 58
 *
 * Dispatcher index proof comes from the UltimateStormAPI 281-entry
 * dispatcher-name table. Runtime code consumes this as a generic data table;
 * there is no character-specific gameplay branch in the hook.
 */

namespace nsc {
namespace p103_data {

struct SpecialCondMapEntry {
    uint32_t character_selector;
    uint32_t dispatcher_selector;
};

static constexpr SpecialCondMapEntry kSpecialCondMap[] = {
    {276u, 276u},
    {281u, 58u},
};

static constexpr std::size_t kSpecialCondMapCount =
    sizeof(kSpecialCondMap) / sizeof(kSpecialCondMap[0]);

static inline uint32_t MapSpecialCondSelector(uint32_t selector) {
    for (std::size_t i = 0; i < kSpecialCondMapCount; ++i) {
        if (kSpecialCondMap[i].character_selector == selector) {
            return kSpecialCondMap[i].dispatcher_selector;
        }
    }
    return selector;
}

} // namespace p103_data
} // namespace nsc
