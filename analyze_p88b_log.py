import sys
L=open(sys.argv[1],errors='replace').read().splitlines()
print('P87_READY',sum('[NSC:P87A] READY' in x for x in L));print('P88B_READY',sum('[NSC:P88B] READY' in x for x in L));H=[(i+1,x) for i,x in enumerate(L) if '[NSC:P88B] HELPER' in x];print('P88B_HELPER',len(H))
for i,x in H:
 if 'bda4=3->' in x or 'bda4=4->' in x: print(f'{i}: {x}')
