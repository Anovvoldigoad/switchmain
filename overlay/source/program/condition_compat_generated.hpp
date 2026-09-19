#pragma once
#include <cstddef>
#include <cstdint>

namespace nsc::condition_compat_generated {

struct ConditionDescriptor {
    const char* name;
    uint32_t field08;
    uint32_t field0C;
    uint32_t field10;
    uint32_t field14;
    uint32_t field18;
    uint32_t field1C;
};
static_assert(sizeof(ConditionDescriptor) == 0x20);

static constexpr char kName0[] = "SW_MTOB_XH";
static constexpr char kName1[] = "SW_MTOB_ST";
static constexpr char kName2[] = "YXNQ_MTOB";
static constexpr char kName3[] = "SW_MTOB_BREAK";
static constexpr char kName4[] = "WC_MTOB_BREAK";

static constexpr uint32_t kNativeConditionCount = 512u;
static constexpr uint32_t kExtraConditionCount = 5u;
static constexpr uint32_t kTotalConditionCount = kNativeConditionCount + kExtraConditionCount;

static const ConditionDescriptor kExtraConditions[kExtraConditionCount] = {
    {kName0, 0x201u, 0x1u, 0x8u, 0x5u, 0x5u, 0x0u},
    {kName1, 0x0u, 0xAu, 0x7u, 0x5u, 0x5u, 0x0u},
    {kName2, 0x201u, 0x1u, 0x9u, 0x5u, 0x5u, 0x0u},
    {kName3, 0x0u, 0x0u, 0x0u, 0x5u, 0x5u, 0x0u},
    {kName4, 0x0u, 0x0u, 0x3u, 0x5u, 0x5u, 0x0u},
};

} // namespace nsc::condition_compat_generated
