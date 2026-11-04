#include "lib.hpp"
#include "nsc_runtime_core.hpp"
#include "nsc_runtime_v2.hpp"
#include "nsc_image_guard.hpp"
extern "C" {
#include "nsc_sha256.h"
}
std::uintptr_t test_base;
std::size_t test_size, test_writes;
static unsigned hook_calls;
namespace nsc::factory { bool InstallFactoryHook() { ++hook_calls; return true; } }
namespace nsc::conditions { bool InstallRawStorageHooks() { ++hook_calls; return true; } }
namespace nsc {
void InstallP128AStaticPreciseGateCaveProof() { ++hook_calls; }
bool InstallR172UjMissAnmDirectParity() { ++hook_calls; return true; }
void InstallR175DpadLookupMatrixTrace() { ++hook_calls; }
void InstallR176ActionRegistryMatrixTrace() { ++hook_calls; }
void InstallR177ActionDescriptorMatrixTrace() { ++hook_calls; }
bool InstallV2NStageRegistryProof() { ++hook_calls; return true; }
void InstallV2PPassiveOrderProbe() { ++hook_calls; }
}
extern "C" {
int run_init(void* p, std::size_t n) {
 test_base=reinterpret_cast<std::uintptr_t>(p); test_size=n; test_writes=0; hook_calls=0;
 return nsc::runtime::Initialize();
}
int run_patch(void* p,std::size_t n) {
 test_base=reinterpret_cast<std::uintptr_t>(p); test_size=n; test_writes=0;
 nsc::v2::InstallResolverHookMigrationProbe();
 return nsc::v2::InstallOriginalMainRuntimePatches();
}
std::size_t writes() { return test_writes; }
unsigned hooks() { return hook_calls; }
int profile(void* p,std::size_t n) { return static_cast<int>(nsc::image::Identify(p,n)); }
void digest(const void* p,std::size_t n,void* out) {
 SHA256_CTX c; nsc_sha256_init(&c); nsc_sha256_update(&c,static_cast<const unsigned char*>(p),n);
 nsc_sha256_final(&c,static_cast<unsigned char*>(out));
}
}
