#include "nsc_pc_pack.hpp"
#include <cstring>
extern "C" {
#include "nsc_sha256.h"
}

namespace {
constexpr std::size_t kHeader = 64u;
constexpr std::size_t kDirRecord = 48u;
constexpr std::size_t kFamilyCount = 9u;
constexpr std::size_t kPayloadStart = kHeader + kDirRecord*kFamilyCount;
constexpr std::size_t kMaxFamilySize = 4u*1024u*1024u;
constexpr std::size_t kMaxPack = kPayloadStart + 9u*(kMaxFamilySize+15u);
constexpr std::uint8_t kMagic[16] = {
    'N','S','C','_','P','C','_','P','A','C','K','_','V','1',0,0
};
std::uint32_t Read32(const std::uint8_t* src) {
    return std::uint32_t(src[0]) |
          (std::uint32_t(src[1])<<8) |
          (std::uint32_t(src[2])<<16) |
          (std::uint32_t(src[3])<<24);
}
bool Digest(const std::uint8_t* src,std::size_t size) {
    SHA256_CTX sha{};
    std::uint8_t digest[32]{};
    nsc_sha256_init(&sha);
    nsc_sha256_update(&sha,src,32);
    nsc_sha256_update(&sha,src+kHeader,size-kHeader);
    nsc_sha256_final(&sha,digest);
    std::uint8_t difference=0;
    for (std::size_t i=0;i<32;++i) difference|=digest[i]^src[32+i];
    return difference==0;
}
// Never publish metadata into the caller-owned source pack. The pack may
// be memory-mapped read-only, and an overlapping output would invalidate its
// digest after validation. Integer address arithmetic avoids pointer UB.
bool Overlaps(const void* a,std::size_t an,const void* b,std::size_t bn) {
    if (!a || !b || !an || !bn) return false;
    const auto x=reinterpret_cast<std::uintptr_t>(a);
    const auto y=reinterpret_cast<std::uintptr_t>(b);
    return x<=y ? y-x<an : x-y<bn;
}
bool Check(const void* ptr,std::size_t n,NSCPcPackSummary& report) {
    if (!ptr || n<kPayloadStart || n>kMaxPack || n>0xffffffffu) return false;
    const auto* b=static_cast<const std::uint8_t*>(ptr);
    if (std::memcmp(b,kMagic,sizeof(kMagic))!=0 ||
        Read32(b+16)!=1u || Read32(b+20)!=kFamilyCount ||
        Read32(b+24)!=n) return false;
    const auto mask=Read32(b+28);
    if (!mask || (mask & ~0x1ffu)) return false;
    if (!Digest(b,n)) return false;
    std::size_t cursor=kPayloadStart;
    std::uint32_t count=0,record_total=0;
    for (std::uint32_t family=0;family<kFamilyCount;++family) {
        const auto* entry=b+kHeader+family*kDirRecord;
        const auto offset=Read32(entry);
        const auto length=Read32(entry+4);
        const auto records=Read32(entry+40);
        const auto reserved=Read32(entry+44);
        if (reserved) return false;
        if (!(mask & (1u<<family))) {
            for (std::size_t j=0;j<kDirRecord;++j)
                if (entry[j]!=0) return false;
            continue;
        }
        const auto aligned=(cursor+15u)&~std::size_t(15u);
        if (offset!=aligned || length==0 || length>kMaxFamilySize ||
            aligned>n || length>n-aligned) return false;
        for (std::size_t j=cursor;j<aligned;++j)
            if (b[j]!=0) return false;
        NSCPcRawSummary source{};
        if (!nsc_pc_raw_validate(family,b+offset,length,entry+8,&source) ||
            source.record_count!=records) return false;
        // Keep integer math proven bounded; the source reader caps rows.
        if (record_total>0xffffffffu-records) return false;
        record_total+=records;
        cursor=aligned+length;
        ++count;
    }
    if (cursor!=n) return false;
    report={mask,count,static_cast<std::uint32_t>(n),record_total};
    return true;
}
}

extern "C" int nsc_pc_pack_validate(const void* data,std::size_t size,
                                     NSCPcPackSummary* out) {
    if (!out || Overlaps(data,size,out,sizeof(*out))) return 0;
    NSCPcPackSummary valid{};
    if (!Check(data,size,valid)) return 0;
    *out=valid;
    return 1;
}
extern "C" int nsc_pc_pack_row_at(const void* data,std::size_t size,
             std::uint32_t family,std::uint32_t row,NSCPcRawRow* out) {
    if (!out || family>=9u || Overlaps(data,size,out,sizeof(*out))) return 0;
    NSCPcPackSummary valid{};
    if (!Check(data,size,valid) || !(valid.present_mask & (1u<<family))) return 0;
    const auto* b=static_cast<const std::uint8_t*>(data);
    const auto* e=b+kHeader+family*kDirRecord;
    const auto offset=Read32(e),length=Read32(e+4);
    // Raw reader independently verifies the per-family source SHA256 and
    // source row contract. Its output is not published on failure.
    return nsc_pc_raw_row_at(family,b+offset,length,e+8,row,out);
}
extern "C" const NSCPcPackAPI* nsc_pc_pack_get_api() {
    static const NSCPcPackAPI api{1u,9u,&nsc_pc_pack_validate,&nsc_pc_pack_row_at};
    return &api;
}
