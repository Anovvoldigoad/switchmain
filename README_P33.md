# P33 — attempt-scoped loader diagnostics

P32's analyzer classifies an entire path as OPEN_FAIL if any historic FILE_OPEN
failed. P31 already showed retries for mtobbod1acc, so path-lifetime aggregation
can hide later recovery.

This change adds analyze_p33_log.py and unit tests without changing binary
hooks, resources, or loader behavior. It consumes existing P32 logs. Each
PROCESS observation is classified only using unconsumed preceding FILE_OPEN
events for that same path. Concurrency and repeated in-flight requests cannot
be definitively correlated using P32 fields, so those results explicitly remain
provisional; native request IDs are required for decisive classification.

Run: python3 -m unittest -v test_analyze_p33.py
Usage: python3 analyze_p33_log.py fresh_uzuy_log.txt --json

This is diagnostic tooling, NOT a playable mod or runtime fix.
