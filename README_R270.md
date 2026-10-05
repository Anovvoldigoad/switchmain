# R270

Read-only diagnostic following hardware log44.

R269 proved `source188 == model+0x90`, visual population executes, and `main+0x11A2D4C` returns 0, leaving the sole base-visual child slot NULL.

R270 captures the exact fallback compare record at `main+0x11A2E34` and logs descriptor/candidate `{u32 key,u8 type}` without invoking extra game functions. The overwritten native `LDRB W8,[X20,#4]` is replayed exactly.
