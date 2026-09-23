from pathlib import Path
import hashlib
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "artifact")
sub = root / "atmosphere/contents/0100FA10190A0000/exefs/subsdk9"
main = root / "atmosphere/contents/0100FA10190A0000/exefs/main"
rest = root / "restore/atmosphere/contents/0100FA10190A0000/exefs/main"

for path in (sub, main, rest):
    if not path.is_file():
        raise SystemExit(f"MISSING {path}")

sub_data = sub.read_bytes()
if sub_data[:4] != b"NSO0":
    raise SystemExit("subsdk9_NSO0=FAIL")
if len(sub_data) <= 10 * 1024:
    raise SystemExit(f"subsdk9_SIZE=FAIL size={len(sub_data)}")
print(f"subsdk9_NSO0=PASS size={len(sub_data)}")

expected = {
    main: "1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0",
    rest: "2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9",
}
for path, want in expected.items():
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    status = "PASS" if got == want else "FAIL"
    print(f"{path} sha256={got} {status}")
    if got != want:
        raise SystemExit(1)

print("P89A_ARTIFACT_VERIFY=PASS")
