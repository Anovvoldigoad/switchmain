# R249 static audit — post-identity resource/chunk/allocation corridor

Baseline: clean Switch v1.70 `main`, SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.

R248 hardware proves target identity 46 resolves non-null but `model+0x90` remains null. Static recovery of `main+0x6EAC24` identifies the next exact gates:

```text
6EACF8 BL  1207B38   ; file resource lookup(manager,path)
6EACFC CBZ X0,6EADAC ; null => skip ready object producer
...
6EAD50 BL  120A3D4   ; chunk/resource typed-key lookup
6EAD54 CBZ X0,6EADAC ; null => skip ready object producer
...
6EAD6C BL  116AE60   ; allocator, size 0x3B0 in this call
6EAD70 MOV X21,X0
6EAD74 CBZ X0,6EAD90
...
6EAD98 STR X21,[X19,#0x90]
```

R249 hooks only the target model-init scope and observes:
- file lookup path/result;
- chunk type/key/result;
- allocator size/result;
- model identity and `ready90` before/after native init.

No return override, state write, path rewrite, CPK bind, ID remap, or gameplay patch is introduced.
