#include "nsc_cpk_profile.hpp"
#include <atomic>
extern "C" {
#include "nsc_sha256.h"
}

namespace nsc::cpk {
namespace {
struct Entry { char path[kPathSize]; int priority; std::uint32_t id; };
Entry entries[kCapacity]{};
std::uint32_t count = 0;
std::atomic<std::uint32_t> registered{0};
std::atomic_flag busy = ATOMIC_FLAG_INIT;
std::uint32_t Read32(const std::uint8_t* p) {
    return p[0] | (std::uint32_t(p[1])<<8) | (std::uint32_t(p[2])<<16) | (std::uint32_t(p[3])<<24);
}
unsigned Lower(unsigned c) { return c >= 'A' && c <= 'Z' ? c + ('a'-'A') : c; }
bool ValidPath(const std::uint8_t* p) {
    constexpr char prefix[] = "sim:data/moddingapi/";
    constexpr auto begin = sizeof(prefix)-1;
    for (std::size_t i=0;i<begin;++i) if (p[i]!=prefix[i]) return false;
    std::size_t length=begin, component=begin;
    for (;length<kPathSize && p[length];++length) {
        const unsigned c=p[length];
        if (c=='/') {
            if (length==component || p[component]==' ' || p[length-1]==' ' ||
                (length-component==1 && p[component]=='.') ||
                (length-component==2 && p[component]=='.' && p[component+1]=='.')) return false;
            component=length+1;
        } else if (!((c>='a'&&c<='z') || (c>='A'&&c<='Z') ||
                     (c>='0'&&c<='9') || c=='_' || c=='-' || c=='.' || c==' ')) return false;
    }
    if (length==kPathSize || length-component<=4 || p[component]==' ' || p[length-1]==' ') return false;
    if (p[length-4]!='.' || Lower(p[length-3])!='c' || Lower(p[length-2])!='p' || Lower(p[length-1])!='k') return false;
    for (auto i=length;i<kPathSize;++i) if (p[i]) return false;
    return true;
}
bool SamePath(const std::uint8_t* a, const std::uint8_t* b) {
    for (std::size_t i=0;i<kPathSize;++i) {
        if (Lower(a[i])!=Lower(b[i])) return false;
        if (!a[i]) return true;
    }
    return true;
}
bool Sim(const char* p) {
    constexpr char prefix[]="sim:";
    if (!p) return false;
    for (unsigned i=0;i<4;++i) if (p[i]!=prefix[i]) return false;
    return true;
}
}
bool LoadProfile(const void* data, std::size_t size) {
    if (!data || size!=kProfileSize) return false;
    const auto* b=static_cast<const std::uint8_t*>(data);
    constexpr char magic[16]="NSC_CPK_LIST_V1";
    for (unsigned i=0;i<16;++i) if (b[i]!=magic[i]) return false;
    const auto n=Read32(b+20);
    if (Read32(b+16)!=1 || n>kCapacity) return false;
    for (unsigned i=56;i<64;++i) if (b[i]) return false;
    SHA256_CTX ctx;std::uint8_t digest[32];
    nsc_sha256_init(&ctx);nsc_sha256_update(&ctx,b,24);
    nsc_sha256_update(&ctx,b+56,kProfileSize-56);nsc_sha256_final(&ctx,digest);
    for (unsigned i=0;i<32;++i) if (b[24+i]!=digest[i]) return false;
    for (std::uint32_t i=0;i<n;++i) {
        const auto* row=b+64+i*kRecordSize;
        if (Read32(row)>INT32_MAX || !ValidPath(row+16)) return false;
        for (unsigned k=4;k<16;++k) if (row[k]) return false;
        for (std::uint32_t j=0;j<i;++j) {
            const auto* prior=b+64+j*kRecordSize;
            if (Read32(row)==Read32(prior) || SamePath(row+16,prior+16)) return false;
        }
    }
    for (auto i=64+n*kRecordSize;i<kProfileSize;++i) if (b[i]) return false;
    for (std::uint32_t i=0;i<kCapacity;++i) {
        entries[i]={};
        if (i<n) {
            const auto* row=b+64+i*kRecordSize;
            entries[i].priority=static_cast<int>(Read32(row));
            for (unsigned k=0;k<kPathSize;++k) entries[i].path[k]=static_cast<char>(row[16+k]);
        }
    }
    count=n;registered.store(0,std::memory_order_release);busy.clear(std::memory_order_release);
    return true;
}
bool LoadEmbeddedProfile() { return LoadProfile(&nsc_cpk_profile,sizeof(nsc_cpk_profile)); }
std::uint32_t Count() { return count; }
std::uint32_t RegisteredCount() {
    auto mask=registered.load(std::memory_order_acquire);std::uint32_t n=0;
    while (mask) { mask &= mask-1; ++n; }
    return n;
}
bool BindingId(std::uint32_t index, std::uint32_t* out) {
    if (!out || index>=count || !(registered.load(std::memory_order_acquire)&(1u<<index))) return false;
    *out=entries[index].id;return true;
}
void AfterBind(const PathArg* request, std::uint32_t result, Bind original) {
    if (!count || !original || !result || !request || !Sim(request->path)) return;
    if (busy.test_and_set(std::memory_order_acquire)) return;
    for (std::uint32_t i=0;i<count;++i) {
        const auto bit=1u<<i;
        if (registered.load(std::memory_order_relaxed)&bit) continue;
        PathArg desc{entries[i].path,0,0,0};std::uint32_t id=0;
        const auto status=original(&desc,&id,entries[i].priority);
        // Native 0x115E80C returns 1 without assigning an ID on missing binder
        // or allocation failure. Nonzero return alone is NOT registration proof.
        if (status && id) {
            entries[i].id=id;registered.fetch_or(bit,std::memory_order_release);
        }
    }
    busy.clear(std::memory_order_release);
}
}
