# R204E — native mtob post-load resource-consumer trace

R204D hardware proved `mtobcharsel.xfbin` reaches native SUCCESS_SET and status=2 while the preview remains empty. R204E keeps every R204D read-only hook and additionally traces:

- `main+0x1207B38`: completed resource lookup by file path (`RESOURCE_LOOKUP`)
- `main+0x120A3D4`: lower-level resource/chunk resolution (`CHUNK_LOW`)

`SUCCESS_SET` maps each completed resource pointer back to its source path, allowing `CHUNK_LOW` to identify direct consumers even if they bypass `ccGetChunkBinary(main+0x3EAE70)`.

No main override, CPK bind, ID patch, path rewrite, forced status, return override, or gameplay patch is installed.

Expected startup marker:

```
[NSC:R204E] READY installed=1 process_installed=1 completion_writers=1 resource_consumers=1 ...
```

Deploy beside the unchanged R209A real-Tobi-charsel carrier. Hover the native Naruto slot once, close the game, and capture the full log.
