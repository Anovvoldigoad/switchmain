#include "nsc_pc_raw.hpp"
#include <cstring>
extern "C" {
#include "nsc_sha256.h"
}

namespace {
constexpr std::size_t kMaxSource = 4u*1024u*1024u;
constexpr std::uint32_t kMaxRows = 10000u;
constexpr std::uint32_t kRaw32MaxRows = 8192u;
constexpr const char* kSusanoo[] = {"SSN_2ITC","SSN_2SSZ","SSN_3SSK","SSN_4SSI","SSN_BSSZ"};
constexpr const char* kPartner[] = {
    "PARTNER_TYPE_2PAR","PARTNER_TYPE_2KKG","PARTNER_TYPE_2AKM",
    "PARTNER_TYPE_2KRS","PARTNER_TYPE_1AKM","PARTNER_TYPE_1KRS",
    "PARTNER_TYPE_2SCX","PARTNER_TYPE_8AEM"};
std::uint32_t U32(const std::uint8_t* p) {
    return std::uint32_t(p[0]) | (std::uint32_t(p[1])<<8) |
           (std::uint32_t(p[2])<<16) | (std::uint32_t(p[3])<<24);
}
std::uint16_t U16(const std::uint8_t* p) {
    return std::uint16_t(p[0] | (std::uint16_t(p[1])<<8));
}
bool EqualName(const std::uint8_t* data, const char* name) {
    const auto n = std::strlen(name);
    return n < 24 && std::memcmp(data,name,n)==0 && data[n]==0;
}
bool KnownName(std::uint32_t family, const std::uint8_t* name) {
    if (family==0) {
        for (const auto* s : kSusanoo) if (EqualName(name,s)) return true;
    } else if (family==1) {
        for (const auto* s : kPartner) if (EqualName(name,s)) return true;
    }
    return false;
}
bool MatchingSha(const std::uint8_t* raw, std::size_t size, const std::uint8_t* expected) {
    SHA256_CTX ctx{};
    std::uint8_t found[32];
    nsc_sha256_init(&ctx);
    nsc_sha256_update(&ctx,raw,size);
    nsc_sha256_final(&ctx,found);
    std::uint8_t difference=0;
    for (std::uint32_t i=0;i<32;++i) difference|=found[i]^expected[i];
    return difference==0;
}
bool Parse(std::uint32_t family, const std::uint8_t* raw, std::size_t size,
           std::uint32_t requested, NSCPcRawSummary& summary, NSCPcRawRow& selected) {
    std::uint32_t count=0;
    std::size_t position=0;
    std::uint32_t terminal=0;
    if (family==0 || family==1) {
        if (size%0x20 || size/0x20>kRaw32MaxRows) return false;
        // Duplicate u16 IDs are invalid for both publicly verified PC 0x20
        // formats; 65536-bit stack bitset, no heap and no global state.
        std::uint8_t used[8192]{};
        for (std::size_t off=0;off<size;off+=0x20) {
            if (!KnownName(family,raw+off)) return false;
            const auto id=U16(raw+off+0x18);
            if (used[id>>3] & (1u<<(id&7u))) return false;
            used[id>>3]|=std::uint8_t(1u<<(id&7u));
            if (count==requested) selected={
                static_cast<std::uint32_t>(off),0x20u,id,0u};
            ++count;
        }
        position=size;
    } else if (family==2 || family==3) {
        if (size%4 || size/4>kMaxRows) return false;
        for (std::size_t off=0;off<size;off+=4) {
            if (count==requested) selected={
                static_cast<std::uint32_t>(off),4u,U32(raw+off),0u};
            ++count;
        }
        position=size;
    } else if (family==4) {
        while (position<size) {
            if (count==kMaxRows || size-position<4) return false;
            const std::size_t off=position;
            const auto n=U32(raw+position);
            position+=4;
            if (n>(size-position)/4) return false;
            const auto length=4u+4u*n;
            if (count==requested) selected={
                static_cast<std::uint32_t>(off),length,n,0u};
            position+=std::size_t(n)*4;
            ++count;
        }
    } else if (family==5 || family==6 || family==8) {
        const std::size_t width=family==5 ? 0x18u : family==6 ? 0x68u : 0xF8u;
        terminal=family==5 ? std::uint32_t(size%width) : 0u;
        if (family==5 ? terminal>1 : size%width!=0) return false;
        if (size/width>kMaxRows) return false;
        for (std::size_t off=0;off+width<=size;off+=width) {
            std::uint32_t a=0,b=0;
            if (family==5) {
                a=U32(raw+off+0x10);b=U32(raw+off+0x14);
            } else if (family==6) {
                a=U32(raw+off+0x60);b=U32(raw+off+0x64);
            } else {
                a=U32(raw+off);b=U32(raw+off+4);
            }
            if (count==requested) selected={
                static_cast<std::uint32_t>(off),
                static_cast<std::uint32_t>(width),a,b};
            ++count;
        }
        position=size-terminal;
    } else if (family==7) {
        if (size<4) return false;
        const auto rowcount=static_cast<std::int32_t>(U32(raw));
        if (rowcount<0 || rowcount>static_cast<std::int32_t>(kMaxRows)) return false;
        position=4;
        for (std::int32_t n=0;n<rowcount;++n) {
            if (size-position<8) return false;
            const std::size_t off=position;
            const auto id=U32(raw+position);
            const auto triggers=static_cast<std::int32_t>(U32(raw+position+4));
            position+=8;
            if (triggers<0 || std::size_t(triggers)>(size-position)/4) return false;
            if (count==requested) selected={
                static_cast<std::uint32_t>(off),
                static_cast<std::uint32_t>(8u+4u*triggers),
                id,static_cast<std::uint32_t>(triggers)};
            position+=std::size_t(triggers)*4;
            ++count;
        }
    } else {
        return false;
    }
    if (position+terminal!=size) return false;
    summary={count,static_cast<std::uint32_t>(position),terminal,0u};
    return true;
}
}

extern "C" int nsc_pc_raw_validate(std::uint32_t family, const void* data,
    std::size_t size, const std::uint8_t expected_sha256[32], NSCPcRawSummary* out) {
    if (!data || !expected_sha256 || !out || !size || size>kMaxSource || family>=9) return 0;
    const auto* p=static_cast<const std::uint8_t*>(data);
    if (!MatchingSha(p,size,expected_sha256)) return 0;
    NSCPcRawSummary summary{};
    NSCPcRawRow ignored{};
    if (!Parse(family,p,size,~std::uint32_t(0),summary,ignored)) return 0;
    *out=summary;
    return 1;
}

extern "C" int nsc_pc_raw_row_at(std::uint32_t family, const void* data,
    std::size_t size, const std::uint8_t expected_sha256[32],
    std::uint32_t row, NSCPcRawRow* out) {
    if (!out) return 0;
    NSCPcRawSummary summary{};
    if (!nsc_pc_raw_validate(family,data,size,expected_sha256,&summary) ||
        row>=summary.record_count) return 0;
    NSCPcRawSummary verified{};
    NSCPcRawRow selected{};
    if (!Parse(family,static_cast<const std::uint8_t*>(data),
               size,row,verified,selected) || verified.record_count!=summary.record_count)
        return 0;
    *out=selected;
    return 1;
}

extern "C" const NSCPcRawAPI* nsc_pc_raw_get_api() {
    static const NSCPcRawAPI api{1u,9u,&nsc_pc_raw_validate,&nsc_pc_raw_row_at};
    return &api;
}
