#!/usr/bin/env python3
import unittest
from analyze_p34_log import parse, summarize

def begin(tid, attempt, path):
    return f'[NSC:P34] PROCESS_BEGIN tid={tid} attempt={attempt} path={path} owner=0x1 readctx=0x2 load=0x3'

def opened(tid, path, value):
    return f'[NSC:P34] FILE_OPEN tid={tid} path={path} request=0x1 slot=0 result={value}'

def end(tid, attempt, path, status, err):
    return f'[NSC:P34] PROCESS_END tid={tid} attempt={attempt} path={path} status={status} readerr={err}'

class P34Tests(unittest.TestCase):
    def classify(self, rows):
        return summarize(parse(rows))
    def test_file_open_failure(self):
        p="data/spc/mtobbod1acc.bin.xfbin"
        r=self.classify([begin(12,1,p),opened(12,p,0),end(12,1,p,5,0)])
        self.assertEqual(r["completed"][0]["classification"],"OPEN_FAIL")
    def test_xfbin_read_failure(self):
        p="data/spc/mtobbod1_col3.xfbin"
        r=self.classify([begin(12,1,p),opened(12,p,1),end(12,1,p,5,1)])
        self.assertEqual(r["completed"][0]["classification"],"XFBIN_READ_FAIL")
    def test_retry_recovery(self):
        p="data/spc/mtobbod1acc.bin.xfbin"
        r=self.classify([begin(12,1,p),opened(12,p,0),end(12,1,p,5,0),
                         begin(12,2,p),opened(12,p,1),end(12,2,p,2,0)])
        self.assertEqual([x["classification"] for x in r["completed"]],
                         ["OPEN_FAIL","LOADED"])
    def test_two_threads_interleaved(self):
        p="data/spc/mtob1.xfbin"
        q="data/spc/mtob2.xfbin"
        rows=[begin(12,1,p),begin(13,2,q),
              opened(13,q,1),opened(12,p,0),
              end(12,1,p,5,0),end(13,2,q,2,0)]
        r=self.classify(rows)
        self.assertEqual([x["classification"] for x in r["completed"]],
                         ["OPEN_FAIL","LOADED"])
        self.assertFalse(r["anomalies"])
    def test_nested_scopes(self):
        p="data/spc/mtob1.xfbin"
        q="data/spc/mtob2.xfbin"
        rows=[begin(12,1,p),begin(12,2,q),opened(12,q,1),
              end(12,2,q,2,0),opened(12,p,1),end(12,1,p,2,0)]
        r=self.classify(rows)
        self.assertEqual(len(r["completed"]),2)
        self.assertTrue(all(x["classification"]=="LOADED" for x in r["completed"]))
    def test_unknown_thread_cannot_pair(self):
        p="data/spc/mtob.xfbin"
        r=self.classify([begin(0,1,p),opened(0,p,0),end(0,1,p,5,0)])
        self.assertEqual(len(r["completed"]),0)
        self.assertEqual(len(r["anomalies"]),3)
    def test_incomplete_scope(self):
        p="data/spc/mtob.xfbin"
        r=self.classify([begin(12,1,p),opened(12,p,1)])
        self.assertEqual(len(r["incomplete"]),1)
        self.assertFalse(r["completed"])
    def test_mismatch_does_not_fabricate_pairing(self):
        p="data/spc/mtob.xfbin"
        r=self.classify([begin(12,1,p),opened(12,p,1),end(12,2,p,5,1)])
        self.assertFalse(r["completed"])
        self.assertEqual(r["anomalies"][0]["issue"],"MISMATCHED_END")
        self.assertEqual(len(r["incomplete"]),1)
    def test_other_path_open_flagged(self):
        p="data/spc/mtob.xfbin"
        q="data/spc/mtob-child.xfbin"
        r=self.classify([begin(12,1,p),opened(12,q,0),end(12,1,p,5,0)])
        self.assertEqual(r["completed"][0]["classification"],"OTHER_PATH_OPEN_INSIDE_SCOPE")
if __name__=="__main__":
    unittest.main()
