# R204T Per-Resource Stream Forensic Trace

R204T fixes the R204S global stream-log budget bug. R204S proved bod1 and bod1acc both pass FILE_OPEN, READ_DISPATCH, STREAM_ATTACH and READ_HEADER, then enter READ_PAYLOAD immediately before the NCE storm. However, the 5mdr control consumed the global STREAM_READ budget before the body requests began.

R204T preserves the same 9 boot-safe read-only hooks but allocates STREAM_READ quotas independently: control 5mdr=24 calls, bod1=1024, bod1acc=1024, other bod1 family=256. ENTER/EXIT use the same per-call slot so a missing EXIT is unambiguous.

No CPK bind, path rewrite, state override, gameplay patch, ID patch, main patch, or return override is installed.
