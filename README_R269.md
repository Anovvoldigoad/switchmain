# R269 — Base Visual Population Trace

Use after R268 log43.

R268 proved the base visual list is allocated (`count=1`) but entry 0 stays NULL, so the child visibility gate is never reached.

R269 is read-only and answers exactly why entry 0 is NULL:
- source link `secondary+0x188 <- model+0x90`;
- visual population method `main+0x117BA00`;
- candidate/descriptor matcher `main+0x11A2D4C`;
- child0 before/after population.

Deploy with the same R263 diagnostic `sound.cpk`, clean `main`, external Tobi CPK OFF, ID281 OFF.
