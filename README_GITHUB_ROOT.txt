R73 P64F UJ SEMANTIC BRIDGE — GITHUB REPOSITORY ROOT PACKAGE
=============================================================

Extract the CONTENTS of this ZIP directly into the root of the GitHub repository.
After extraction the repository must contain:

  .github/workflows/build-subsdk9-p64f.yml
  overlay/source/program/...
  deploy/...
  restore/...
  prepare_exlaunch.sh
  verify_p64f_kit.py
  README_P64F.txt
  P64F_STATIC_AUDIT.txt

Do not put an extra wrapper directory above .github.

Workflow triggers:
- automatically on every push
- manually via Actions -> Build NSC P64F UJ Semantic Bridge -> Run workflow

Expected uploaded artifact:
  NSC-P64F-uj-semantic-bridge
