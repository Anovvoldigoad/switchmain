#include "nsc_factory.hpp"
static nsc::factory::Registry registry;
extern "C" {
int load_profile(const void* p, std::size_t n) { return registry.Load(p,n); }
std::uint32_t resolve_profile(std::uint32_t id) { return registry.Resolve(id); }
std::uint32_t count_profile() { return registry.Count(); }
}
