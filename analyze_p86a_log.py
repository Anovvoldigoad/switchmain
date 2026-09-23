#!/usr/bin/env python3
import re,sys,collections
p=sys.argv[1]
lines=open(p,errors='replace').read().splitlines()
state=[x for x in lines if '[NSC:P86A] STATE' in x]
ctrl=[x for x in lines if '[NSC:P86A] CTRL' in x]
ip=[x for x in lines if '[NSC:P86A] INPUT_PRED' in x]
ap=[x for x in lines if '[NSC:P86A] ACTOR_PRED' in x]
f58=[x for x in lines if '[NSC:P85A] F58' in x]
print(f'P86 records state={len(state)} ctrl={len(ctrl)} input_pred={len(ip)} actor_pred={len(ap)} inherited_f58={len(f58)}')
pat=lambda n,s: re.search(rf'\b{n}=([^ ]+)',s).group(1) if re.search(rf'\b{n}=([^ ]+)',s) else '?'
print('\nINPUT_PRED census:')
c=collections.Counter((pat('char',x),pat('stage',x),pat('phase',x),pat('bdc8',x),pat('ret',x),pat('hit404',x),pat('hit408',x)) for x in ip)
for k,v in c.most_common(): print(v,k)
print('\nACTOR_PRED census:')
c=collections.Counter((pat('char',x),pat('stage',x),pat('phase',x),pat('bdc8',x),pat('ret',x)) for x in ap)
for k,v in c.most_common(): print(v,k)
print('\nSTATE transitions:')
for x in state:
    print('char',pat('char',x),'phase',pat('phase',x),'bdc8',pat('bdc8',x),'hit404',pat('hit404',x),'hit408',pat('hit408',x))
print('\nInherited P85 F58:')
for x in f58:
    print('seq',pat('seq',x),'char',pat('char',x),'ret',pat('ret',x),'bdc8',pat('bdc8',x),'e98',pat('e98',x))
