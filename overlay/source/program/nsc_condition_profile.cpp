#include "nsc_condition_profile.hpp"
extern "C" {
#include "nsc_sha256.h"
}
namespace nsc::condition_profile {
namespace {
char names[kCapacity][49]{};
Descriptor entries[kCapacity]{};
std::uint32_t count=0;
std::uint32_t U32(const std::uint8_t* b) {
    return b[0]|(std::uint32_t(b[1])<<8)|(std::uint32_t(b[2])<<16)|(std::uint32_t(b[3])<<24);
}
bool Name(const std::uint8_t* b) {
    std::size_t i=0;
    for (;i<49 && b[i];++i) if (b[i]<32 || b[i]>126) return false;
    if (!i || i==49) return false;
    for (;i<56;++i) if (b[i]) return false;
    return true;
}
bool Same(const std::uint8_t* a,const std::uint8_t* b) {
    for (unsigned i=0;i<49;++i) { if (a[i]!=b[i]) return false; if (!a[i]) return true; }
    return true;
}
}
bool LoadProfile(const void* data,std::size_t size) {
    if (!data || size!=kProfileSize) return false;
    const auto* b=static_cast<const std::uint8_t*>(data);
    constexpr char magic[16]="NSC_COND_V1";
    for (unsigned i=0;i<16;++i) if (b[i]!=magic[i]) return false;
    const auto n=U32(b+20);
    if (U32(b+16)!=1 || n>kCapacity) return false;
    for (unsigned i=56;i<64;++i) if (b[i]) return false;
    SHA256_CTX ctx;std::uint8_t digest[32];
    nsc_sha256_init(&ctx);nsc_sha256_update(&ctx,b,24);
    nsc_sha256_update(&ctx,b+56,kProfileSize-56);nsc_sha256_final(&ctx,digest);
    for (unsigned i=0;i<32;++i) if (b[24+i]!=digest[i]) return false;
    for (std::uint32_t i=0;i<n;++i) {
        const auto* row=b+64+i*kRecordSize;
        if (!Name(row) || U32(row+56)>=kNativeCount+n || U32(row+76)) return false;
        for (std::uint32_t j=0;j<i;++j) if (Same(row,b+64+j*kRecordSize)) return false;
    }
    for (auto i=64+n*kRecordSize;i<kProfileSize;++i) if (b[i]) return false;
    // Publish only after the entire profile passed validation.
    for (std::uint32_t i=0;i<kCapacity;++i) {
        entries[i]={};
        for (auto& c:names[i]) c=0;
        if (i<n) {
            const auto* row=b+64+i*kRecordSize;
            for (unsigned k=0;k<49;++k) names[i][k]=static_cast<char>(row[k]);
            entries[i]={names[i],U32(row+56),U32(row+60),U32(row+64),U32(row+68),U32(row+72),0};
        }
    }
    count=n;return true;
}
bool LoadEmbeddedProfile() { return LoadProfile(&nsc_condition_profile,sizeof(nsc_condition_profile)); }
std::uint32_t Count() { return count; }
std::uint32_t TotalCount() { return kNativeCount+count; }
const Descriptor* Get(std::uint32_t index) {
    return index>=kNativeCount && index<kNativeCount+count ? &entries[index-kNativeCount] : nullptr;
}
}
