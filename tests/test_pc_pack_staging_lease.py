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
#include <cstdio>
#include <fstream>
#include <iterator>
#include <vector>
int main(int argc,char** argv) {
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
    assert(!lease.bind(src.data(),src.size(),src.data(),src.size()));
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
    assert(row.offset==saved.offset && row.size==saved.size);
    lease.unbind();
    assert(!lease.bound && lease.arena==nullptr && lease.length==0);
    assert(!lease.row(0,0,&row));
    assert(lease.bind(arena.data(),arena.size(),src.data(),src.size()));
    assert(lease.row(0,0,&row));
    lease.unbind();
    std::puts("PC_PACK_STAGING_LEASE_PASS 15 NO_ENGINE_ABI");
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
        assert "PC_PACK_STAGING_LEASE_PASS 15 NO_ENGINE_ABI" in cp.stdout
        out.mkdir(parents=True,exist_ok=True)
        (out/"pc_pack_staging_lease.txt").write_text(cp.stdout)
        print(cp.stdout,end="")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    run(args.main,args.output)
