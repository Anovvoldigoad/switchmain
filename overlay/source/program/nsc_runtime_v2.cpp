#include "nsc_runtime_v2.hpp"
#include <lib/util/modules.hpp>
#include <program/loggers.hpp>
#include <cstddef>
#include <cstdint>

namespace nsc::v2 {
namespace {

// V2A is deliberately a coexistence/read-only proof.  The scan span is the
// verified v1.70 .text size.  A later loader stage will query RX memory ranges
// dynamically; this stage first proves the resolver/signature model without
// changing the already-functional P128 gameplay path.
constexpr std::size_t kScanSpan = 0x12F5FD0;

struct Pattern {
    const char* name;
    const std::uint32_t* value;
    const std::uint32_t* mask;
    std::size_t count;
    std::ptrdiff_t v170_expected;
};

bool MatchAt(std::uintptr_t base, std::size_t off, const Pattern& p) {
    const auto* q = reinterpret_cast<const volatile std::uint32_t*>(base + off);
    for (std::size_t i = 0; i < p.count; ++i) {
        const std::uint32_t w = q[i];
        if ((w & p.mask[i]) != (p.value[i] & p.mask[i])) return false;
    }
    return true;
}

std::uintptr_t ResolveUnique(std::uintptr_t base, const Pattern& p, std::uint32_t& hits) {
    hits = 0;
    std::uintptr_t found = 0;
    const std::size_t bytes = p.count * sizeof(std::uint32_t);
    if (bytes == 0 || bytes > kScanSpan) return 0;
    for (std::size_t off = 0; off + bytes <= kScanSpan; off += 4) {
        if (!MatchAt(base, off, p)) continue;
        ++hits;
        if (hits == 1) found = base + off;
        if (hits > 1) return 0; // fail closed: ambiguous signature
    }
    return hits == 1 ? found : 0;
}

#define ARRAY_COUNT(a) (sizeof(a) / sizeof((a)[0]))

// Masks keep stable opcode/register structure while ignoring relocatable
// immediates in ADRP/B/BL/CBZ/B.cond where appropriate.
static constexpr std::uint32_t kCharVal[] = {
    0xF000EA68,0xF9424508,0xF9760908,0x2A0003E1,0xF9409500,0x1410AC93,
    0x00000000,0x00000000,0xF81E0FFE,0xA9014FF4,0xF000EA68,0xF9424508};
static constexpr std::uint32_t kCharMask[] = {
    0x9F00001F,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFC000000,
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0x9F00001F,0xFFFFFFFF};

static constexpr std::uint32_t kCpkVal[] = {
    0xF81D0FFE,0xA90157F6,0xA9024FF4,0xD000E6A8,0xF945ED08,0xAA0003F5,
    0xF9400100,0xB4000200,0xAA0103F4,0xB9400AA8,0x2A0203F3,0xF94002A1};
static constexpr std::uint32_t kCpkMask[] = {
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0x9F00001F,0xFFFFFFFF,0xFFFFFFFF,
    0xFFFFFFFF,0xFF00001F,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF};

static constexpr std::uint32_t kEvent236Val[] = {
    0xF81F0FFE,0xF9400008,0xF946E908,0xD63F0100,0xB4000080,0xF9400008,
    0xF945E108,0xD63F0100,0x52800020,0xF84107FE,0xD65F03C0,0x52800020};
static constexpr std::uint32_t kEvent236Mask[] = {
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFF00001F,0xFFFFFFFF,
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF};

static constexpr std::uint32_t kPlayVal[] = {
    0xA9BE57FE,0xA9014FF4,0xB9529408,0x2A0403F4,0xAA0003F3,0x7100091F,
    0x54000080,0xB9528668,0x7100051F,0x540000A1,0x2A1F03E2,0x52800028};
static constexpr std::uint32_t kPlayMask[] = {
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,
    0xFF00001F,0xFFFFFFFF,0xFFFFFFFF,0xFF00001F,0xFFFFFFFF,0xFFFFFFFF};

static constexpr std::uint32_t kSetterVal[] = {
    0xD10303FF,0x6D0523E9,0xA9067BFD,0xA9076FFC,0xA90867FA,0xA9095FF8,
    0xA90A57F6,0xA90B4FF4,0xF9410C08,0x4EA01C08,0x2A0303F4,0x2A0203F6};
static constexpr std::uint32_t kSetterMask[] = {
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF};

static constexpr std::uint32_t kOuterVal[] = {
    0xF81E0FFE,0xA9014FF4,0xAA0003F3,0x940023EE,0x350002A0,0x9000CAA8,
    0xF9424508,0xF9762514,0xB4000234,0xF9400268,0xAA1303E0,0xF9402508};
static constexpr std::uint32_t kOuterMask[] = {
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFC000000,0xFF00001F,0x9F00001F,
    0xFFFFFFFF,0xFFFFFFFF,0xFF00001F,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF};

static constexpr std::uint32_t kState137Val[] = {
    0x528058C1,0xF94027F8,0x1E2E1000,0x12800002,0xAA1303E0,0x2A1F03E3,
    0x2A1F03E4,0x97FDFF32,0x340004C0,0x528002C1,0xAA1303E0,0x97FEB5B6};
static constexpr std::uint32_t kState137Mask[] = {
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,
    0xFFFFFFFF,0xFC000000,0xFF00001F,0xFFFFFFFF,0xFFFFFFFF,0xFC000000};

static constexpr Pattern kPatterns[] = {
    {"CHARACODE_GETTER", kCharVal, kCharMask, ARRAY_COUNT(kCharVal), 0x3F4150},
    {"CPK_BIND", kCpkVal, kCpkMask, ARRAY_COUNT(kCpkVal), 0x473190},
    {"EVENT236", kEvent236Val, kEvent236Mask, ARRAY_COUNT(kEvent236Val), 0x816300},
    {"PLAY_ACTION", kPlayVal, kPlayMask, ARRAY_COUNT(kPlayVal), 0x766B8C},
    {"CENTRAL_SETTER", kSetterVal, kSetterMask, ARRAY_COUNT(kSetterVal), 0x766320},
    {"UJ_SESSION_OUTER", kOuterVal, kOuterMask, ARRAY_COUNT(kOuterVal), 0x7EF098},
    {"STATE137_CONTROLLER", kState137Val, kState137Mask, ARRAY_COUNT(kState137Val), 0x7E6EA8},
};

} // namespace

void InstallResolverCoexistenceProbe() {
    const std::uintptr_t base = exl::util::modules::GetTargetStart();
    std::uint32_t ok = 0;
    Logging.Log("[NSC:V2A] RESOLVER_START base=%p span=0x%lx readonly=1 coexist_p128=1",
                reinterpret_cast<void*>(base), static_cast<unsigned long>(kScanSpan));
    for (const auto& p : kPatterns) {
        std::uint32_t hits = 0;
        const std::uintptr_t addr = ResolveUnique(base, p, hits);
        const std::ptrdiff_t off = addr ? static_cast<std::ptrdiff_t>(addr - base) : -1;
        const bool expected = addr && off == p.v170_expected;
        if (addr) ++ok;
        Logging.Log("[NSC:V2A] RESOLVE name=%s hits=%u addr=%p off=0x%lx v170_expected=0x%lx exact=%u",
                    p.name, hits, reinterpret_cast<void*>(addr),
                    static_cast<unsigned long>(off),
                    static_cast<unsigned long>(p.v170_expected), expected ? 1u : 0u);
    }
    Logging.Log("[NSC:V2A] READY resolved=%u total=%u fail_closed=1 no_runtime_patch=1 no_new_hook=1",
                ok, static_cast<unsigned>(ARRAY_COUNT(kPatterns)));
}

} // namespace nsc::v2
