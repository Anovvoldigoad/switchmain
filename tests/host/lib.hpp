#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <stdexcept>
extern std::uintptr_t test_base;
extern std::size_t test_size, test_writes;
struct TestLogger { template<typename... T> void Log(const char*, T...) {} };
inline TestLogger Logging;
namespace exl::util {
struct Range { std::uintptr_t m_Start; std::size_t m_Size; };
struct Module { Range m_Text; };
inline Module GetMainModuleInfo() { return {{test_base, test_size}}; }
namespace modules { inline std::uintptr_t GetTargetStart() { return test_base; } }
}
namespace exl::patch {
struct RandomAccessPatcher {
 template<typename T> void Write(std::uintptr_t off, T value) {
  if(off > test_size || sizeof(T) > test_size - off) throw std::out_of_range("patch");
  std::memcpy(reinterpret_cast<void*>(test_base+off),&value,sizeof(value)); ++test_writes;
 }
 void Flush() {}
};
}
