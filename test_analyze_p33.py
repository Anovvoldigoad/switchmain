#!/usr/bin/env python3
import unittest
from analyze_p33_log import parse, classify

def line(kind,path,other):
    return f"23:10:20 [NSC:P32] {kind} path={path} {other}"

class P33Tests(unittest.TestCase):
    def test_retry_recovery_not_poisoned(self):
        p="data/spc/mtobbod1acc.bin.xfbin"
        rows=[line("FILE_OPEN",p,"slot=0 result=0"),
              line("PROCESS",p,"owner=0x1 status=5 readerr=0"),
              line("FILE_OPEN",p,"slot=0 result=1"),
              line("PROCESS",p,"owner=0x2 status=2 readerr=0")]
        a=classify(parse(rows))["attempts"]
        self.assertEqual([x["classification"] for x in a],
                         ["OPEN_FAIL_OBSERVED","LOAD_SUCCESS_OBSERVED"])
    def test_parse_real_format_and_read_fail(self):
        p="data/spc/mtobbod1_col3.xfbin"
        rows=[f"[NSC:P32] FILE_OPEN request=0x14 path={p} slot=1 result=1",
              f"[NSC:P32] PROCESS path={p} owner=0x1 readctx=0x2 load=0x3 status=5 readerr=1"]
        self.assertEqual(classify(parse(rows))["attempts"][0]["classification"],"XFBIN_READ_FAIL_OBSERVED")
    def test_missing_open_is_not_failure_classification(self):
        p="data/spc/mtobbod1_col3.xfbin"
        a=classify(parse([line("PROCESS",p,"owner=0x1 status=5 readerr=1")]))["attempts"]
        self.assertEqual(a[0]["classification"],"UNCORRELATED_NO_OPEN")
    def test_mixed_opens_mark_ambiguous(self):
        p="data/spc/mtob.xfbin"
        a=classify(parse([line("FILE_OPEN",p,"slot=0 result=0"),line("FILE_OPEN",p,"slot=1 result=1"),line("PROCESS",p,"owner=0x1 status=5 readerr=1")]))["attempts"]
        self.assertEqual(a[0]["classification"],"AMBIGUOUS_MULTIPLE_OPENS")
    def test_unpaired_open_not_assumed_success(self):
        p="data/spc/mtob.xfbin"
        r=classify(parse([line("FILE_OPEN",p,"slot=0 result=1")]))
        self.assertEqual(len(r["unpaired_opens"]),1)
        self.assertEqual(r["attempts"],[])
if __name__=="__main__": unittest.main()
