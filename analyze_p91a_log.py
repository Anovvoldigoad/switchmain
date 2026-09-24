import sys,re
for line in open(sys.argv[1],errors='ignore'):
    if '[NSC:P91A] HANDOFF' in line: print(line,end='')
