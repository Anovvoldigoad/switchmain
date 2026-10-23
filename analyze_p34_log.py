#!/usr/bin/env python3
"""P34 parser: correlate XFBIN PROCESS scopes and FILE_OPEN by Switch thread ID.

P34 native hook emits PROCESS_BEGIN, FILE_OPEN and PROCESS_END on the same
thread. Nested scopes are supported. Never infer a failed open from missing
events, null thread IDs, or truncated logs.
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

EVENT = re.compile(r"\[NSC:P34\]\s+(PROCESS_BEGIN|FILE_OPEN|PROCESS_END)\s")
FIELDS = {
    "PROCESS_BEGIN": re.compile(
        r"tid=(\d+) attempt=(\d+) path=(.*?) owner=\S+ readctx=\S+ load=\S+"),
    "FILE_OPEN": re.compile(
        r"tid=(\d+) path=(.*?) request=\S+ slot=(\d+) result=(\d+)"),
    "PROCESS_END": re.compile(
        r"tid=(\d+) attempt=(\d+) path=(.*?) status=(\d+) readerr=(\d+)"),
}

def parse(lines):
    events = []
    for line_no, line in enumerate(lines, 1):
        matched = EVENT.search(line)
        if not matched:
            continue
        kind = matched.group(1)
        fields = FIELDS[kind].search(line, matched.end())
        if not fields:
            events.append({"kind": "UNPARSED", "line": line_no,
                           "source_kind": kind, "raw": line})
            continue
        if kind == "FILE_OPEN":
            tid, path, slot, result = fields.groups()
            event = {"tid": int(tid), "path": path, "slot": int(slot),
                     "open_result": int(result)}
        elif kind == "PROCESS_BEGIN":
            tid, attempt, path = fields.groups()
            event = {"tid": int(tid), "attempt": int(attempt), "path": path}
        else:
            tid, attempt, path, status, readerr = fields.groups()
            event = {"tid": int(tid), "attempt": int(attempt), "path": path,
                     "status": int(status), "readerr": int(readerr)}
        events.append({"kind": kind, "line": line_no, **event})
    return events


def summarize(events):
    stacks = defaultdict(list)
    completed = []
    anomalies = []
    for event in events:
        kind = event["kind"]
        if kind == "UNPARSED":
            anomalies.append(event)
            continue
        tid = event["tid"]
        if not tid:
            anomalies.append({"issue": "UNKNOWN_THREAD_ID", **event})
            continue
        stack = stacks[tid]
        if kind == "PROCESS_BEGIN":
            stack.append({"tid": tid, "attempt": event["attempt"],
                          "path": event["path"], "begin_line": event["line"],
                          "opens": []})
            continue
        if kind == "FILE_OPEN":
            if not stack:
                anomalies.append({"issue": "ORPHAN_OPEN", **event})
            else:
                stack[-1]["opens"].append(event)
            continue
        if not stack:
            anomalies.append({"issue": "ORPHAN_END", **event})
            continue
        scope = stack[-1]
        if (scope["attempt"] != event["attempt"] or
                scope["path"] != event["path"]):
            anomalies.append({"issue": "MISMATCHED_END", **event,
                              "expected_attempt": scope["attempt"],
                              "expected_path": scope["path"]})
            continue
        stack.pop()
        opens = scope["opens"]
        matching = [x for x in opens if x["path"] == scope["path"]]
        other = [x for x in opens if x["path"] != scope["path"]]
        values = {x["open_result"] for x in matching}
        if other:
            classification = "OTHER_PATH_OPEN_INSIDE_SCOPE"
        elif not matching:
            classification = "NO_MATCHING_OPEN_OBSERVED"
        elif len(matching) != 1:
            classification = "MULTIPLE_OPENS_INSIDE_SCOPE"
        elif event["status"] == 5 and values == {0}:
            classification = "OPEN_FAIL"
        elif event["status"] == 5 and values == {1} and event["readerr"] == 1:
            classification = "XFBIN_READ_FAIL"
        elif event["status"] == 2 and values == {1}:
            classification = "LOADED"
        elif event["status"] == 5:
            classification = "STATUS5_OTHER"
        else:
            classification = "OTHER_STATUS"
        completed.append({
            "tid": tid, "attempt": scope["attempt"], "path": scope["path"],
            "begin_line": scope["begin_line"], "end_line": event["line"],
            "status": event["status"], "readerr": event["readerr"],
            "open_results": [x["open_result"] for x in matching],
            "other_path_opens": [x["path"] for x in other],
            "classification": classification,
        })
    incomplete = [scope for stack in stacks.values() for scope in stack]
    return {"completed": completed, "anomalies": anomalies,
            "incomplete": incomplete,
            "limitations": [
                "Only captured P34 hook events are analyzed; trace budgets are finite.",
                "No observed FILE_OPEN is not proof that the file could not open.",
                "Status 2 is observed state, not proof of a playable character.",
                "A native crash can truncate an in-flight PROCESS scope."
            ]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = summarize(parse(args.log.read_text(errors="replace").splitlines()))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for item in result["completed"]:
            print(f'{item["classification"]}: attempt={item["attempt"]} '
                  f'tid={item["tid"]} path={item["path"]} '
                  f'status={item["status"]} readerr={item["readerr"]}')
        print(f'anomalies={len(result["anomalies"])} '
              f'incomplete={len(result["incomplete"])}')
        for warning in result["limitations"]:
            print("NOTE:", warning)


if __name__ == "__main__":
    main()
