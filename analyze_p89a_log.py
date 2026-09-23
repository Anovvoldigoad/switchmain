import re,sys,collections
p=sys.argv[1]
rx=re.compile(r'\[NSC:P89A\] ACTOR_PRED .*?char=(\d+).*?bda4=(\d+) bdc8=(\d+) native=(\d+) semantic=(\d+) member=(\d+) bridge=(\d+) out=(\d+)')
c=collections.Counter()
for line in open(p,errors='replace'):
 m=rx.search(line)
 if m: c[tuple(map(int,m.groups()))]+=1
print('P89A_ACTOR_PRED_RECORDS',sum(c.values()))
for k,n in c.most_common(): print(n,k)
