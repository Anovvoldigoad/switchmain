NSC2Switch P41A — GitHub Actions build kit

YES: this package includes the P41A subsdk9/exlaunch source overlay:
  overlay/source/program/main.cpp
  overlay/source/program/nsc_cpk_bridge.cpp
  overlay/source/program/nsc_cpk_bridge.hpp

GitHub build:
1. Create/open a GitHub repository.
2. Upload the CONTENTS of this folder to repository root (keep .github hidden folder).
3. Commit/push.
4. Open Actions -> "Build NSC P41A condition517 Event121 self" -> Run workflow.
5. Download artifact "NSC-P41A-condition517-event121-self".
6. Deploy BOTH generated files together:
   atmosphere/contents/0100FA10190A0000/exefs/main
   atmosphere/contents/0100FA10190A0000/exefs/subsdk9

The workflow clones pinned exlaunch commit 229bbd6, overlays these P41A sources,
builds subsdk9 using devkitPro/devkitA64, and packages it with the already audited
P41A main SHA256:
  407ff7247a2c70941c05eb2cdfbd65a2a25fffc247845274b096ed0b5aee6ae7

Do NOT mix the generated P41A subsdk9 with P40 main or P40 subsdk9.
Keep the existing P33A Sorted=0 CPK/RomFS setup unchanged.
