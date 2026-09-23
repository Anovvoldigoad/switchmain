#!/usr/bin/env python3
import re,sys
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'
for line in open(p,errors='replace'):
    if '[NSC:P90B]' in line or ('[NSC:P59A] PLAY_CALL' in line and re.search(r'index=(700|707|708|709|710|711|712|713|714|740)\b',line)):
        print(line.rstrip())
