#include "nsc_cpk_profile.hpp"
extern "C" {
bool load_cpk(const void* p, std::size_t n) { return nsc::cpk::LoadProfile(p,n); }
std::uint32_t cpk_count() { return nsc::cpk::Count(); }
std::uint32_t cpk_registered() { return nsc::cpk::RegisteredCount(); }
bool cpk_id(std::uint32_t i, std::uint32_t* p) { return nsc::cpk::BindingId(i,p); }
void cpk_after(const nsc::cpk::PathArg* p, std::uint32_t status, nsc::cpk::Bind fn) { nsc::cpk::AfterBind(p,status,fn); }
}
