import argparse
import json
from pathlib import Path

from portlib.native_fileload_inbound_args import inspect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = inspect(args.main.read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    path = args.output / "native_fileload_inbound_args.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print("FILELOAD_INBOUND_ARGUMENTS", json.dumps({
        "status": report["status"],
        "main_sha256": report["original_main_sha256"],
        "caller": report["incoming_direct_calls"],
        "origins": report["caller_window"]["possible_reaching_definitions"],
        "ownership_verified": report["object_type_or_ownership_verified"],
        "native_consumer_abi_verified": report["native_consumer_abi_verified"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
