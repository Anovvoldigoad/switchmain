"""Build an original-ZIP-backed source-data pack for AArch64 PC raw readers."""
import argparse,json
from pathlib import Path
from portlib.pc_nsc_param_pack import assemble

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=assemble(json.loads(args.spec.read_text()),args.output)
    print("PC_NATIVE_SOURCE_PACK_STAGED",result["family_count"],
          result["packed_sha256"],"NO_ENGINE_ABI_OR_UZUY")
if __name__=="__main__":
    main()
