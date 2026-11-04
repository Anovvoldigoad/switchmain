#include "nsc_condition_profile.hpp"
extern "C" {
bool condition_load(const void* p,std::size_t n) { return nsc::condition_profile::LoadProfile(p,n); }
std::uint32_t condition_count() { return nsc::condition_profile::Count(); }
std::uint32_t condition_total() { return nsc::condition_profile::TotalCount(); }
const nsc::condition_profile::Descriptor* condition_get(std::uint32_t i) { return nsc::condition_profile::Get(i); }
}
