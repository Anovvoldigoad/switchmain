# R253 static audit — Load::enter child-vector construction

Clean original Switch v1.70 `main` SHA256:
`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

## R252 correction
R252 showed `[self+0x188..0x190)` empty in Wait. Static recovery proves Wait does not create that vector. `Wait::update @ main+0x549B80` only consumes it.

## Producer
The vector is populated by `main+0x549610` during the large `Load::enter @ main+0x548094` path.

`main+0x549610(self, source, mode)`:
- validates required globals;
- resolves the current character descriptor with `main+0x64ED30` using `[self+0xCC]`;
- allocates a 0xE8-byte child;
- initializes child fields including mode at `child+0xE0`;
- appends the child pointer to `[self+0x188..0x190)`;
- fast append end-pointer store is at `main+0x54970C`;
- vector growth replacement store pair is at `main+0x5497C0` and capacity at `main+0x5497C4`.

Direct producer callsites in clean main:
- `0x548F4C` mode 1
- `0x548FE0` mode 2
- `0x549078` mode 3
- `0x549110` mode 4
- `0x54924C` mode 0
- `0x54BC18` additional caller

## Upstream candidate pipeline
Inside Load::enter:
- source candidate vector builder call: `main+0x548DE4 -> main+0x3FCE60`;
- candidate getter/resolver used before each producer call: `main+0x3FBC4C`;
- if no producer call occurs, the child vector necessarily remains empty.

## R253 read-only split
R253 traces exactly:
1. target registry capture;
2. Load::enter vector pre/post state;
3. source-list builder output count;
4. candidate resolve input/result;
5. child producer pre/post vector count.

Decision:
- source count 0 -> `LOAD_CHILD_SOURCE_EMPTY`;
- source count >0 but no candidate/producer for target -> `SELECTOR_NO_MATCH`;
- candidate resolve returns null -> `CANDIDATE_RESOLVE_FAIL`;
- producer called but post count unchanged -> `PRODUCER_EARLY_EXIT`;
- producer grows vector -> `CHILD_VECTOR_BUILT` and investigate later clearing/consumption.
