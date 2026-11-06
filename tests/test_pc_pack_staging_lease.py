"""Offline staging ownership regression; NOT engine/CRI/Uzuy integration."""
import argparse,hashlib,subprocess,sys,tempfile
from pathlib import Path
from test_pc_native_pack import case
from portlib.native_cpk_graph import MAIN_SHA256

ROOT=Path(__file__).resolve().parents[1]
CPP=r"""
#include "nsc_pc_pack_lease.hpp"
#include <cassert>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <type_traits>
#include <vector>
int main(int argc,char** argv) {
    static_assert(!std::is_copy_constructible<NSCPcPackLease>::value);
    static_assert(!std::is_copy_assignable<NSCPcPackLease>::value);
    static_assert(!std::is_move_constructible<NSCPcPackLease>::value);
    static_assert(!std::is_move_assignable<NSCPcPackLease>::value);
    assert(argc==2);
    std::ifstream in(argv[1],std::ios::binary);
    std::vector<char> src((std::istreambuf_iterator<char>(in)),{});
    assert(!src.empty());
    std::vector<std::uint8_t> arena(src.size()+64,0x5A);
    NSCPcPackLease lease{};
    NSCPcRawRow row{77,77,77,77};
    assert(!lease.row(0,0,&row) && row.offset==77);
    assert(!lease.bind(arena.data(),src.size()-1,src.data(),src.size()));
    assert(!lease.bound && arena[0]==0x5A);
    // Reject caller storage that overlaps lease control state, including
    // partial overlaps, without changing the object or the source pack.
    const auto source_before=src;
    assert(!lease.bind(&lease,sizeof(lease)+src.size(),src.data(),src.size()));
    assert(!lease.bound && lease.arena==nullptr && lease.capacity==0);
    auto* overlapping_lease_storage=reinterpret_cast<std::uint8_t*>(&lease)+sizeof(lease)-1;
    assert(!lease.bind(overlapping_lease_storage,src.size(),src.data(),src.size()));
    assert(!lease.bound && lease.length==0 && src==source_before);
    assert(!lease.bind(src.data(),src.size(),src.data(),src.size()));
    assert(!lease.bound);
    // Source located in the unused tail of the destination arena must fail.
    std::vector<std::uint8_t> overlapping(src.size()*2+64,0x5A);
    std::memcpy(overlapping.data()+src.size()+8,src.data(),src.size());
    assert(!lease.bind(overlapping.data(),overlapping.size(),
                       overlapping.data()+src.size()+8,src.size()));
    assert(!lease.bound);
    std::vector<char> corrupted=src;
    corrupted.back()^=1;
    assert(!lease.bind(arena.data(),arena.size(),corrupted.data(),corrupted.size()));
    assert(!lease.bound && arena[0]==0x5A);
    assert(lease.bind(arena.data(),arena.size(),src.data(),src.size()));
    assert(lease.bound && lease.length==src.size());
    assert(!lease.bind(arena.data(),arena.size(),src.data(),src.size()));
    assert(lease.row(0,0,&row));
    assert(!lease.row(9,0,&row));
    assert(!lease.row(0,0xffffffffu,&row));
    auto saved=row;
    arena[lease.length-1]^=1;
    assert(!lease.row(0,0,&row));
    assert(row.offset==saved.offset && row.length==saved.length);
    lease.unbind();
    assert(!lease.bound && lease.arena==nullptr && lease.length==0);
    assert(!lease.row(0,0,&row));
    assert(lease.bind(arena.data(),arena.size(),src.data(),src.size()));
    assert(lease.row(0,0,&row));
    // Copy a validated row to a disjoint consumer-owned output buffer.
    std::vector<std::uint8_t> consumer(4096,0xA5);
    std::size_t copied=999;
    assert(lease.copy_row(0,0,consumer.data(),consumer.size(),&copied));
    assert(copied==row.length && copied>0);
    // The row view is family-relative; compare the actual copied payload.
    const std::size_t family_dir=64u;
    const auto read32=[](const std::uint8_t* p) -> std::uint32_t {
        return std::uint32_t(p[0]) | (std::uint32_t(p[1])<<8) |
               (std::uint32_t(p[2])<<16) | (std::uint32_t(p[3])<<24);
    };
    const std::size_t family_base=read32(arena.data()+family_dir);
    assert(family_base<=lease.length && row.offset<=lease.length-family_base);
    assert(row.length<=lease.length-family_base-row.offset);
    assert(std::memcmp(consumer.data(),arena.data()+family_base+row.offset,copied)==0);
    assert(consumer[copied]==0xA5);
    const auto consumer_before=consumer;
    copied=0xBADu;
    assert(!lease.copy_row(9,0,consumer.data(),consumer.size(),&copied));
    assert(copied==0xBADu && consumer==consumer_before);
    assert(!lease.copy_row(0,0,consumer.data(),1,&copied));
    assert(copied==0xBADu && consumer==consumer_before);
    assert(!lease.copy_row(0,0,arena.data(),arena.size(),&copied));
    assert(copied==0xBADu && consumer==consumer_before);
    // Metadata pointer aliasing the validated pack or output must fail closed.
    auto* length_in_arena=reinterpret_cast<std::size_t*>(arena.data()+lease.length);
    const auto arena_before=arena;
    assert(!lease.copy_row(0,0,consumer.data(),consumer.size(),length_in_arena));
    assert(arena==arena_before && consumer==consumer_before);
    auto* length_in_output=reinterpret_cast<std::size_t*>(consumer.data()+2048);
    assert(!lease.copy_row(0,0,consumer.data(),consumer.size(),length_in_output));
    assert(arena==arena_before && consumer==consumer_before);
    assert(copied==0xBADu);
    // Reject metadata aliases to the lease's own control fields, including
    // pointers to capacity/length: otherwise a successful copy corrupts state.
    assert(!lease.copy_row(0,0,consumer.data(),consumer.size(),&lease.length));
    assert(lease.bound && lease.length==src.size());
    assert(!lease.copy_row(0,0,consumer.data(),consumer.size(),&lease.capacity));
    assert(lease.capacity==arena.size() && consumer==consumer_before);
    assert(copied==0xBADu);
    lease.unbind();
    std::puts("PC_PACK_STAGING_LEASE_PASS 45 NO_ENGINE_ABI");
}
"""
def run(main,out):
    assert hashlib.sha256(main.read_bytes()).hexdigest()==MAIN_SHA256
    with tempfile.TemporaryDirectory() as d:
        folder=Path(d)
        _,candidate,_,_=case(folder,main)
        program=folder/"lease_test.cpp"
        program.write_text(CPP)
        obj=folder/"sha.o"
        source=ROOT/"overlay/source/program"
        subprocess.run(["gcc","-O2","-c",str(source/"nsc_sha256.c"),"-o",str(obj)],check=True)
        binary=folder/"lease_test"
        subprocess.run(["g++","-std=c++17","-O2","-Wall","-Wextra","-Werror",
            "-I",str(source),str(program),str(source/"nsc_pc_pack.cpp"),
            str(source/"nsc_pc_raw.cpp"),str(obj),"-o",str(binary)],check=True)
        cp=subprocess.run([str(binary),str(candidate/"pc_native_sources.pack")],
            text=True,capture_output=True,check=True)
        assert "PC_PACK_STAGING_LEASE_PASS 45 NO_ENGINE_ABI" in cp.stdout
        out.mkdir(parents=True,exist_ok=True)
        (out/"pc_pack_staging_lease.txt").write_text(cp.stdout)
        print(cp.stdout,end="")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    run(args.main,args.output)
