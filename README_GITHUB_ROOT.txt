R72B P63A GITHUB REPOSITORY ROOT PACKAGE
========================================

IMPORTANT:
Extract the CONTENTS of this ZIP directly into the root of your GitHub repository.
After extraction the repository must contain exactly:

  .github/workflows/build-subsdk9-p63a.yml
  overlay/source/program/...
  deploy/...
  restore/...
  prepare_exlaunch.sh
  verify_p63a_kit.py

There must NOT be an extra P63A_UJ_ROUTER_FIRST_DIVERGENCE_TRACE_BUILD_KIT/ directory above .github.

Workflow triggers:
- automatically on every push
- manually via Actions -> Build NSC P63A UJ Router First Divergence Trace -> Run workflow
