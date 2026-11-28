2026-11-23 PENDING_HEAD_CI: compressed batch independent verifier now reconstructs exact deterministic literal/runs CRILAYLA bitstream for changed Event236 candidates, rejecting a valid alternate encoder even when decoded bytes and updated SHA match; three encoder modes positive and alternate negative regressions. Code commit 28c95224bc9538dae9dcba85f1e1b437c3cf5500 parent aca1be0f02b7e334768d82d2483523507ff96ecc. Prior compressed push run 45157982290 job 137635718880 COMPLETED SUCCESS raw log inspected; new HEAD CI pending. Synthetic offline only. NSC-ModManager/Toolbox 2.1.2.1 upstream release 2026-08-30; no Switch ABI inference. Original main expected SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not rehashed. Sakura aura107, Event236 marked/unmarked and three false release flags preserved. NEXT inspect compressed workflow push run/job/log for new HEAD, repair failures, then authentic consumer evidence.

2026-11-23 PENDING_HEAD_CI: compressed PRM batch now preserves the exact original CRILAYLA stored bytes for unchanged Event236 members across literal/runs/auto, while changed members still encode and independently roundtrip. New mixed-member, all-encoder, no-encode and SHA regressions; synthetic offline only. Parent 40f8de7c05c193a21b7fc799b28273bf663692c0. Upstream ModManager 2.1.2.1 README blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709, Toolbox README blob 657f161390c4abe8afe10cea11a2b9a28e6bf6b0; generic REA evidence only; pinned original main bytes not available for rehash. No native ABI/ownership/archive precedence/Uzuy proof. Preserve Sakura aura107, Event236 variants and false release flags.

2026-11-23 PENDING_HEAD_CI: ordered factory source validation now rejects unknown source kinds before applying --exclude, preventing invalid excluded source from bypassing kind validation. Regression covers excluded unknown kind; host/Actions HEAD CI not yet verified. Parent cdfbd08e7241b3118506aff161ce8318bdd3a039. This is offline factory input correctness only; no original main rehash, Switch ABI, lifecycle, archive precedence, or Uzuy proof. Preserve Sakura aura107, both Event236 forms and all three false release flags.

2026-11-23 PENDING_HEAD_CI: shared native CPK/FileLoad ARM64 CFG now classifies BLRAA/BLRAB/BLRAAZ/BLRABZ as unresolved authenticated calls and BRAAZ/BRABZ as terminal jumps. FileLoad uses shared edge classification, retains opaque-call SP barrier; regression covers four call and six terminal mnemonics plus existing original-main SHA-guarded CFG tests. Parent d225194e6b18d3b540f12ea3c99adccda350dd5c; local Capstone unavailable (DNS), HEAD Actions log not yet inspected. Upstream ModManager 2.1.2.1 release 502c38d (Switch Projectiles Target), 2.1.2.0 Start/Stop Deflect; Toolbox 2.1.2.1 789fe96; generic REA/CRI references do not prove Switch ABI. Original main expected SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not rehashed. No native consumer ABI, lifecycle, archive precedence or Uzuy proof; Sakura aura107, both Event236 variants and three false release flags untouched. NEXT inspect authentic Foundation push run/job/log for new HEAD; if failing repair; authenticate original main for native consumer proof.

2026-11-23 PENDING_HEAD_CI: ARMv8.3 authenticated indirect BLRAA/BLRAB calls in read-only FileLoad CFG now act as opaque call barriers instead of falsely allowing SP stack witness across call. Positive negative synthetic BLRAA regression uses clang-assembled word 0xd73f092a. Parent 2da3c6f97aa4cdc9856d1686c05062bad761de12; host Capstone unavailable; HEAD push Actions job/log unverified. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not rehashed. Native consumer ABI/ownership/lifecycle/CPK precedence/Uzuy unresolved; Sakura aura107 and both Event236 forms untouched; full_moddingapi=false ready_for_gameplay_test=false emulator_tested=false. NEXT run Foundation CI for HEAD and inspect authentic job logs, then source-pinned native proof.

2026-11-22 PENDING_HEAD_CI: FileLoad CFG backward-edge witness now considers lower-address readers reached after a stack writer, instead of filtering by numeric PC order; synthetic positive backward branch and negative disconnected edge added. Parent a4f9056bc09985362c96065bdccab8b2867a2fce; host Capstone unavailable; HEAD Actions job/log not verified. Read-only static possibility only, no consumer ABI, ownership, lifecycle, archive precedence or Uzuy proof. Original main expected SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not rehashed. Sakura aura107, marked/unmarked Event236 untouched; full_moddingapi=false ready_for_gameplay_test=false emulator_tested=false. NEXT inspect Foundation push job log for new HEAD and fix failures; continue original main consumer proof.

2026-11-22 PENDING_HEAD_CI: fix ordered factory publication race via Linux renameat2 RENAME_NOREPLACE (unsupported hosts fail closed); regression creates destination after staging, asserts sentinel preservation and cleanup. Parent 346c2b698fbf181a2abcbbbf42973cd336a17602; HEAD CI/log not verified; native consumer ABI/lifecycle/archive precedence and Uzuy unresolved, original main not rehashed. Sakura aura107, both Event236 variants untouched; full_moddingapi=false ready_for_gameplay_test=false emulator_tested=false. NEXT verify HEAD Actions push log and fix failures.

2026-11-22 PENDING_HEAD_CI: ordered factory output now stages factory.profile and factory_ordered_report.json in a sibling temporary directory and publishes the pair by rename, cleaning staged files on write failure. New test injects report-write failure, checks no partial output/stage, and rejects existing destination. Code commits 53e73a0, ff89765, 4a882d1; parent 00cb3ec6db5de8745dd70fe2a3fce37d6a4eee07. GitHub Actions HEAD push run/job/log not verified; host/ARM64/Uzuy not claimed. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not rehashed. Consumer ABI/lifecycle/archive precedence unresolved; Sakura aura107 and both Event236 variants untouched; full_moddingapi=false ready_for_gameplay_test=false emulator_tested=false. NEXT obtain authentic HEAD factory workflow job log, fix failures, then prove consumer from original bytes.

2026-11-21 PENDING_HEAD_CI: code dba80ee828b8bf759216258b4c47b785a9da1b7e (parent a8b18362cc33d47bcbf183b23713d127a1bab1ec) now attributes baseline add/remove/replace operations to before_source/after_source when SHA256-pinned baseline report is provided. Added positive add/remove/replace provenance and --verify-output replay regression. GitHub connector can read previous job 136800592579 log (run 44889037329, prior commit only), but HEAD push workflow run/job/log is not accessible yet. No host test execution or HEAD CI PASS claimed. ModManager and Toolbox tag 2.1.2.1 READMEs checked (blob SHA 8e9560b2 and 657f1613); original Switch main not available for byte rehash; native ABI/ownership/lifecycle/CPK precedence/Uzuy unresolved. Original main expected SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. Sakura aura107, marked/unmarked Event236 untouched; full_moddingapi=false ready_for_gameplay_test=false emulator_tested=false. NEXT inspect exact HEAD push Actions logs and repair failures; source-authenticate native consumer before any hook.

2026-11-21 PENDING_HEAD_CI: ordered factory now accepts SHA256-pinned --baseline-report alongside --baseline-profile and records same-selector source transfers (operation=transfer), with baseline report/profile cross-check and complete unique effective-owner validation. Source commit 981bc6cba42c58e88a1f9eecc2c5fbb9fc65e2ff; test commit d51d309ca047c57e196df4dde5478eaea1c2fddb; parent 3f98581455a71d688b889901a95633da777dbfb6. Added regression for transfer, replay, tampered report, missing baseline. GitHub Actions push runs/logs for new HEAD not verified; local clone blocked by DNS, no PASS. Upstream ModManager/Toolbox 2.1.2.1 referenced, no Switch ABI proof; original main pinned SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not rehashed. Sakura aura107, marked/unmarked Event236 untouched. full_moddingapi=false ready_for_gameplay_test=false emulator_tested=false. NEXT read exact HEAD push Actions job logs, fix regressions, prove native consumer ABI/lifecycle before hooks.

2026-11-21 PENDING_HEAD_CI: ordered factory adds SHA256-pinned baseline semantic delta (add/remove/replace owners), exact replay-verifiable alongside source ledger; regression covers all three operations, tampered baseline, immutable output. Prior HEAD 28adaecdc7abdcc24c2f1e364d989e989d8984d2 five push workflows COMPLETED SUCCESS; authentic job logs inspected: ordered 44889037329/136800592579, foundation 44889037296/136800592664, factory 44889037288/136800592639, compressed 44889037273/136800592614, MovesetPlus 44889037281/136800592677. Primary source ModManager 2.1.2.1 README blob 8e9560b2, Toolbox 2.1.2.1 README blob 657f1613, REA main README blob 93e1e272; none proves Switch consumer ABI. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 pinned but bytes not rehashed; no runtime hook, Sakura aura107/Event236 variants untouched; all three release flags false. NEXT inspect exact new HEAD push run/jobs/logs; native consumer ABI/lifecycle/Uzuy unresolved.
## 2026-11-21 — Effective factory ownership attribution (PENDING HEAD CI)
2026-11-21 PENDING_HEAD_CI: ordered factory report now includes effective_owners (last-writer source/kind/selector per owner, sorted) so multi-mod attribution is machine-readable and replay-verified. Code 21e19d6b07c3b09126df15823bdc7eddd572fa63 parent 919ced4db2fa603e682ae8ea730a49ff02fc6520. Prior HEAD Ordered Factory run 44875549776 job 136759337635 COMPLETED SUCCESS, authentic log read: 8 tests OK. New HEAD CI not verified. No native ABI, original main rehash, archive precedence or Uzuy proof; SHA256 original main 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 pinned; Sakura aura107/Event236 marked/unmarked untouched; full_moddingapi=false ready_for_gameplay_test=false emulator_tested=false. NEXT verify new HEAD push CI authentic log, then consumer evidence.

## 2026-11-21 — Ordered factory replay verifier (PENDING HEAD CI)
2026-11-21 PENDING_HEAD_CI: --verify-output authenticates ordered raw/profile sources including excluded mods, replays exact factory.profile bytes, provenance ledger, and directory membership; positive/negative tamper CLI regression added. Parent 9329bfb9eacecb9986f1b0a305481179851e297f. Primary ModManager 2.1.2.1 README blob 8e9560b2, Toolbox 2.1.2.1 README blob 657f1613; original main bytes and REA unavailable this run. Editor-only, native consumer/ownership/Uzuy unverified. Original main pinned SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not rehashed; Sakura aura107, Event236 marked/unmarked untouched; full_moddingapi=false ready_for_gameplay_test=false emulator_tested=false. NEXT read HEAD Actions job logs and repair if failing.

## 2026-11-21 — Ordered mixed factory mod removal (PENDING HEAD CI)
2026-11-21 PENDING_HEAD_CI: ordered mixed raw PC/profile factory composer now supports --exclude LABEL to remove any mod and deterministically replay surviving sources in original order, restoring shadowed selectors. Every excluded source remains SHA256-authenticated, unknown/duplicate exclusions fail closed, provenance records excluded status. 3 positive/negative/CLI tests added. Parent ecf1e9099c2821fad2050becd1c0032ca4ecae25; host/Actions HEAD CI not yet verified. Upstream ModManager 2.1.2.1 release 502c38d, Toolbox 2.1.2.1 release 789fe96, REA generic reference; no native Switch ABI inference. Pinned original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not rehashed. Sakura aura107, Event236 marked/unmarked untouched; full_moddingapi=false ready_for_gameplay_test=false emulator_tested=false. NEXT inspect exact HEAD Actions ordered-factory job authentic log; fix if failing. Native consumer ownership/lifecycle/archive precedence/Uzuy remain unresolved.

2026-11-21 PENDING_HEAD_CI: explicit interleaved raw PC specialCondParam and SHA256-authenticated factory.profile multi-mod order implemented in tools/compose_ordered_factory.py; positive/negative/boundary/CLI regressions in tests/test_factory_ordered_sources.py. Parent de5aeaf7c31a2ec73fd0cb7f750028e0105b6fd5; code 766dedb0e81ece2828ca16fd72fb6fdba9d81a16. Existing compiler grouped raw before profile and could not represent profile -> raw priority. New standalone CLI processes exact source order; no native consumer. Primary references: https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1 (release 502c38d, current source 276116e), https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1 (789fe96), REA reference from previous pinned evidence only; no original main rehash this run. Switch original main expected SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; ABI, ownership, archive precedence, Uzuy unresolved. Sakura aura107, Event236 marked/unmarked untouched. full_moddingapi=false ready_for_gameplay_test=false emulator_tested=false. HEAD CI pending; inspect authentic workflow job log before PASS.

2026-11-21 PENDING_HEAD_CI: mixed factory composition now accepts authenticated --profile LABEL PATH SHA256 after raw PC specialCondParam inputs; deterministic last-wins or reject, provenance and positive/negative/boundary regression. Code 622d65c890359be4dbaaac2d2b32c29bd5953ee6 parent 66847664b781ae31f5b7a35e2ddbfdbb66a71736. Parent HEAD four push workflows COMPLETED SUCCESS, authentic logs inspected: Foundation 44855979418/136698177683; factory 44855979405/136698177499; compressed 44855979396/136698177373; MovesetPlus 44855979480/136698177758. New HEAD workflow pending. Offline class-selector composition only; no Switch native consumer, original main rehash or Uzuy. SHA guard, Sakura aura107, Event236 variants and three false flags preserved. NEXT inspect new HEAD factory job log and fix failures; prove consumer ABI from original bytes before hooks.
2026-11-21 PENDING_HEAD_CI: ordered SHA256 authentication of raw PC factory inputs, report provenance and negative CLI regression. Code b378773d0b6917f16e3b1a016ff222bf8dab5863; parent 94069ee01aa1873173a5c3d49f5ad69df6744bd9. Prior HEAD factory 44836719730/136634842690 and foundation 44836719662/136634842448 COMPLETED SUCCESS authentic logs inspected. New HEAD CI pending. Offline editor only, original main pinned not rehashed, no native consumer or Uzuy proof. Sakura aura107, Event236 variants, three release flags unchanged.
2026-11-21 PENDING_HEAD_CI: code 8292c004bffc5bedc44f34aad5672552c3941fc3 (parent 13249b458ca4bc9c5f3f5a327791b6c87822b497) adds --conflicts reject/last to raw PC specialCondParam factory compiler. Strict mode rejects duplicate final Switch owners across/within sources and owner-map collisions before output; default last-wins preserved. New regression tests/test_factory_raw_conflicts.py + factory workflow step. Prior HEAD Foundation 44828270273/job 136606336221 and factory 44828270332/job 136606337206 COMPLETED SUCCESS; authentic logs inspected. Current code HEAD push Actions log unavailable, NOT PASS. Upstream ModManager 2.1.2.1 and Toolbox 2.1.2.1, REA generic reference do not prove Switch ABI. Original main expected SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not rehashed; Sakura aura107, Event236 marked/unmarked and all three false flags untouched. NEXT obtain HEAD factory push run/job/log; fix if failing; native consumer ownership/lifecycle remains unresolved.
2026-11-21 PENDING_CI: offline factory multi-mod SHA256-verified canonical profile composition (last-owner-wins or collision reject), code 52d7034b7257da2ff0902783f2bb2f5dc44f68a8; import fix 5eaf77ca2b9fc81b3f32367794ee60e9bea6ff2e. First factory workflow 44828176316/job 136606011691 FAILED (test import path); original log inspected, repaired. New HEAD Actions pending. This is class-selector editor-only; no native consumer, 53 unsupported factory ABI, archive precedence or Uzuy proof. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 variants and three false flags preserved. NEXT: read new HEAD workflow job logs, fix failure, then authenticate native consumer lifecycle.
2026-11-21 VERIFIED_CI_OFFLINE_EDITOR: code 8eaba7c4cb0a17b50eae911ebc969b2b3726a5c2 (parent 50fea16f028030792bf97e4b157128dcc1dcd223) adds standalone read-only SHA-source-replayed owner-partition directory reassembly CLI with exclusive output publication, byte-for-byte restoration, unexpected-file/index/part/source tamper rejection. MovesetPlus push run 44802490050 job 136517931666 COMPLETED SUCCESS; authentic job log inspected: new test_replay_and_fail_closed OK; 16+1+8+5+4+4+13+3 tests OK. Host GitHub Actions only, not ARM64 or Uzuy. Primary references ModManager 2.1.2.1 release 2026-08-30, Toolbox HEAD 6f780cb6814f07e03c16b3e78d97dde4e4368983, REA HEAD 86b4360ce23aa640f1cdd475cffb0860fba8c723; no Switch consumer ABI proof. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 remains pinned, not rehashed; Sakura aura107 and marked/unmarked Event236 unchanged. full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT authenticate native consumer ABI/lifecycle using pinned original main bytes; no hook.

2026-11-21 PENDING_CI: parent 531305c83b1effdb28313078c15a46c521af450d; code 78c7b01c6bdc2cbbfa3d4e65b5e6ddfd59c40209 adds reassemble_owner_partitions, a reversible editor-only inverse of explicit-owner MovesetPlus partitions preserving global event order. It validates source partition ordering, per-part SHA256, event-owner ledger, missing/extra events, final merged byte SHA and event count; regression covers positive, tampered SHA, reversed partitions/ledger, missing part, and empty losing-owner partition. Upstream ModManager 2.1.2.1 README SHA 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709 (Steam-only), Toolbox README SHA 657f161390c4abe8afe10cea11a2b9a28e6bf6b0; REA generic reference from prior evidence, not refreshed this run. Previous HEAD 531305c CI completed success and authentic job logs read: MovesetPlus 44782462393/136448455336, Foundation 44782462286/136448455226, compressed PRM 44782462660/136448456498. New code HEAD CI not verified; no original main byte rehash, Switch consumer ABI, ownership, CPK precedence or Uzuy proof. Original main expected SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; Sakura aura107, marked/unmarked Event236 unchanged; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT: obtain push Actions run/job/log for final HEAD, fix regression if needed; then source-pinned consumer analysis.

2026-11-21 PENDING_CI: code f5ad7cfd8bc1526f9021e43e08ffd7d4a99610d6 (parent 1dce633b87d215bfe8631092934bb0fea4c48892) adds read-only --verify-partition-directory exact source replay of standalone selected-owner editor files/index; positive, altered index, altered part, unexpected file, altered source and CLI regression. GitHub Actions push run/job/raw log for this code not yet available. ModManager tag 2.1.2.1 README 8e9560b2; Toolbox 6f780cb README 657f1613; REA README 93e1e272 are PC/generic only. No native Switch consumer ABI/ownership/Uzuy proof. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 pinned; Sakura aura107, Event236 marked/unmarked and all three false release flags untouched. NEXT inspect exact HEAD push Actions job raw logs, repair failures, then authenticate original main consumer ownership.

2026-11-20 PENDING_CI: code b72be2698cc5c46027446860c5fb69a3b06498d9 (parent 316e8342b30232671d21c59f95e083fc47e073b5) adds --verify-resolved --partition-directory to publish SHA-replayed selected-owner PC editor manifests as individual numbered JSON files plus SHA256 index using staged directory rename; no engine ABI. Direct regression tests positive owner selection, unsafe source names (not used as paths), SHA integrity, existing destination, mutated proof/source rollback. Local tests not run (GitHub DNS unavailable); HEAD push workflow run/job/authentic log not obtained, NOT PASS. Primary sources: ModManager tag 2.1.2.1 README blob 8e9560b2; NSC-Toolbox 6f780cb README blob 657f1613; REA main README blob 93e1e272; none proves Switch ABI. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not independently rehashed; no consumer ownership/lifecycle/CPK precedence/Uzuy proof. Sakura aura107, Event236 marker 0x4E53 +0x2A and unmarked variant untouched; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT obtain HEAD MovesetPlus push run and raw job logs, fix any failure; then authentic native consumer proof.

2026-11-20 PENDING_CI: Added authenticated read-only replay verification of existing PC editor owner-partition bundles (--verify-partition-bundle); exact bundle bytes, provenance, selected owner and source SHA are checked. Parent 55306b12028a5f182c0a5dc83a7616f3e3b8ca12, code de8cbb7522cae0b9cccd31a0380c5f9fca7a2811. Previous parent four push workflows COMPLETED SUCCESS and original job logs inspected (Foundation 44744226927/136315242897, MovesetPlus 44744226985/136315242449, CPK 44744226917/136315242743, compressed 44744226878/136315242596). New code HEAD CI NOT YET VERIFIED. Original main pinned SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; no original bytes/ABI proof, no runtime hooks; Sakura aura107, Event236 marked/unmarked untouched, full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. Evidence handoff/evidence_partition_replay_20261120.md. NEXT inspect new HEAD MovesetPlus job raw log, repair any failures, then native ownership evidence.
2026-11-20 PENDING_CI: --verify-resolved --partition-output publishes a single SHA-bound editor-only JSON bundle of per-owner selected events after source replay, with no binary/engine ABI claim. CLI regression covers positive owner rows, per-partition byte SHA, existing output, tampered merged bytes, tampered source. Parent 37b14e6692efe92a1460d761b87162880c55d465. Research upstream ModManager 2.1.2.1 README blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709 (Steam-only); Toolbox README 657f161390c4abe8afe10cea11a2b9a28e6bf6b0; REA README 6cbd8d77f786b2f71b952a1282fda93a2fbdc13d. Original main SHA256 pinned 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; native ABI and Uzuy unverified, three release flags remain false. Next: run tests and inspect HEAD Actions push job original logs; do not claim PASS.

2026-11-20 PENDING_CI: resolved PC editor multi-mod output now emits per-event selected-source provenance for every event, including unique and explicitly resolved collisions. Read-only replay verifier compares complete provenance and exact bytes; regression asserts ordered owners and rejects tampered owner ledger. Parent 876c7c9f5cfe50ff993e0f074953c98d94d3b8c5. No engine archive precedence or native ABI claim; original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, both Event236 variants, and three false flags untouched. Host/HEAD CI job log pending.
2026-11-20 PENDING_CI: explicit-owner MovesetPlus editor output now supports read-only --verify-resolved replay from SHA-pinned PC manifests, comparing exact payload and full provenance; source 4eaff6c515090061c66a010695a771927370c9d1, regression d5c62c1aba9f46154653cfdb0cf5e3f194c002c3, parent f1f5ab0f324cee774a196293c5240878d5f42fa5. No host/HEAD Actions raw log verified. Original main pinned SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; Sakura aura107, Event236 marked/unmarked and three false release flags unchanged. No Switch ABI/ownership/Uzuy proof. NEXT execute new regression, inspect authentic HEAD Actions job logs, fix failures.
2026-11-20 PENDING_CI explicit PC editor collision owner resolution: parent 21ae9996be9e92af2bf3a986150b243b683cdf7e; source 5b79d6ffa15be4bbe0968acd730b1d27ecbec62d, tests 66de632b7ad2bbb6992b15d518dd3a1c3f827f2c, newline fix 96276d87edc423eb4f8a17ed6b40b9d4dbee1549. New --resolve JSON event_id->source owner selects authenticated PC editor event rows only when every collision has exactly one explicit owner, preserves first-occurrence event order, rejects missing/extra/unknown owners and tampered source; SHA-pinned provenance output and CLI positive/negative/rollback tests. Host tests NOT executed; HEAD Actions push runs/job raw logs NOT obtained; PENDING_CI NOT PASS. Research ModManager tag 2.1.2.1 README blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709 (Steam-only), Toolbox README 657f161390c4abe8afe10cea11a2b9a28e6bf6b0, REA README 6cbd8d77f786b2f71b952a1282fda93a2fbdc13d; none proves Switch consumer ABI. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107 and both Event236 variants unchanged; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT verify HEAD Actions original job logs, repair failures; authenticate original main native consumer ownership before any hook.
2026-11-20 PENDING_CI: code 813669ded6e4c7afdc28e7eb1cbc4181210adccf parent ff37c40425fe9a240c163830a309b79235d3cadd exposes SHA-authenticated PC editor event-ID collision report through --collisions-only CLI; JSON report and independent evidence SHA256, no merge or engine precedence; subprocess positive, tampered-source and preexisting-output fail-closed regressions. GitHub Git tree/commit/ref update succeeded; host tests and HEAD Actions push-run/job/raw logs NOT verified (GitHub DNS unavailable from container, connector commit runs PR-only). NOT PASS. Original main pinned SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; Sakura aura107, marked/unmarked Event236 unchanged; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT obtain authentic HEAD Actions logs, fix any failures; prove consumer ownership/lifecycle before runtime hooks.
2026-11-20 PENDING_CI: code f6dc2c829463061b74ae8faa3fbadf6d937b05a0 parent 18d55757a9ecf0dd99e4dc783ca4239a03cdcc9c implements SHA-pinned PC MovesetPlus multi-mod editor index reorder with source replay before/after, bijective order validation, CLI two-file publication, positive/negative/tamper tests and workflow integration. Evidence handoff/evidence_pc_moveset_reorder_20261120.md. HEAD Actions run/job/raw log pending, NOT PASS. No Switch ABI, CPK precedence or Uzuy proof; original main SHA256 pinned, Sakura aura107 and marked/unmarked Event236 unchanged; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT inspect HEAD push Actions jobs and raw logs, fix failures; then prove native consumer ownership.
2026-11-20 VERIFIED_CI_OFFLINE_SYNTHETIC: mixed compressed CRILAYLA + plain Event236 PRM exact-size atomic CPK publication; source commit 3edc5d915a748912335decdb544b661961cecab6. Initial commit ebf83027c3bf57d6effbb13294d45eaf56e1d9cd failed compressed run 44627970677/job 135926726165 because publisher rejected plain members; fixed validator AND independent verifier with semantic byte equality and tamper regression. HEAD code workflows completed SUCCESS and original job logs inspected: compressed 44628063852/job 135927055000 (6+13+32+16 tests), same-size 44628063929/job 135927055273 (39 tests), MovesetPlus 44628063939/job 135927055922, Foundation 44628063805/job 135927054696. This proves only offline synthetic pipeline, not authentic game CPK, native consumer ABI, ownership, lifecycle, archive precedence or Uzuy. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 pinned; Sakura aura107, Event236 marker 0x4E53 +0x2A and unmarked native untouched; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. Documentation HEAD CI needs separate verification.

2026-11-20 PENDING_CI REPAIR: compressed workflow run 44627970677 job 135926726165 FAILED: independent publisher cpk_same_size.py rejected plain selected PRM ('Both streams must be CRILAYLA'). Extended publisher validator AND independent output verifier to validate source-authenticated uncompressed Event236 semantic mark byte-for-byte, while retaining CRILAYLA path. Added negative plain tamper test. Parent ebf83027c3bf57d6effbb13294d45eaf56e1d9cd; verify new HEAD run/job/raw logs before PASS. Offline synthetic only, no native ABI/Uzuy.

2026-11-20 PENDING_CI: mixed CRILAYLA + uncompressed Event236 PRM batch conversion added to same-size offline CPK publisher, with positive byte integrity and negative no-op/non-PRM rollback regressions. Source SHA and TOC validated once at intake; independent publisher still revalidates. Synthetic only; no native consumer ABI, archive precedence or Uzuy proof. Original main pinned SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; Sakura aura107 and both Event236 forms untouched. All three release flags false. Verify HEAD compressed/Foundation/MovesetPlus push Actions raw logs before PASS.

2026-11-20 OFFLINE COMPRESSED BATCH: parent d18b446c4a5ee689af6206bdbd52e43c2dc58b11; code d360cd62f7758e4ceff7fe1abaef824c13473ceb. Multi-member CRILAYLA/Event236 conversion now SHA-verifies the source and parses CPK TOC once before decoding all selected members, using an internal validated-index path. Prior per-member SHA+TOC repetition removed; no public reencode_candidate behavior changed. Negative wrong-SHA-before-TOC and positive two-member one-TOC regression added. Compressed push run 44618894253 job 135894875213 COMPLETED SUCCESS, authentic job log inspected: 6+13+32+12 synthetic tests OK. Other HEAD workflows 44618894255 (foundation) and 44618894295 (MovesetPlus) were in progress when recorded; verify final jobs/logs. This is offline performance and provenance, not engine consumer ABI, authentic CPK, ownership, archive precedence or Uzuy. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 pinned, Sakura aura107 and both Event236 forms unchanged, all release flags false. Research note handoff/evidence_compressed_batch_20261120.md.

2026-11-19 PENDING_CI: multi-member offline compressed Event236 same-size CPK publication implemented at code 129eaf7adea0367d9aecbf18ca3ad65b4af390b9 and tests 6aa8ad785317f0f64d5bcde27cfb407b42df8a9e (parent c1ab84f3f8b9b7b7275c2424533d971d92edff1d). convert_many validates each SHA-bound CRILAYLA candidate, rejects duplicates/no-op/size mismatch, and atomically publishes all via existing independently verified publisher; single-member API remains compatible. New synthetic multi-member positive, negative second-member rollback, duplicate/empty, byte-integrity regressions. NOT PASS: HEAD Actions push run/job/raw log unavailable through connector (commit workflow lookup PR-only; combined statuses empty); tests not executed locally. Upstream README blobs NSC-ModManager 2.1.2.1 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709, NSC-Toolbox 657f161390c4abe8afe10cea11a2b9a28e6bf6b0, REA ff39a01428340fb243f5268fb70f5d6ee40ffeb0; PC/generic sources, no Switch ABI. Original main pinned SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; Sakura aura107/Event236 marked and native untouched; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT inspect HEAD push workflow original logs and repair failure; then authenticate native consumer ABI/ownership/lifecycle/archive precedence before any hook.

2026-11-19 PENDING_CI code 1a8c1b590142c45699af496a7e7e74a0cf62ac43 parent bbad993399ea563843092d1afb364f762bed5428: compressed PRM zero-change path preserves original CRILAYLA stored bytes bit-for-bit; offline CLI now calls shared validated reencode_candidate and verifies stored SHA, instead of duplicating encoder path. Added zero-change export identity/size and changed-payload evidence regressions. Prior HEAD bbad993 GitHub push runs 44479125643/44479125629/44479125726 COMPLETED SUCCESS, authentic jobs 135406786399/135406786200/135406786684 logs read. New HEAD run/log NOT YET VERIFIED, no PASS claim. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 pinned, Sakura aura107 and Event236 marked/unmarked untouched; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. Research upstream ModManager 2.1.2.1 2026-08-30, NSC-Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983, REA 93c8e0c0c8e80e3c2379a1c7d2c2a956331cc8e8 (not game ABI). NEXT retrieve new HEAD push runs via REST actions/runs branch, raw job logs, fix any failure; then pursue consumer ownership/CPK precedence.

2026-11-19 VERIFIED_CI_STATIC_ONLY: code 9d87417613ba2fb26b18396a1a3d03b4187163bd corrects AArch64 Wn zero-extension invalidating Xn alias in FileLoad CFG; 3 synthetic pre/post-writer clobber and unrelated-register cases. HEAD code run Foundation 44457996680 job 135337632477 COMPLETED SUCCESS, original log PINNED_FILELOAD_SP_CFG_PASS 166 10 NO_CONSUMER_ABI; MovesetPlus 44457996686 job 135337632473 SUCCESS, compressed 44457996703 job 135337632479 SUCCESS, original logs read. This is host/static evidence only; consumer ABI/ownership/lifecycle and Uzuy unresolved. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 pinned; Sakura aura107 and Event236 marked/unmarked preserved; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT: prove native consumer ownership from original main or work on authentic nine-family integration; do not add runtime hooks.

2026-11-19 W-register alias invalidation: AArch64 Wn writes zero-extend into Xn; FileLoad CFG now invalidates Xn provenance when Wn is written. Three synthetic cases cover prewriter/afterwriter clobber and unrelated W-register preservation. Parent b17064d32a689ae33e74d60ed203486cf3c5b7b3; code and tests pending HEAD CI. Previous HEAD b17064d32a689ae33e74d60ed203486cf3c5b7b3 Foundation 44451292830/job 135315619331, MovesetPlus 44451292685/job 135315618416, compressed 44451292747/job 135315618507 COMPLETED SUCCESS, authentic logs inspected; this does NOT verify the new change. Upstream NSC-ModManager latest release 2.1.2.1 (Switch Projectiles Target), repo commit 276116ebf5ba398a867793cb02ee6c33c0927645; NSC-Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983; REA fe784e7f03612a7d6e4d834031df3b5ff59ce00f. PC editor and RE sources do not prove Switch ABI. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 marked/unmarked unchanged. No runtime hook; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT: inspect new HEAD Foundation push job raw log, repair if failed, then native consumer ownership proof.

2026-11-19 PENDING_CI: code a2def4e665a150cb357c4442530082a753a04674 parent 9dd768210efc86cfe9eed1af2e8f6abaaef4d1e9 adds entry-to-writer CFG alias propagation with path-local MOV/ADD/SUB transfer, register clobber and opaque-call barriers, bounded state search, plus synthetic disjoint/overlap/clobber regressions. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 remains pinned; no runtime hook or consumer ABI proof. Local Capstone absent; HEAD GitHub Actions run/job/raw logs not verified, NOT PASS. Upstream README blob anchors: NSC-ModManager 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709, NSC-Toolbox 657f161390c4abe8afe10cea11a2b9a28e6bf6b0, REA 5ea33378b67bb648f2e1288ef9760075208d30f5. Sakura aura107/Event236 marked/unmarked unchanged. full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT fetch authentic Foundation push-run and job log for HEAD, fix failures, then prove consumer ownership and lifecycle from original main.

2026-11-19 PENDING_CI: ARM64 FileLoad byte-width semantics now distinguish byte/halfword/signed-word loads from destination register width, and fail closed on unsupported transfer mnemonics; synthetic narrow-load negative regressions added. Code eab7be2e9ca1c98a5c838c09bce01948508a107d parent 1c31307b3ce53ffe8fc3161496c3d10631a27474. Local Capstone install blocked by DNS, no HEAD authentic Actions run/job/log yet. This is static alias evidence, not consumer ABI, ownership, or Uzuy. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 both variants unchanged; three release flags false. NEXT obtain Foundation push-run raw log, repair any failure, then pursue register provenance and actual native consumer lifecycle.

2026-11-18 PENDING_CI: FileLoad CFG now emits possible stack write/read address-equality candidates only when each instruction has a unique entry-SP-relative offset; ambiguous paths are excluded. Candidate does NOT establish same executed path, register value, pointer ownership, ABI, lifecycle, or engine consumer. Positive same-offset, negative different-offset and ambiguous-path synthetic regressions added. Parent 0396cef291485e617db4f108d13edda60287cdbb; local Capstone unavailable, HEAD Actions job logs pending. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; Sakura aura107 and Event236 variants unchanged. Upstream ModManager tag 2.1.2.1 README blob 8e9560b2, Toolbox blob 657f1613, REA blob 4ccd45ed; none establishes Switch ABI. Release flags false. NEXT inspect authentic HEAD Foundation job logs and then prove path-sensitive register provenance before runtime integration.

2026-11-18 VERIFIED_CI_STATIC_ONLY: New conservative FileLoad SP CFG slice at b9bed4840db45d1a0d0eb725fa0a41ce768a5179 (parent 93f12b34ea4ab167e03a9e9d97395d9d3ae3fa15). Uses original-main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 and original ARM64 word hashes. Tracks entry-SP-relative displacements along bounded CFG, preserves differing paths as ambiguous, and marks unknown after BL/BLR; no call-preservation ABI assumption. Synthetic linear, fork/join, call, truncated and state-budget tests. Foundation run 44294505825 job 134767889692 COMPLETED SUCCESS, authentic log PINNED_FILELOAD_SP_CFG_PASS 166 10 NO_CONSUMER_ABI; compressed 44294505944 job 134767889225 and MovesetPlus 44294505872 job 134767888993 COMPLETED SUCCESS, authentic logs read. This verifies only bounded static CFG, not ownership/ABI. Primary references NSC-ModManager tag 2.1.2.1 (2026-08-30), NSC-Toolbox HEAD 6f780cb6814f07e03c16b3e78d97dde4e4368983, REA HEAD b21db3f3293bcfaffa6793be2f09b1aaf35dcc69; PC source does not establish Switch engine ABI. No hook, original main mutation, Sakura aura107/Event236 change or Uzuy test; release flags false.
2026-11-18 PENDING_CI: new SHA-pinned FileLoad SP/FP memory operand census (original instruction words, exact offsets, writeback, negative mutated main, synthetic STR/LDR test); no stack-slot dataflow, pointer ownership, consumer ABI or runtime claims. Parent b56ae5e70769b400597ec1e9ffd8fdc9bc62519f. Upstream ModManager 2.1.2.1, Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983, REA 4995018d3a492aa6627929e1d45ea35c95170970 are not Switch ABI evidence. All release flags false. NEXT verify HEAD Actions authentic log; investigate original FileLoad SP delta and control-flow before claiming stack aliases.

2026-11-17 VERIFIED OFFLINE CPK: code ab7caf471b7303ccb73ef88da77fe05d73373c9b (parent 3062e83cda93426339d856f2bcb427ac8b5fab73) maps every packed candidate read-only via ExitStack rather than Path.read_bytes; validate_many_same_size accepts mmap payloads and validates CRILAYLA against source-bound Event236; output streaming, independent disk verification and exclusive publication remain. Two-member synthetic regression and no-read_bytes assertion. GitHub Actions CPK push run 43986842680 job 133717069114 COMPLETED SUCCESS; authentic job log inspected: 39 tests OK. MovesetPlus run 43986842799 job 133717069869 and compressed PRM run 43986842723 job 133717069130 SUCCESS with original logs inspected. Foundation run 43986843402 still pending at checkpoint. Earlier code d238ae7c CPK run 43978999838 job 133690273906 COMPLETED SUCCESS 38 tests with original log inspected. Upstream ModManager release 2.1.2.1 published 2026-08-30, Toolbox HEAD 6f780cb6814f07e03c16b3e78d97dde4e4368983, REA HEAD d5a942177fad030d3caf0f8d39856c116e3e5cda; these are PC/generic references and DO NOT prove Switch engine ABI. Original pinned main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 and authentic CPK unavailable in this run; no native consumer/ownership/lifecycle/archive precedence or Uzuy proof. Sakura aura107 and Event236 marked/unmarked untouched. full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT authenticate original main and CPK bytes, establish consumer ABI/lifecycle before hooks.

2026-11-17 PENDING_CI: code d238ae7ca128f0cdcada84c9fae1407b76f46429 (parent 5004892d263b9721c1900fb608b59c39a5fb6382) extracts source-SHA/TOC/semantic validation into validate_many_same_size and streams CPK output in 1MiB chunks to fsynced staging, followed by independent on-disk verifier and exclusive hard-link publication. No full archive bytearray/bytes output allocation in publisher; in-memory replace_many_same_size remains for API compatibility. Synthetic publication regression added; local tests NOT executed (container GitHub DNS unavailable), HEAD push Actions run/job/log NOT verified. Prior synthetic CI successes do not cover this HEAD. Original game main/CPK consumer ABI, ownership, lifecycle, async, rollback, precedence and Uzuy remain unresolved. Preserve main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 marked/unmarked and all three release flags false. NEXT inspect HEAD Actions raw job log, repair failures, authenticate game bytes before native hooks.

2026-11-17 PENDING_CI: code 31c692a45ee31c268110b0f904e4a42a16aded90 (parent 32df22134713b3e73fa8f9de9d2dd9685e6ea05e) independently verifies staged on-disk same-size CPK bytes using source/output SHA-pinned read-only mmap and semantic verifier before exclusive hard-link publication. Negative regression forces verifier failure and asserts no published output or staging residue. GitHub Actions push run/job/raw log for this code NOT VERIFIED; local tests not executed; no PASS. Earlier run 43928815687 job 133515411235 SUCCESS only for earlier code. Original Switch CPK and pinned main bytes unavailable for consumer ABI/ownership/lifecycle/async/rollback/archive precedence; no Uzuy. Preserve main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 marked/unmarked; three release flags false. NEXT retrieve new push run and raw job logs, repair any failure, authenticate original game assets before native hooks.
2026-11-17 VERIFIED OFFLINE CPK: code 9b3e82940976c0befef16cca44a03409c072c5cf (parent 6bd9e03710bd213cc17fcc6f50118ad48f397ee2) uses read-only mmap source in same-size multi-member CPK publisher instead of source_path.read_bytes(), reducing peak Android archive copies; one regression proves source Path.read_bytes is never called. GitHub Actions push run 43928815687, job 133515411235 COMPLETED SUCCESS; raw job log inspected: 36 real-parser synthetic tests OK including new mmap publisher test. Prior code 15701b3c run 43877214874 job 133333273151 also SUCCESS 35 tests, authentic log inspected; prior PENDING_CI notes are historical. Original Switch CPK not tested; original pinned main bytes not available in this session for ABI; no native engine consumer/lifecycle/precedence or Uzuy proof. Upstream ModManager tag 2.1.2.1 commit 502c38d3ee832509f9ee3951b7d3339826538fec, Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983, REA 26d88826cc36c5513ce8977346c0e4f15bb25169; no cross-OS ABI inference. Preserve main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 both variants and three false release flags. NEXT verify final HEAD foundation workflow log, authenticate original game CPK/main and prove consumer lifecycle before any hook.
2026-11-16 PENDING_CI: Fixed an actual Python SyntaxError in tools/portlib/cpk_same_size_verify.py: the call to _extract_validated_candidate contained literal backslash-n characters instead of a newline, preventing module import and therefore all independent verifier tests. Code commit 15701b3cfb5326645d59c08da81b4ebefd11e530 (parent 3db3a0209d34b9861fbca4fcb2442c5f1d805bb1), one source file only; existing workflow unittest imports module and is the regression gate. Verified GitHub compare only changed this file; no local tests or authentic Actions push run/job/log confirmed (REST DNS failure). Upstream README anchors NSC-ModManager 2.1.2.1 blob 8e9560b2, NSC-Toolbox blob 657f1613, REA blob 5ea33378; none prove Switch ABI. No authentic original main/CPK bytes, consumer ABI/lifecycle, archive precedence or Uzuy proof. Keep SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 marked/unmarked, and all three release flags false. NEXT obtain Actions push-run and raw job log, fix remaining test failures, validate authentic CPK before runtime hooks.
2026-11-16 PENDING_CI: Independent same-size CPK verifier now passes its SHA-authenticated source TOC/index to each selected Event236 candidate extraction rather than rehashing and reparsing the entire original archive per selected member. Code commit 1d01038349fe735832dfeb3b5bba3ca127d73016; regression commit 5b0a7c75a454ee7e73f39f9c624f8938f5f88069 (two selected compressed members, parser count and index provenance). Parent 9a07521e0683431b40ffe4aa41e878f8bdaf3e50. GitHub Actions push-run/job/raw log and local tests NOT VERIFIED; do not mark PASS. Upstream anchors: NSC-ModManager 2.1.2.1 README Git blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709 (Steam only); NSC-Toolbox README blob 657f161390c4abe8afe10cea11a2b9a28e6bf6b0 (PC editor); REA README blob 5ea33378b67bb648f2e1288ef9760075208d30f5 (generic RE, not Switch ABI). No original Switch CPK or pinned main bytes verified in this execution; native consumer ABI/ownership/lifecycle/async/rollback/archive precedence and Uzuy unresolved. Preserve main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 marked/unmarked; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT: authenticate push-run via Actions REST, read raw job logs and fix failures, test authentic CPK; do not hook runtime.
2026-11-16 PENDING_CI: Code 3067e6af1faa6aba2f4acf4faf24d52278ee26bc (parent d594906903bfe2da270753468c880123b028356a) adds read-only mmap verification for source/output CPK, avoiding full-file read_bytes copies on Android; direct verifier accepts mmap and bytes, positive and wrong-hash mmap regressions added. GitHub compare: 1 ahead, 0 behind; PR-filtered workflow lookup empty and combined statuses empty, NOT evidence of push-run absence. Push Actions run/job/authentic log NOT verified; local tests NOT executed. Primary source anchors: NSC-ModManager tag 2.1.2.1 README blob 8e9560b2 (Steam-only), NSC-Toolbox README 657f1613 (PC editor), REA README 5ea33378 (generic reverse engineering). No original Switch CPK or pinned original main bytes available here for ABI proof; no native consumer/ownership/lifecycle/archive precedence/Uzuy proof. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 unchanged; Sakura aura107, Event236 marked/unmarked preserved. full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT: obtain push-run via Actions REST and inspect authentic job logs, repair failures, test genuine CPK; do not hook runtime.

2026-11-16 PENDING_CI: Added read-only offline CLI tools/verify_same_size_cpk.py wrapping independent SHA-pinned CPK output verifier, with four real-parser synthetic subprocess regressions (valid, wrong SHA, unselected tamper with recomputed SHA, unknown member) and push workflow trigger. Parent 77b2ee97e0a37c071b5cc6443abcef216d0b2691, code f9261cc3d9a080388467405166eba71e9ba2686a. GitHub Actions push-run/job/log unavailable; no PASS. Research anchors NSC-ModManager tag 2.1.2.1 README blob 8e9560b2, NSC-Toolbox 6f780cb README blob 657f1613, REA README blob 5ea33378; no cross-OS ABI proof. Pinned main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107 and Event236 marked/unmarked unchanged; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. Next authenticate HEAD Actions job logs, repair any failures, then test genuine Switch CPK; do not hook native consumers.

2026-11-16 PENDING_CI: Added independent read-only verification of SHA-pinned source/output CPK, TOC equality, every nonselected byte, selected Event236 decoded semantics, and synthetic positive/negative regressions. No authentic Switch archive or native consumer ABI/ownership/lifecycle/archive precedence; no Uzuy. Upstream anchors NSC-ModManager 2.1.2.1 README 8e9560b2, NSC-Toolbox 6f780cb README 657f1613, REA README 5ea33378 (not Switch ABI). Parent b80b93c69fd40a651baf04a9fd60c33ce45ecea0; final HEAD CI run/job/log not yet authenticated. Preserve pinned main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 marked/unmarked; all three release flags false.

2026-11-16 PENDING_CI: Fixed offline same-size CPK multi-member collision handling: casefold duplicate member names now rejected before candidate processing; publisher JSON duplicate object keys (exact/casefold) fail closed rather than silently overwriting a candidate. Added real-parser integration negative regression and CLI publication regressions for both cases. Parent bf4d91e9b7921780754f4e15b8554ebaa560bedd; CI run/job/log not verified; no authentic Switch CPK, original-main consumer ABI, ownership, lifecycle, archive precedence or Uzuy. Primary evidence: NSC-ModManager 2.1.2.1 README blob 8e9560b2 (Steam-only), NSC-Toolbox 6f780cb README blob 657f1613 (editor), REA README blob 5ea33378 (general RE). Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 unchanged; Sakura aura107 and Event236 marked/unmarked unchanged; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. Next obtain push-run and authentic job log; repair test failures; then authenticate real v1.70 archive and native consumer before any runtime hook.

2026-11-16 PENDING_CI: atomic multi-member same-size CRILAYLA replacement implemented in ddf52047a1a09a777164b1cafa45ee7a1324205a (parent 4dec5b1e71cf0c293f39168660c175425595736e). One SHA-authenticated original CPK and original TOC; all selected decoded Event236 candidates validated against original before any archive bytes are published; byte-exact untouched spans and unchanged TOC verified. Two synthetic real-parser regressions added for two-member conversion, unaffected third entry, wrong SHA, empty mapping, wrong semantic candidate and size mismatch. NOT executed locally (GitHub DNS unavailable), push Actions run/job/log NOT verified; no authentic CPK, native ABI/ownership/lifecycle/archive precedence or Uzuy proof. Research refs: NSC-ModManager 2.1.2.1 README blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709 (Steam only), NSC-Toolbox README blob 657f161390c4abe8afe10cea11a2b9a28e6bf6b0, REA generic reverse engineering reference (not game ABI). Next inspect HEAD push Actions run and full job log, fix any regressions; then authenticate real v1.70 CPK before installation. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 untouched; Sakura aura107 and both Event236 variants preserved; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false.
2026-11-16 PENDING_CI: Real parser integration regression for source-SHA-pinned same-size CRILAYLA CPK replacement added in 8ded8f18, corrected exact-length corrupt stream fixture f63dfa59. Five synthetic CPK/UTF/PRM integration tests cover decoded Event236, byte-exact nonselected payload/metadata, wrong SHA/path, same-size semantic mismatch, corrupt stream, CRC rejection. No authentic v1.70 CPK, runtime ABI, or Uzuy evidence. CI push-run and original job logs NOT VERIFIED (GitHub connector exposes PR-only workflow lookup; direct Actions API unavailable). Next: obtain push run ID via Actions REST, inspect job logs, fix tests, then authenticate game fixture. Preserve original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 marked/unmarked and all three false release flags.\n2026-11-15 PENDING_CI: Added offline source-authenticated batch remove/replace for PC MovesetPlus editor indices (one replayed composition, conflict rejection, five synthetic regressions); no native consumer, CPK installation or Uzuy proof. Research: NSC-ModManager 2.1.2.1 README blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709 (Steam-only), NSC-Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983 README blob 657f161390c4abe8afe10cea11a2b9a28e6bf6b0, REA README blob 056af5e87775520a72fd8609f88edd074a5e7498 (not game ABI). Pinned original main 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 unchanged; Sakura aura107, Event236 marked/unmarked preserved; all release flags false. Next verify HEAD Actions logs, then authenticate consumer lifecycle and archive precedence.
2026-11-15 PENDING_CI: Added SHA-pinned PC MovesetPlus editor source replacement (original source replay, full recomposition, collision rejection, 4 synthetic regressions); no binary consumer or Uzuy evidence.
2026-11-15: Added original-source replay verifier for offline PC MovesetPlus merged editor indices. Re-converts every original SHA-pinned source in order and requires byte-exact merged payload and full evidence equality; negative tests cover source tampering, order, missing sources, forged evidence and boundaries. Upstream references: NSC-ModManager 2.1.2.1 README blob 8e9560b2; NSC-Toolbox 6f780cb README blob 657f1613; REA main README blob 78b7064b (not Switch ABI). Pinned main 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not modified. No runtime hooks, authentic consumer lifecycle, archive precedence or Uzuy proof. CI PENDING for new HEAD; release flags remain false.
2026-11-15: Offline PC MovesetPlus editor index multi-mod restore CLI added. SHA-pinned merged payload/proof split() is verified before any output, numbered names prevent path injection, exclusive publication rolls back on I/O error; four positive/negative/boundary regression cases. This is NOT a binary moveset, game consumer, CPK installer or Uzuy proof. Parent d4d0ee87d19c3b741efd06aec4a297e30c107af8; new HEAD CI pending. Primary research: NSC-ModManager tag 2.1.2.1 released 2026-08-30 (Switch Projectiles Target); NSC-Toolbox commit 6f780cb6814f07e03c16b3e78d97dde4e4368983; REA commit 351c2f4a038f618a5c16a5e2a52aa1b656388c3c (no Switch ABI inference). Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 untouched; Sakura aura107, Event236 marker 0x4E53 +0x2A and unmarked preserved; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. Next authenticate original main consumer ownership/lifecycle/precedence before any runtime hook.

2026-11-15: Added reversible, SHA-verified per-mod source ranges to offline PC MovesetPlus multi-mod editor manifest composition. split() reconstructs each converted NSC editor manifest, rejects merged payload tampering, forged source ranges/digests, and unattributed events; new synthetic regressions. No binary moveset, Switch consumer ABI, original-main runtime evidence, or Uzuy. Parent dd8c909652740623f11f8a9230052b67f2e094ab. CI PENDING for new HEAD; preserve original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 marked/unmarked, and three false release flags. Sources: NSC-ModManager release 2.1.2.1 (2026-08-30); NSC-Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983; REA reference only. Previous HEAD dd8c909 CI foundation 43647601668, compressed 43647601645, multi-mod 43647601769 completed success; logs require inspection.
2026-11-15: Added PC MovesetPlus NS4/NSC -> NSC index-only manifest exporter, SHA256-pinned input and output, source-pinned 289 shared / 300 NSC indices, exclusive output publication and negative regressions. This is a PC editor index artifact, NOT binary conversion, Switch engine ABI, CPK patch, or Uzuy proof. Primary: NSC-ModManager release 2.1.2.1 (2026-08-30, Switch Projectiles Target) https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1 ; NSC-Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983; REA f3b697da5a698a5548afd3b19d044ec623bdda0b (reference only, not ABI). Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not modified. CI PENDING until HEAD run completes and original job logs inspected. Next: authenticate game bytes and consumer lifecycle; do not hook. All release flags false.
2026-11-15: Independent verifier replay commit 53e049dacedb7f867fbe0f40b92a6c749259e34b (parent 88a220eccca7a7996dfb01dd1fabb25e0dc6a2c6). Source-bound CRILAYLA verifier now reconstructs Event236 marker semantics from SHA-pinned original CPK decoded records, independently of exporter candidate builder; checks native/unmarked/already-marked provenance and exact candidate bytes. Added exporter-isolation and forged-provenance negative tests. CI for this code PENDING until push workflow COMPLETED SUCCESS and authentic job log inspected; no game-authentic compressed PRM, installable CPK, native consumer ABI/ownership/lifecycle/archive precedence or Uzuy. Pinned main 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 untouched, Sakura aura107 and Event236 variants preserved, all three release flags false. Upstream: NSC-ModManager tag 2.1.2.1 commit 502c38d3ee832509f9ee3951b7d3339826538fec; NSC-Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983; REA 764203cf4a3a3f4ec3c34ebe7049bbd9a04adca9 (not a game-specific ABI reference). Next verify CI push-run logs and then obtain authentic PRM/consumer proof.

2026-11-14: Offline compressed PRM batch adds optional --encoder auto, selecting smaller exact-verified literal or distance-3 run candidate per member (ties literal). Commits 5a68aa0 and 9b084eac; synthetic tests cover candidate selection, decoded digest, nonrepeating fallback, source byte integrity. CI for HEAD 9b084eac PENDING: GitHub connector commit workflow runs endpoint filters PR-only, direct push-run API inaccessible in this session; do not mark PASS without authentic job log. No original game PRM fixture, native ABI, CPK repack or Uzuy. Source anchors NSC-ModManager 276116eb README blob 8e9560b2; NSC-Toolbox 6f780cb README blob 657f1613; REA b2f3dc81 README blob 4e525c0c. Original main SHA 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 and three false release flags unchanged.

2026-11-14 CI VERIFIED for code 671d4647fc98dc358ea03c72a7cf0f6ebbbd4cf2: foundation push run 43609927148 job 132492505994 COMPLETED SUCCESS, authentic 196810-char log inspected; distance-3 RLE tests 3/3, release flags guard 26. Compressed-candidate push run 43609927107 job 132492505934 COMPLETED SUCCESS, authentic 19140-char log inspected; batch tests 11/11 including new run-encoder integration. Prior decoded batch run 43571173349 job 132375700550 SUCCESS authenticated. All evidence SYNTHETIC/OFFLINE, not native consumer ABI, real compressed PRM, CPK repack, Switch gameplay or Uzuy. No runtime hooks, original main 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9/Sakura aura107/Event236 variants unchanged; three release flags false. Next authenticate compressed PRM and prove engine ownership/lifecycle/archive precedence before any runtime path.

2026-11-14: NEW PENDING CI optional CRILAYLA distance-3 run encoder for offline compressed PRM batch; default literal unchanged. Local independent roundtrip/boundary/random/repeating checks 3/3 PASS, GitHub Actions pending. No CPK repack, authentic PRM, native ABI, ownership, archive precedence or Uzuy. Parent eb4dd9d85f7f30e399d7cd30095ac9e153fa7713. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 unchanged; Sakura aura107 and both Event236 forms untouched; release flags false. Sources: NSC-ModManager README blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709 (Steam-only); NSC-Toolbox README blob 657f161390c4abe8afe10cea11a2b9a28e6bf6b0; REA README blob 78b7064b8053b0076b4329013611881f395b6aba. Next: inspect HEAD push Actions full job log and fix CI; obtain authentic compressed PRM and native consumer ABI proof.

2026-11-14: decoded PRM batch exporter now mmap SHA-pins original CPK once, parses TOC once, disk-stages candidates, and publishes via exclusive hard links with rollback. Added synthetic one-index/no-read_bytes and publication-failure tests. Parent 94d7dd375e4cb3a5a67fa306a84410694fb2db77; code db6275eb0d9f0ead9a1d1ffb04b3f7968bb54e10. CI for final HEAD PENDING, no authentic compressed PRM or Switch consumer ABI/Uzuy proof. Original main 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 untouched; Sakura aura107, both Event236 forms, three false flags preserved.


2026-11-14 — PENDING CI: SHA-pinned static ARM64 ADRP+LDR and literal-LDR code references to relocation-pair candidate bases; independently tested positive, negative, truncated and wrong-main cases. Original main untouched. This does not prove X8 runtime identity, ABI, ownership, async, unbind, destructor, archive precedence or Uzuy. Upstream: NSC-ModManager release 2.1.2.1 (2026-08-30), NSC-Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983, REA da91bbd4eb417405895ff2621b2798e1f598d30e. Parent 84e2dd1d5255e0a12eedabfdb353bb8bc0c07535. New HEAD/run/log pending. Preserve Sakura aura107, Event236 marked/unmarked, all release flags false.

2026-11-14 FOLLOW-UP: First exact-main relocation-pair census CI 43482768847 job 132083236699 COMPLETED SUCCESS, authentic 193725-character log inspected, candidate counts +0xC0=217495, +0x58=219222. These are syntactic pairs, NOT unique objects or resolved dispatch. Large exhaustive JSON was replaced with deterministic SHA256 of all pairs, count and first eight candidates; new bounded-report HEAD CI PENDING. No native ABI, lifecycle or Uzuy proof.

## 2026-11-14 — FileOpen indirect method relocation pair census (PENDING CI)

Parent 95335d5b88550925149730eb2da74e0e3964702b. New exact-main SHA-pinned read-only relocation pair census for the two observed FileOpen X8 method offsets +0xC0 and +0x58; independently relocated candidate base and executable target required. Positive, negative, duplicate, alignment, and out-of-text tests plus original-main replay. This tests static candidate layout, NOT runtime X8 value, actual vtable identity, ABI, ownership, lock/async, unbind, destructor, archive precedence, or Uzuy. Primary references checked 2026-11-14: NSC-ModManager release 2.1.2.1 (2026-08-30) https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1 ; NSC-Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983 ; REA 3cb75d46bf6ee0a44d846a4d3e2cc3196e9ba418 . Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; no game binary edited. Sakura aura107 and Event236 marked/unmarked untouched. All three release flags remain false. New HEAD CI and authentic job log PENDING; no PASS claim. Next read push-run job log, repair failures, then correlate X8 object construction to actual candidate pointer addresses before any hook.

2026-11-13 — ATOMIC OFFLINE COMPRESSED PRM BATCH: commit 3db467b683b996011a34b62e52105b7db6a4a4b0, Actions 43344801740 job 131621435819 COMPLETED SUCCESS, authentic log inspected (5 new batch + 5 existing candidate tests). Added read-only SHA-pinned mmap multi-member compressed candidate exporter, deterministic roundtrip, duplicate/collision rejection and rollback on failed second output; no CPK repack. Only synthetic fixtures; no native ABI, ownership, archive precedence or Uzuy. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 marked/unmarked, release flags false. Source anchors: ModManager 276116eb, Toolbox 6f780cb, REA b2f3dc81. Next authenticate real compressed PRM and native consumer contract; don't repeat passed tests unless code changes.
## 2026-11-13 — Memory-mapped compressed PRM candidate extraction (PENDING CI)

The SHA-pinned offline candidate exporter now maps its input CPK read-only instead of materializing a full archive bytes object. The existing decoded Event236 integrity proof and literal-only CRILAYLA roundtrip remain mandatory. A regression patches Path.read_bytes to fail during export. This is synthetic-only and does not prove native consumer ABI, archive precedence, installability or Uzuy. Upstream pins: NSC-ModManager 276116eb README blob 8e9560b2, NSC-Toolbox 6f780cb Program.cs blob 9d5f3e0, REA b2f3dc81 README blob 4e525c0c. Original main/Sakura/Event236/three false flags unchanged. New HEAD Actions original log NOT VERIFIED.


## 2026-11-13 — CRILAYLA literal encoder bounded-memory implementation (PENDING CI)
Source a56661acf3ad10eae435c1b19516b00c80a95000 replaces nine Python bit integers per decoded byte with a packed output bytearray; test b224852e3e75a73b97a31363e78ec2eb3eb7bea9 compares exact stream bytes with independent legacy reference across 10 boundary lengths, plus decoder replay. Local independent 10-size comparison PASS; GitHub HEAD workflow log NOT VERIFIED. No authentic game PRM, archive repack, consumer ABI or Uzuy. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 both forms and false release flags unchanged. Upstream pins: NSC-ModManager 276116eb README blob 8e9560b2; Toolbox 6f780cb README blob 657f1613; REA b2f3dc81 README blob 4e525c0c. Next inspect HEAD push Actions original job log, then authentic compressed PRM validation.
## 2026-11-12 — Decoded Event236 semantic provenance (PENDING_CI)

2026-11-12: Parent 581eb15b1f720adab16c030bea9da0d23fa6d50a push Actions run 43190559263 job 131088483249 COMPLETED SUCCESS, authentic 191048-character job log inspected: 4/4 batch tests and RELEASE_FLAGS_FALSE_STATIC_CI_GUARD_PASS 26. New decoded Event236 per-record provenance ledger: opcode, original/candidate marker, exact decoded offset, native/previously/newly marked classification, consistency checked against mark() counts. Synthetic only, no compressed stream offsets, native consumer, repack or Uzuy. NEW CI PENDING. Upstream: NSC-ModManager release 2.1.2.1 (2026-08-30), NSC-Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983, REA b2f3dc81fa503c2b9ff0d8625336ed2e74d1e829; none establishes Switch ABI. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 native and marked, three false flags preserved. Next: verify new HEAD push Actions and raw job logs; authenticate actual compressed PRM before repacker.

## 2026-11-12 — SHA-pinned decoded-only compressed PRM CLI (PENDING_CI)

Parent `b9b302f15b9924dfd4eda4f4e30d5d099edda8ec`. Added `tools/export_decoded_prm.py` to export the already validated CRILAYLA Event236 decoded candidate to a new exclusive file, with source SHA256 validation, output SHA256 evidence and explicit `output_is_installable=false`; no CPK repack or engine write. Added `tests/test_export_decoded_prm.py` for synthetic positive integrity, wrong SHA, absent path, decoded size bound, and existing output preservation. No local execution or Actions log verified yet. Source anchors checked: NSC-ModManager v2.1.2.1 README blob `8e9560b2`, NSC-Toolbox v2.1.2.1 README blob `657f1613`, REA `b2f3dc81` README blob `4e525c0c`. None proves Switch ABI. Original pinned main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`, Sakura aura107 and Event236 both variants preserved; release flags false. Next: obtain direct push Actions run/job and original logs, fix any test failure, then validate authentic compressed PRM fixture before repacking.

## 2026-11-11 — Correct call-free FileOpen BR witnesses across indirect BLR (PENDING_CI)

Original pinned main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. A prior call-free path filter excluded direct BL but accidentally allowed BLR indirect calls, which decode_edge classifies separately. The filter now excludes both; negative BLR-only regression and byte-verified pinned-main replay added. This is conservative syntactic evidence, not native consumer ABI, ownership, lifecycle, archive precedence or Uzuy. Upstream NSC-ModManager 2.1.2.1 release (2026-08-30), NSC-Toolbox 6f780cb, REA 4a1c4a5, cpktools eff288cf9 remain reference sources; no cross-OS ABI inference. All three release flags false. Await HEAD CI and raw log.

## 2026-11-10 — Exact byte-witnessed bounded FileOpen entry-to-BR paths (PENDING_CI)

Parent 1de606ab3597ae4f7430c3c75f585cd6d0eedcea. Original-main SHA256 remains 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. Read-only external-edge census now emits a deterministic shortest local path with exact four-byte instruction witnesses for each external inbound target that syntactically reaches BR X1/X2. Positive, terminal, cycle and authentic-main replay checks independently verify every edge and instruction byte. This makes the BR-path candidates actionable without confusing high-fanout unrelated callees with ABI proof. Calls may change state or not return, indirect branches remain unknown, and no owner/lifetime/async/archive precedence or gameplay is established. Upstream pins: ModManager 276116eb (release 2.1.2.1, 2026-08-30), Toolbox 6f780cb (2.1.2.1), REA 4a1c4a5, original pinned main. All three release flags false. Await HEAD push CI and original job log.


## 2026-11-10 — Pinned original main reaching-definition evidence emitted (PENDING_CI)

Parent 09ee191cca9863fc1f948cfc8d86f7ae34f01d41. The previously synthetic-only `reaching_writers` traversal is now executed for both SHA256-pinned original FileOpen BR sites by the production `analyze()` report. JSON records exact four-byte instruction witnesses and conservative unknown call/external-predecessor states. Regression cross-checks emitted evidence against independent direct invocation for each original site, bounds, byte lengths, and false ABI/memory claims. This is bounded hypothetical-entry provenance, NOT verified native consumer ABI or runtime value. Research: NSC-ModManager 276116eb README blob 8e9560b2 (Steam only), NSC-Toolbox 6f780cb Program.cs blob 9d5f3e0, REA 4a1c4a5; pinned main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. Preserve Sakura aura107, Event236 marked/unmarked and all false flags. Await new HEAD Actions raw job logs.
## 2026-11-10 — Hypothetical window-entry CFG reachability (PENDING_CI)

Parent 9b4dd62fdda7dfdbb178d875912f660cc12f5dd7. Source: original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; upstream NSC-ModManager 276116eb and NSC-Toolbox 6f780cb, REA and cpktools previously pinned. Existing syntactic census can count predecessors from unreachable instructions. Added a separate bounded reachability traversal from hypothetical window start; dead instructions remain in raw census but are excluded from reachable merge evidence. Tests cover conditional merge, skipped dead instruction, pinned original SHA, mutation rejection and bounds. Window start is NOT a proven function entry; no consumer ABI, runtime pointer, ownership, archive precedence or Uzuy proof. All three release flags remain false. Await authentic HEAD CI logs.

## 2026-11-09 — FileOpen indirect BR register-definition evidence (PENDING_CI)

Parent 2e7814d5eb692f02884dbbabcecabd49f752d49b. Primary source pins: Switch main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; TheLeonX/NSC-ModManager 276116ebf5ba398a867793cb02ee6c33c0927645 README blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709 (Steam-only); NSC-Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983 Properties/Program.cs blob 9d5f3e0dfa4ed51cf7924b503081a87b12146f64; REA 4a1c4a59ba4ea964115fd36001ac3d2c05133fc6 README blob 5c894fb7a5900392412a65d284c1d99b911be635; cpktools eff288cf9c5b844269b215a920fe36e198aee4c9 README blob 51686733d46e4b99d43ccd865f4d9941fecd3a9e. None establishes Switch ABI.

New read-only evidence producer captures original instruction bytes and backward syntactic register definitions for BR X1 @0x116B724 and BR X2 @0x116B430. Tests reject mismatched branch register, malformed alignment, invalid window, tampered main; CI outputs machine-readable JSON. Memory values, cross-block path merges, object ownership, async, archive precedence and runtime remain UNRESOLVED. No game hook, no flags changed. Await HEAD CI and raw job log.

## 2026-11-09 — Bounded nonadjacent ARM64 PC-family reference evidence (PENDING_CI)

Primary sources: original Switch v1.70 main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; TheLeonX/NSC-Toolbox Properties/Program.cs commit 6f780cb6814f07e03c16b3e78d97dde4e4368983 blob 9d5f3e0dfa4ed51cf7924b503081a87b12146f64; NSC-ModManager commit 276116ebf5ba398a867793cb02ee6c33c0927645; CRI reference cpktools eff288cf9c5b844269b215a920fe36e198aee4c9. Previous adjacent-only census returned zero candidates. New bounded read-only scanner searches nonadjacent ADRP/ADD, stopping on clobbers and control transfers; synthetic regressions and SHA-pinned original-main CI pending. No consumer ABI, lifecycle, archive precedence, runtime or Uzuy claims. Original main, Sakura aura107, Event236 and three false flags unchanged.


## 2026-11-08 — Offline PC multi-mod file/directory namespace collision guard (CI pending)

Added fail-closed source path prefix collision detection across mods and families, including casefold and both file/child ordering directions. Three regression cases cover forward/reverse collision and non-conflicting siblings. This does not prove engine archive precedence, consumer ABI, or Uzuy runtime. Original main and gameplay hooks unchanged. Release flags remain false.

# Port ModdingAPI Switch: implementation checkpoint

**Belum full ModdingAPI dan belum siap uji gameplay.** Binary berhasil dikompilasi;
status ini tidak berubah hanya karena seluruh tes di bawah lulus. Tidak ada paket
instalasi baru yang diterbitkan oleh workflow branch ini.

## Perubahan yang sudah diimplementasikan

- Identifikasi SHA256 seluruh text Switch 1.70 sebelum pemasangan hook/perubahan
  main. Hanya dua text yang diaudit diterima: stock dari input pengguna dan R180.
  Build ID saja tidak cukup karena keduanya memiliki Build ID yang sama.
- Tiga perubahan PRM R180 yang sebelumnya berada pada `main` kini masuk rencana
  patch RAM. Alokasi 16,384 byte, kapasitas 1,024, dan batas iterasi harus cocok.
- Loop `data/spcload/<char>prm_load.bin.xfbin` kini memakai batas 1,024 yang sama.
  R180 menghentikannya pada 282. Getter char-code native memeriksa jumlah dinamis
  dan loop melewati hasil null. Ini **bukan bukti** seluruh game mendukung
  1,024 karakter: factory, roster, aset dan konsumen lain masih harus diverifikasi.
- Tabel condition descriptor 32 byte dan raw conditionprm 176 byte dipisahkan.
  Raw getter menerima batas dari alokasi native sebenarnya; tidak lagi diperluas
  ke 517 hanya karena descriptor berjumlah 517. CPK Tobi yang diperiksa ternyata
  mempunyai dua varian: raw 512 dan raw 517. Callback mencatat owner, alamat dan
  jumlah; alamat yang berubah atau tidak dikenal ditolak. Metadata dihapus pada
  jalur reload dan kedua jalur destructor sebelum alamat digunakan ulang.
- Rencana patch RAM berisi 33 word: 4 kapasitas/loader, 4 batas descriptor,
  1 prasyarat P67, 24 word koridor P128. Dengan profil kondisi kosong, empat word
  descriptor tetap bernilai stock; perubahan nyata adalah 29 word dari stock
  dan 26 dari R180. Batas raw 512 dibiarkan utuh sampai
  getter diganti oleh callback berbasis alokasi.

Source dasar adalah branch recovery R183, dengan rollback D-pad R181 yang sudah
ada di sana. Arsip R180 pengguna tetap menjadi pembanding. Perubahan ini tidak
mengklaim memperbaiki semua perilaku D-pad, True Awakening, maupun UJ.

## Bukti pengujian

Lihat JSON dalam `reports/port_foundation/`. Tes mengompilasi source produksi,
menjalankan callback ARM64 hasil build, dan menjalankan potongan instruksi main
Switch asli. Tidak ada laporan gameplay PASS.

- 14 vektor SHA256 dibandingkan dengan Python; dua profil main diterima dan 36
  mutasi text ditolak sebelum hook/write. Lima kerusakan rencana patch juga
  ditolak langsung oleh validasi rencana.
- Hasil patch dari main stock dan R180 identik. Main sumber tetap tidak ditulis.
- Alokasi/copy raw condition: 0, 1, 511, 512, 517, 1,024 record, dengan 60 kasus
  batas dan pemeriksaan byte penjaga. Empat kasus storage tak dikenal ditolak.
- 40 siklus pergantian owner/release; 12 kegagalan fingerprint installer menulis
  nol hook. 20 kasus menjalankan assembly penyimpanan/pemulihan register inline
  exlaunch, dengan entry/trampoline yang dibentuk sesuai implementasi pinned.
- Masing-masing 1,024 kasus batas loop PRM dan spcload; alokasi PRM 16,384 byte.
- Loader char-code native dengan 281, 282, 286, 400 dan 1,024 entri; 50 kasus
  getter, salinan byte identik, penjaga alokasi utuh.
- Rantai installer compiled dengan profil factory aktif mengajukan 20 lokasi hook
  berbeda. Getter raw memakai replacement, sehingga diperlukan 19 trampoline
  dari kapasitas 20. Profil factory kosong tidak memasang hook factory.
  Publikasi hook dan pemetaan executable oleh OS dimodelkan dalam tes ini.
- Tiga segmen NSO identik dengan ELF, checksum cocok, segment permissions RX/R/RW,
  tanpa DT_NEEDED; dua import `nn::ro` sesuai bootstrap yang digunakan.

Allocator, memset, diagnostic logging, serta bagian konteks OS/RTLD yang tidak
sedang diuji dimodelkan. Tes ini tidak menjalankan game penuh dan tidak membuktikan
ketersediaan resource, konstruksi/destruksi actor secara lengkap, atau kecocokan
emulator Android.

## Pekerjaan yang masih menghalangi port penuh

Dispatcher Event236 kini mengenali penanda eksplisit pada PRM hasil konversi;
sejumlah helper legacy masih menyaring ID karakter. Operasi 12/13/18 dan banyak
operasi lainnya masih tanpa efek. Kontrol 14/15 kini menulis permission native;
kesetaraan aksi semua subclass belum terbukti. Opcode 23
terbatas koridor UJ tertentu, voice belum setara, projectile 27–29 belum dipetakan.
CPK kini memakai daftar path eksplisit (maksimal 32); penemuan arsip, penggabungan
parameter, dan siklus selesai-load/unbind belum terintegrasi. Descriptor kondisi
kini berbasis profil append-only; membership ougi masih generated untuk data lama. Factory berbasis profil sekarang terintegrasi untuk 228 selector yang namanya
cocok, tetapi 53 nama placeholder, reset global saat factory PC, parameter API
lainnya, repacking PRM terkompresi,
lifecycle timer/actor, kamera, audio, serta multi-mod belum selesai diintegrasikan.

Tidak ada dasar untuk menyebut binary ini “full API” atau meminta pengguna
memasang ini sebagai hasil selesai. `PORT_STATUS.json` mempertahankan status false.

## Mengulangi pemeriksaan

Workflow `verify-port-foundation.yml` memakai image resmi devkitpro/devkita64
amd64 pada digest `sha256:82575ea78651b530b2e232bb3799cfd1fe331514e053d5f724bb4b28191fb79d`.
Unduhan langsung package toolchain ditolak HTTP 403 pada runner; image tersebut
sudah berhasil menjalankan build dan tes fondasi di GitHub Actions.
Jalankan workflow baru ini untuk branch implementasi; verifikasi R181/R183 lama
menguji layout 30-word historis dan tidak menjadi acceptance test perubahan ini.
Workflow hanya mengunggah JSON bukti, bukan main, ELF, atau paket gameplay.

Input test main R180 yang sudah ada dalam repository digunakan secara read-only.
`prepare_test_images.py` membalik empat word yang diaudit untuk merekonstruksi
text stock, kemudian memeriksa SHA256 text stock secara penuh.

Acuan PC: TheLeonX/NSC-ModManager commit
`276116ebf5ba398a867793cb02ee6c33c0927645`, runtime source UltimateStormAPI
`a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`. Perbandingan source ini tidak dianggap
sebagai bukti otomatis bahwa seluruh perilaku DLL distribusi sudah dipindahkan.

## Factory berdasarkan parameter PC

`specialCondParam` raw 32 byte dibaca berurutan; nama dinormalisasi ke uppercase
`COND_`, owner diambil dari uint16 little-endian pada offset 24. Entri owner yang
sama mengikuti aturan PC: entri terakhir menang. Perubahan ID PC ke slot Switch
harus diberikan eksplisit, tidak ditebak dari nama karakter. File NUCC yang masih
berbungkus, record terpotong, nama tak dikenal, dan selector placeholder belum
terbukti ditolak dengan pesan kesalahan.

228 nama dari 281 nama PC cocok dengan characode Switch pada ordinal yang sama.
Profil serialized diperiksa ukuran, magic, versi, SHA256, urutan owner, kapasitas,
selector, reserved bytes, dan padding sebelum rencana patch main berjalan.
Default module memakai profil kosong: tidak otomatis mengaktifkan factory Tobi.

`tools/compile_factory_profile.py` dapat menyisipkan profil ke data NSO dengan
Python standar, tanpa compiler C++ di Android. NSO input harus cocok dengan SHA256
input yang disebutkan. Semua hash segmen diperiksa; text, rodata, virtual layout,
dan build ID modul dipertahankan; hanya isi profil data dan header penyimpanannya
berubah. Nama output sengaja menunjukkan ini komponen yang belum menjadi paket
uji gameplay. Tool ini belum mengubah aset PC, CPK, seluruh parameter, atau PRM.

Tes tambahan: 4,170 penolakan profil C++ rusak, 684 variasi nama record PC,
53 nama placeholder ditolak, pemetaan maksimal 1,024 owner, round-trip konfigurasi
NSO, serta pembandingan decoder LZ4 dengan liblz4. Native factory diuji melalui
12,240 kasus rute dengan 17 skenario flag native. Konstruksi mendalam dimodelkan,
bukan dinyatakan berhasil dimainkan. Dalam 18 kasus caller/initialization nyata,
selector kelas 58 mempertahankan ID roster 145, 281, atau 457, mode dan sisi.

Callback native menyeleksi kelas, bukan mengganti ID di actor. Lifetime,
resource loading, reset global ModdingAPI PC, dan subclass behavior penuh masih
belum terbukti. Rincian batas model ada di `native_factory.json`.

## Kepemilikan Event236 dan koreksi audit PRM

Event236 bawaan adalah perintah enemy-hide. Menganggap semua event236 dari
karakter >280 sebagai ModdingAPI menyebabkan salah klasifikasi dan mengecualikan
mod yang mengganti ID stock. Runtime sekarang menerima event API hanya jika
record236 memiliki penanda uint16 `0x4E53` pada offset `0x2A` dan opcode1..29.
Record tanpa penanda menjalankan callback native; record bertanda dengan opcode
invalid atau role yang belum didukung dikonsumsi tanpa menjalankan enemy-hide.

`tools/mark_api_events.py` mengonversi plaintext PRM yang **sudah diketahui**
memakai PC ModdingAPI. Field penanda harus nol atau penanda yang sama. Tool tidak
menebak dari ID karakter. Event236 opcode0/unknown tetap native. Konversi CPK dengan PRM tidak terkompresi kini tersedia melalui
`tools/mark_cpk_events.py`. **CPK lama belum berpenanda tidak boleh langsung
dipasangkan dengan module branch ini sebagai paket selesai**.

Aturan panjang record diambil dari instruksi pembaca Switch, termasuk predicate
`0x7938D0`, bukan tebakan berdasarkan adanya kata DMG pada string suara.
Pemeriksaan terhadap input Tobi memperbaiki hitungan lama: 4,876 function record,
566 event236 = 561 operasi API + 5 operasi native. Opcode26 berjumlah **9**, bukan
4. Lima string suara sebelumnya salah dianggap bagian damage extension oleh
analisis lama. Konverter baru hanya mengubah 1,122 byte penanda pada 561 record.

Bukti ARM64: 11,042 kasus pembacaan record, termasuk seluruh 4,876 record Tobi
sebelum/sesudah konversi, serta 378 kasus dispatcher dengan ID0/145/276/280/281/
1023/1024, side0/1/2, marked/unmarked/foreign marker, opcode0/3/30, dan ada/tidaknya
musuh. Instruksi native mempertahankan penanda saat raw64/160-byte record menjadi
runtime72-byte record. Dispatcher asli menjalankan callback compiled; perubahan
skill pada opcode3 hanya terjadi pada event API yang valid. Enemy lookup dan
method visibility musuh dimodelkan, sehingga ini bukan bukti rendering/gameplay.

Perubahan ini tidak mengisi operasi MovesetPlus yang masih shadow/no-op. Full API,
paket gameplay, dan kecocokan emulator tetap belum selesai/diverifikasi.


## Kontrol enable/disable native (opcode 14/15)

Adapter `nsc_controls.cpp` memanggil setter native `0x93D8` dan `0x93C4`.
Getter `0x7D4588` mengakses array Switch pada actor+`0x1214C`; offset PC
`0x12A34` tidak dipakai untuk menulis actor Switch. Seluruh 16 word ketiga
fungsi diverifikasi sebelum perubahan game. Kegagalan menghapus base adapter.

Kontrak berasal dari source PC commit `a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`,
blob MovesetPlus `d7c5dbbebd60415f8d304321f083897658a86146`, fungsi
`me_enable_control`/`me_disable_control`. Selector 0..19 diterjemahkan ke index
permission native. Target nol berarti diri sendiri; semua nilai nonnol berarti
musuh. Enable19 juga enable1 karena fallthrough pada source; disable19 hanya
mengubah far attack. Selector invalid, null actor/target/vtable/method ditolak.
Adapter tidak menyimpan pointer actor dan tidak membuat thread/timer.

Pengujian mengeksekusi callback Event236 compiled: 720 kombinasi ID roster,
opcode, selector dan target; 48 kasus negatif; 16 mutasi fingerprint; 40 slice
konsumen virtual native. Seluruh 128 KiB alokasi masing-masing dari dua actor
dibandingkan, bukan hanya field yang diharapkan berubah. Pembacaan tabel aksi
native `0x80F170` mengonfirmasi 12 rujukan animasi untuk 9 selector. Untuk selector
lain, call-site dan pembacaan index sudah diuji, tetapi arti semua jalur aksi dan
override subclass **belum** dianggap setara penuh. Angka 20 selector bukan bukti
seluruh perilaku kontrol gameplay sudah lulus.

Notifikasi UJ P64 yang sudah ada dipertahankan untuk enable/disable1 dan
fallthrough enable19. Lifetime registry P64 masih perlu perbaikan terpisah;
permission default=1 tidak dipakai sebagai pengganti opt-in eksplisit ke bypass UJ.
Timer opcode16 tetap belum diimplementasikan.

## Penanda PRM dalam CPK

`tools/mark_cpk_events.py` menerima hash input wajib dan daftar path PRM yang
secara eksplisit diketahui memakai ModdingAPI PC. Output selalu direktori baru.
Tool tidak menebak kepemilikan event dari nama file atau ID karakter. Seluruh
input divalidasi sebelum output dibuat. Metadata CPK/UTF, path, ID, offset,
padding, serta payload yang tidak dipilih dipertahankan byte-for-byte.

Cakupan saat ini: TOC di depan content, table UTF plaintext, PRM tidak
terkompresi, tanpa CRC/table tambahan. PRM terkompresi atau skema checksum yang
belum didukung ditolak, bukan disalin sebagai seolah sudah dikonversi. Ini belum
menjadi importer `.nsc` umum. Registrasi multi-CPK terpisah dijelaskan di bawah.

Tes sintetis memeriksa dua PRM, ID tidak berurutan, path tidak tersortir, payload
PRM lain yang sengaja tidak dipilih, idempotensi, dan 35 input invalid.
Pada CPK Tobi input SHA256
`a9dc66fad84fc07c1d29dba08b47e330a756c945c662ed22df201c37506f4a50`,
93 entry dan ukuran 173,996,544 byte tetap sama. Tepat 1,122 byte pada 561 event
API berubah; lima event236 native tetap utuh. Hasil konversi hash
`b7605e5cca9a9072ac28629b5028c2f46c8da168d279c41cff6a4067c18f3250`.
Tidak ada file game atau CPK tambahan yang dipublikasikan bersama perubahan ini.

Semua pengujian menggunakan module yang sama, dibangun dari layer image resmi
pinned yang sama dengan CI. Hasil komponen ini tidak mengubah status port penuh
atau kesiapan paket gameplay.


## Registrasi CPK berdasarkan profil

Path Tobi hardcoded dihapus. Profil default kosong, kapasitas 32, record 208 byte,
path ASCII maksimum 191 byte di bawah `sim:data/moddingapi/`, ekstensi `.cpk`.
Prioritas integer 0..2147483647 harus berbeda; path duplikat tanpa membedakan
huruf besar/kecil, traversal, padding/reserved nonnol, dan SHA256 salah ditolak.
Profil diperiksa saat startup sebelum penulisan game; bukan konfigurasi hot reload.

Contoh manifest komponen (nama path harus mengikuti CPK yang benar-benar tersedia):

```json
[
  {"path": "sim:data/moddingapi/mod_a.cpk", "priority": 32},
  {"path": "sim:data/moddingapi/mod_b.cpk", "priority": 33}
]
```

```sh
python tools/compile_cpk_profile.py --manifest cpk.json --output cpk_component
```

Untuk menyisipkan profil ke module, tambahkan `--module <subsdk9>` dan
`--expected-module-sha256 <hash-input-aktual>`. Output harus direktori baru.
Tool menggunakan Python standar. Profil factory dan CPK dapat diterapkan berurutan;
tes membuktikan hasil akhir identik dalam kedua urutan. Hash yang diberikan pada
langkah kedua harus hash hasil langkah pertama. Text/rodata/layout tetap identik.
Ini tidak membuat atau mengonversi isi CPK secara otomatis.

Callback memakai binder Switch `0x473190`, adapter `0x115FBB8`, dan manager
`0x115E80C`. Temuan native: manager bisa mengembalikan 1 tanpa mengisi bind ID
ketika handle binder atau alokasi tidak tersedia. Karena itu registrasi hanya
dicatat ketika return nonnol **dan** ID nonnol; nilai return saja tidak cukup.
Argumen tambahan descriptor diinisialisasi nol, prioritas diteruskan ke wrapper
native, dan hasil serta output caller asli dipertahankan. Jalur gagal awal tidak
menambah dereference output pointer yang tidak dibaca native.

Registrasi tambahan dicoba setelah bind `sim:` asli yang berhasil dan menghasilkan
ID. Hanya entri gagal yang dicoba ulang pada kesempatan berikutnya. Reentry dan
callback bersamaan tidak menyebabkan bind ganda. Path tersimpan selama lifetime
modul; tidak ada tambahan hook atau trampoline. Registry belum menangani unbind
atau pergantian manager. ID diterima bukan bukti selesai baca arsip asinkron,
prioritas efektif saat lookup, file tersedia, atau parameter berhasil digabung.

Bukti: 6,740 profil korup dan delapan manifest invalid ditolak; kapasitas 0/1/31/32,
reentry, callback bersamaan, preservasi state saat profil invalid, dan komposisi
kedua packer diperiksa. Sebanyak 19 skenario ARM64 menjalankan callback compiled
dan wrapper/manager native, mencakup root/handle/alokasi tidak tersedia, bind gagal,
ID nol, sukses, prioritas, retry, dan bit ke-31. Operasi CRI, allocator/constructor,
locking dan logging dimodelkan. Detail ada pada `cpk_profile.json` dan
`native_cpk.json`. Pengujian seluruh game dan emulator belum dilakukan.


## Descriptor kondisi berdasarkan parameter PC

Tabel lima kondisi Tobi yang hardcoded dihapus. Profil default tidak menambah
kondisi. Compiler membaca satu `conditionprmManager.xfbin` PC yang sudah digabung,
berformat raw record 112 byte: nama 48 byte, nama reaksi 48 byte, empat uint32.
Ini berbeda dari `conditionprm.bin.xfbin` game yang menyediakan raw record 176 byte.
Keduanya tidak boleh diperlakukan sebagai file yang sama.

512 record awal wajib cocok dengan template NSC ModManager commit
`276116ebf5ba398a867793cb02ee6c33c0927645`, SHA256
`fae4c1e1a510f895a7b9b9acbf5b710e7472e9b47f3471087dd4b1c97b7b86c5`.
Baseline PC direkonstruksi independen dari tabel native pada tes dan hash-nya
cocok dengan file upstream. Ada satu perbedaan: descriptor103 `AWAKE_1SKR`
memiliki aura5 pada PC dan aura107 pada Switch. Runtime memakai getter native
untuk seluruh index stock, sehingga metadata Switch tetap dipertahankan.
Stock edits/reordering ditolak; tidak diam-diam dianggap kompatibel.

Entri tambahan mempertahankan ordinal PC512..1023. Nama maksimum 48 byte ASCII,
referensi reaksi diterjemahkan ke index nama pada tabel lengkap. Nama reaksi tak
tertemukan mengikuti source PC (index0) dan dicatat dalam laporan. Nama tambahan
yang bertabrakan dengan entri sebelumnya ditolak. Semua field descriptor diteruskan
sesuai layout 32 byte yang dibuktikan, tanpa mengubah actor. Ini belum membuktikan
kesetaraan setiap ID efek atau asset yang dirujuk.

```sh
python tools/compile_condition_profile.py \
  --param conditionprmManager.xfbin --output condition_component
```

Opsi `--module` dan `--expected-module-sha256` menyisipkan profil ke module yang
dibangun tanpa compiler C++ di Android. Input tetap utuh dan output harus direktori
baru. Keenam urutan konfigurasi factory/CPK/condition menghasilkan NSO akhir yang
identik. Profil kondisi diperiksa sebelum perubahan game; pemuatan profil saat
game berjalan tidak didukung.

Empat loop nama/hash native kini memakai jumlah512+entri tambahan yang sama dengan
getter. Batas tersebut tidak memperbesar alokasi raw176 secara membabi buta:
raw getter tetap memakai ukuran yang ditangkap dari loader native. Pengujian
mencakup jumlah512,513,517,1024, termasuk hasil tidak ditemukan dan index invalid.
Kapasitas descriptor bukan klaim bahwa 1,024 karakter atau semua kondisi sudah
berhasil dimainkan.

Bukti terbaru: 41,037 profil korup ditolak, sembilan tabel PC invalid ditolak,
2,578 kasus getter ARM64, 124 lookup melalui empat loop native, 135 pembacaan
field konsumen native, empat konfigurasi installer, dan 21 kegagalan fingerprint
installer tanpa pemasangan hook. CRC native dan tabel CRC game dijalankan;
strcmp/strlen, publikasi hook, logging, dan konteks caller beberapa slice dimodelkan.
512 descriptor native dibandingkan byte-for-byte, termasuk pointer nama.

Yang masih tertunda: packaging dan keselarasan urutan raw176 companion, pengubahan
descriptor stock, pemetaan efek lintas-platform, lifecycle penerapan/penghapusan
kondisi secara penuh, dan gameplay. Profil ini merupakan komponen source, bukan
paket instalasi atau bukti port ModdingAPI selesai. `PORT_STATUS.json` kini merinci
11 keluarga parameter: dua memiliki implementasi parsial dan sembilan belum
memiliki reader generik yang terintegrasi.

Provenance reader PC: [ConditionPrmManager.cpp](https://github.com/TheLeonX/UltimateStormAPI/blob/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc/xinput9_1_0/ConditionPrmManager.cpp),
Git blob `3e7aacadca117b56e43f1a5c1d04cdd02aed7b1f`; template NSC ModManager
Git blob `0e7133223f10eb2dbbb39d2166fdca9352e84c3e`. Metadata blob dikonfirmasi
melalui GitHub pada commit pinned, bukan menggunakan nama file sebagai bukti versi.


## Companion raw176: validasi identitas ordinal

Compiler kini menerima opsi berpasangan `--raw-condition FILE --expected-raw-sha256 HASH`.
Sebelum membuat folder output, tool memeriksa SHA256, struktur NUCC, tepat satu binary
chunk bernama conditionprm, panjang 8+count*176, jumlah yang sama dengan manager,
dan nama raw64-byte pada setiap ordinal dibandingkan nama manager48-byte.
Raw disalin byte-identik sebagai `conditionprm.COMPANION_NOT_GAMEPLAY_RELEASE.xfbin`.
Tanpa opsi ini, mode descriptor-only sebelumnya tetap tersedia dan tidak mengklaim
raw sudah dipaketkan. Tidak ada perubahan runtime native atau patch main di tahap ini.

Dasar source NSC-ModManager pinned: ConditionPrmViewModel.cs blob
`f31476f325bdb7e5f5a3d7aa7ebf0383c7977b74` menulis nama pada awal record0xB0;
TitleViewModel.cs blob `f7ca7602d12cf9689a08fd6b7e55abc4dc8fd4ca` menggabungkan
raw dan manager secara terpisah dengan nama sebagai key. Kedua file lokal cocok
exact Git blob pada commit manager yang dicatat. Karena urutan dua daftar tidak
dijamin oleh jumlahnya, validator membandingkan nama per indeks, bukan count saja.

Tes baru lulus pada jumlah512/513/517/1024; 11 input invalid (termasuk reorder
stock/tambahan, duplicate, count mismatch, nama tanpa terminator dan truncation)
serta 4 hash invalid ditolak. CLI menolak pasangan salah sebelum output muncul,
mempertahankan input dan output lama, serta menyalin companion byte-identik.
Input nyata raw512 Tobi cocok dengan nama baseline PC512; raw517 romfs ditolak
ketika dipasangkan dengan baseline512. Original merged PC manager517 belum
tersedia dalam input pemeriksaan ini, sehingga tidak ada klaim pasangan Tobi517
sudah verified. Nama extras dicatat dalam condition_companion_real.json.

Batas bukti: kesamaan nama ordinal tidak membuktikan nilai stat/effect raw cocok
Switch. Native raw prefix values, effect dependencies, CPK precedence dan full
lifecycle masih pending. Seluruh raw bytes termasuk unknown fields dipertahankan.
Tidak ada paket instalasi gameplay. Selanjutnya buktikan baseline raw Switch dan
pasangan manager tambahan asli, lalu integrasikan dengan CPK/profile packaging.


## Single-archive condition bundle integration

`tools/compile_condition_bundle.py` binds the descriptor profile to the actual
`data/spc/conditionprm.bin.xfbin` entry inside a SHA-pinned CPK. No separately
supplied raw file can silently differ from the archive payload. Compressed raw
companions are rejected. Count/name/ordinal checks run before output creation.
Only explicitly selected known PC API PRMs are marked; other archive bytes,
metadata and the condition companion remain identical. With no selected PRMs the
archive is unchanged; this does not mean all movesets are API-compatible.

The tool emits condition.profile, cpk.profile, archive bytes under component_data,
and a report linking manager/raw/archive/profile hashes, CPK entry ID/offset,
explicit runtime path and priority. Optional --module plus expected SHA configures
both profiles. Existing CPK registrations must be empty or exactly the requested
single entry; a different list is rejected, not discarded. Factory profile and
other data bytes are retained. No installable romfs/exefs release is implied.

Local regression passed 11 malformed archive/argument cases, same-count reorder,
missing/compressed companion, exact PRM-marker diff, no-conversion archive equality,
idempotence and CLI rejection before output. Module order equivalence, preservation
of text/rodata/other data, and registration conflict rejection additionally passed
on a synthetic NSO data container; this is serialization proof, not execution.
The new CI step uses the built module for those same profile-composition checks.

Actual Tobi.zip.cpk raw512 with the pinned PC baseline512 also passed the pipeline;
561 API events marked, native enemy-hide events preserved. No extras were activated.
See condition_bundle_real.json. The original merged manager517 and native raw values
remain unverified. Priority42 and the sample sim path in the report are explicit
test settings, not proof of archive winner or complete loading.

Previous companion commit fc9e72d: all steps of run41929932638 succeeded. That CI
result predates this bundle change. Full API, gameplay readiness and emulator tests
remain false. Next: verify new CI, native raw baseline/value compatibility, actual
extra-descriptor pair, then asynchronous bind/precedence/resource lifecycle.

## 2026-11-05 — Multi-CPK preservation and raw176 value-audit prerequisite

Starting point: `a30b284` / Actions run41932841482 was green. The new work
below does not change the ARM64 runtime hooks. The module remains a component
foundation, not an installable or GAME_TESTED ModdingAPI release.

### Safe multi-CPK condition-bundle composition

Commit `40eab530d7d90811250cea085d941ca26b929651` added
`merge_cpk_registration` to `tools/portlib/condition_bundle.py`.
A bundle may append its one requested CPK to a valid existing registration
list, preserving order and every original entry. An exact duplicate is
idempotent. Case-insensitive path collisions with a different spelling or
priority, duplicate priorities, and a 33rd entry are rejected. An existing
nonempty condition profile differing from the requested table is also rejected:
appended condition ordinals may depend on a global combined manager and must
not be blindly concatenated or replaced.

`tools/compile_condition_bundle.py` now emits the EFFECTIVE `cpk.profile`
matching the configured NSO and reports requested versus effective hashes.
Tests cover existing-row preservation, 31→32 capacity, 32→33 rejection,
priority/path conflicts, condition-profile conflict, reconfiguration and CLI
artifact equivalence. Action run41937948988: success. This is profile packing
proof only. Archive precedence, file opening, async load completion and unbind
were NOT measured. A single bundle still includes only one archive's companion;
the change is not a global multi-mod condition-table merge.

### Raw176 comparison tool

Commit `4f190568f73973682023582e34ddb7587662c309` added
`tools/audit_condition_raw_values.py` and
`tools/portlib/condition_raw_audit.py`. The tool requires exact SHA256 for
both XFBINs and the pinned PC manager data, parses 176-byte rows, requires a
512-row stock file and matching candidate descriptor ordinals, and reports the
precise raw record byte offsets changed in the shared 512-record prefix.
Additional rows are identified by ordinal, name and SHA256 of the remaining
112 bytes. It does not assign meanings to unknown raw fields.

Example review-only command:

```sh
python tools/audit_condition_raw_values.py \
  --pc-manager merged_conditionprmManager.xfbin \
  --stock-raw stock_switch_conditionprm.bin.xfbin \
  --expected-stock-sha256 ACTUAL_64_HEX_SHA256 \
  --candidate-raw candidate_conditionprm.bin.xfbin \
  --expected-candidate-sha256 ACTUAL_64_HEX_SHA256 \
  --output new_raw_audit_directory
```

Only synthetic input validation was exercised in CI: one altered stock-prefix
record at offset77, one appended record, and seven invalid cases rejected before
CLI output creation. Run41938539789: successful; source provenance, real
Switch raw values, effect semantics and gameplay remain UNVERIFIED. Baseline
Switch raw XFBIN and the real merged manager517 remain inputs to obtain or
authenticate. Prior Tobi raw512 and romfs raw517 hash references are not
substitutes for the missing genuine stock-versus-candidate comparison.

No code in these two commits changes native actor/condition application,
existing UJ latch lifetime, unresolved factory placeholders, parameter-family
readers, archive precedence, or asynchronous CPK loading. `PORT_STATUS.json`
retains `IMPLEMENTATION_INCOMPLETE`, `full_moddingapi=false`,
`ready_for_gameplay_test=false`, and `emulator_tested=false`.

## 2026-11-05 — CPK overlap and CPK-to-CPK condition raw inspection

After checkpoint b4a8a95, two source changes were committed and verified:

1. Commit 96c8684db1fe8965b4ac8d6315ea3a878f06ffb6 adds
   tools/portlib/cpk_overlap.py, tools/audit_cpk_overlaps.py and
   tests/test_cpk_overlaps.py. The tool validates each archive against an explicit
   lowercase SHA256 and existing bounded CPK profile paths/priorities. It maps
   individual CPK TOC paths, compares exact/casefold path names and stored
   payload SHA256, marks conditionprm collisions, and distinguishes same stored
   bytes from unverified decompressed identity. Optional --reject-unresolved
   fails before output. Memory mapping avoids loading entire CPKs into Python.
   CI run41949468472: PASS. Fixture: two archives, three overlapping paths,
   two unresolved, eleven malformed manifests rejected. No real game archives
   supplied to CI and no precedence/asynchronous load/unbind proof.

2. Commit be2a86c6944dfcf84dada2f2b7ffd9fd43250ae2 adds
   tools/portlib/condition_archive_audit.py, tools/audit_condition_cpk_pair.py
   and tests/test_condition_archive_audit.py. Hash-pinned actual CPK entry
   extraction drives the existing raw176 comparator; it checks archive TOC
   geometry, uncompressed payload, embedded source offsets and SHA256,
   manager/companion name+ordinal agreement and stock-prefix byte deltas.
   Outputs are audit JSON only, not a module or release.
   CI run41950000370: PASS. Synthetic stock512 and appended513 companion,
   six invalid paired inputs rejected. This is NOT authentic stock v1.70 raw
   value evidence, not manager517 proof and not gameplay.

The user Library contains files named common.cpk and romfs.zip, but their
filename and size alone cannot authenticate unmodified stock origin. They
were materialized in the analysis environment, which then failed before
programmatic inspection. No SHA256 or condition values were obtained and
none are asserted. Only local file metadata was observed; no private
game archives were uploaded to this public GitHub repository.

Code inspection of CpkBindHook: it calls the verified original bind function
first and adds extra registrations only when the original status and bind ID
are nonzero. A successful bind ID is then logged, explicitly with
async_complete=unverified. The existing native CPK emulator models the
allocation/CRI registration paths; it does not run real CRI file I/O,
archive priority winner lookup, unbind or manager teardown. No new native
hooks were added, because offsets/ABI and lifecycle order beyond those
already established remain unproven.

Before using these tools on Android, supply only authenticated source files.
Review command for direct CPK pair (replace all paths and real hashes):

    python tools/audit_condition_cpk_pair.py \
      --pc-manager MERGED_PC_MANAGER517 \
      --stock-cpk VERIFIED_STOCK_CPK \
      --stock-cpk-sha256 ACTUAL_STOCK_SHA256 \
      --candidate-cpk VERIFIED_CANDIDATE_CPK \
      --candidate-cpk-sha256 ACTUAL_CANDIDATE_SHA256 \
      --output NEW_REVIEW_DIRECTORY

A rejection from this command is evidence of unsupported or inconsistent
inputs, not proof that the game cannot load them. Even on a successful audit,
actual raw field meanings and effect dependencies are still unverified.

Current stage: IMPLEMENTATION_INCOMPLETE; full_moddingapi=false,
ready_for_gameplay_test=false, emulator_tested=false. The next engineering
work is source authentication and the native asynchronous completion/
precedence/unbind investigation, followed by outstanding PC API features.

## 2026-11-05 — Disjoint multi-CPK condition batch packaging

Starting from 9437e8f764d374344656659d7cbeb24586e5afec, commit
6819a8c2321ad38f39389745a35ffff3d0948196 adds
tools/portlib/condition_batch.py, tools/compile_condition_batch.py and
tests/test_condition_batch.py. Action 41963328524 completed SUCCESS.
The new test ran two synthetic CPKs through the production TOC parser,
source SHA256 checks, Event236 PRM ownership marking, descriptor compilation,
and composed NSO data profiles. It rejected 12 invalid manifests and four
invalid manager/module cases. Preexisting registered CPK rows were retained;
other selected archives did not need to contain conditionprm. Tests also
verified unchanged original CPKs, collision rejection and non-clobber output.

This closes a packaging integration gap only: one explicitly declared CPK
must own data/spc/conditionprm.bin.xfbin, other CPKs may contain explicitly
selected known PRMs, and all CPK entry paths must be disjoint (including
casefold collisions). Different/identical duplicates are rejected because
native archive lookup precedence has not been proven. The manager is one
global pinned PC table; independently compiled condition tables are NOT
concatenated. The module is configured through existing condition/CPK
profile packers, with existing CPK registrations preserved and conflicts
rejected. A temporary staged output directory is renamed only after all
checks succeed. Output is deliberately named COMPONENT_NOT_GAMEPLAY_RELEASE.

Example review-only manifest (replace actual paths/SHA256 from proven sources):

    {
      "condition_owner": "sim:data/moddingapi/condition.cpk",
      "archives": [
        {"source": "input/condition.cpk", "sha256": "ACTUAL_SHA256",
         "path": "sim:data/moddingapi/condition.cpk", "priority": 10,
         "pc_api_prms": ["data/spc/known_pc_api_prm.bin.xfbin"]},
        {"source": "input/secondary.cpk", "sha256": "ACTUAL_SHA256",
         "path": "sim:data/moddingapi/secondary.cpk", "priority": 20,
         "pc_api_prms": []}
      ]
    }

Run on Android Termux with standard-library Python:

    python tools/compile_condition_batch.py \
      --manifest INPUT_MANIFEST.json \
      --pc-manager ACTUAL_PINNED_PC_MANAGER \
      --expected-manager-sha256 ACTUAL_MANAGER_HASH \
      --module VERIFIED_COMPONENT_SUBSDK9 \
      --expected-module-sha256 ACTUAL_MODULE_HASH \
      --output NEW_COMPONENT_DIRECTORY

The resulting data under component_data and the NSO profile are not an
installable or GAME_TESTED mod. The exact Switch stock v1.70 common.cpk
and original merged PC manager517 were NOT authenticated this turn.
The user's Library metadata cannot establish byte identity; local Python/
container execution was unavailable. The GitHub repository's inspected tree
contains no packaged .cpk, .xfbin, .zip, .nsc or .unse assets. CI runs only
synthetic CPK fixtures and exact native main module slices, not actual CRI IO.

The native CpkBindHook in overlay/source/program/nsc_cpk_bridge.cpp calls the
original binder, then conditionally registers extra CPKs based on returned
status and nonzero bind ID, and explicitly logs async_complete=unverified.
No native async completion, unbind, priority winner or actor/resource lifetime
was established and no new game hook was installed in this change.

Still missing: authenticated stock/raw517 evidence, native lifecycle/priority
proof, compressed PRM repacking, complete API operations, 53 factory unknowns,
nine parameter families, actual Uzuy gameplay. Stage remains
IMPLEMENTATION_INCOMPLETE; full_moddingapi=false,
ready_for_gameplay_test=false, emulator_tested=false.

## 2026-11-05 — Pinned ARM64 CPK/file-load direct-edge census

Commit 3b9f3f7618f3a48d10f789c9284ca59ccd629233 added
tools/portlib/native_cpk_graph.py, tools/audit_native_cpk_graph.py,
tests/test_native_cpk_graph.py and a CI step. It scans only the verified
R180 Switch 1.70 main NSO (SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9).
No unpinned input, decompilation heuristics, or new runtime hooks are used.
Read-only native B/BL immediate decoding finds 493563 candidate direct
branch instructions and records incoming direct-edge candidates to ten
anchors, plus outbound edges inside bounded 0x100-byte windows.

A follow-up test-log update at e314f9c2157bb84ae16c1aa6394bb7b7c4c6e663
exposes per-anchor counts. Actions 41963998226 and 41964408868 are both
completed/success. Observed inbound counts from log41964408868:
- CpkBind wrapper 0x473190: 12
- CPK manager bind 0x115E80C: 2
- CPK path adapter 0x115FBB8: 2
- CPK priority wrapper 0x115F2BC: 2
- CPK vector insert 0x115E8E0: 2
- Fileload request 0x1206B4C: 4
- Fileload create 0x1206C9C: 2
- Fileload status 0x1207EFC: 7
- Fileload process 0x106F404: 0 *direct* B/BL callers found
- File-open request 0x1170FB0: 1

Specific static edges in the verified image: 0x4731F8 BL→0x115FBB8,
0x115FBC0 B→0x115E80C, 0x1206B9C BL→0x1206C9C, and
0x116F47C BL→0x1170FB0. These are static machine-word branch edges,
not proof that functions execute or that the bounded windows contain full
function bodies. The zero direct callers of 0x106F404 does not imply
inactivity: indirect branches, vtables, callbacks and dynamic dispatch
were not resolved. CRI async completion, unbind, archive winner/precedence,
error paths and game resources remain UNKNOWN.

The next native step is cross-referencing indirect dispatch and lifecycle
handlers, then testing verified exact entrypoint/ABI failure paths in ARM64.
Do not patch an alleged async completion offset without disassembly proof.
See reports/port_foundation/native_cpk_call_edges_summary.json and download
Actions artifacts for full read-only edge lists.

Stock Switch common.cpk/romfs.zip Library filenames remain unverified byte
sources because the local container could not inspect them. No user game
archive was committed. Original merged PC manager517 also remains absent.
Full API, gameplay readiness and emulator tested flags remain FALSE.

## 2026-11-05 — Pinned indirect references and authentic PC parameter templates

Starting HEAD aef7e2491c4515a22edf5c0ef7f3c0cb47c5a239. Commit 100bdea09ef39db558d449146b5a313f809882ff introduced a read-only exact-main indirect-reference census. Initial Actions 41968568148 failed because ordinary repeated NSO dynamic tags were incorrectly rejected. Commit be99b93e9b323944afd32a8dd75fd8c1cc9e4083 fixed this: only conflicting RELA-related dynamic tags 7/8/9 are rejected; Action 41968889996 PASS. This explicit failure and fix are preserved as evidence, not hidden.

Commit 45f52ddb8832cf9a7433bb9c9bd79dcb6e64d389 printed actual per-anchor results, Action 41969481009 PASS. The pinned NSO contained 288312 relocation records. None of the ten exact function offsets had direct RELATIVE relocations, ADR references, adjacent ADRP+ADD materializations, or immediate loads from matched relocation slots. THIS IS A BOUNDED NEGATIVE FINDING ONLY; code pointers may target neighboring entrypoints or be constructed through different instructions; vtable/indirect invocation is unresolved. It does not prove the existence/absence of CPK async callbacks, priority winner, teardown/unbind or gameplay.

Two source-grounded PC payload readers now exist: tools/portlib/pc_param_rows.py and tools/audit_pc_parameter_rows.py. Upstream TheLeonX/UltimateStormAPI commit a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc uses raw 0x20-byte rows with 24-byte type field and a little-endian 16-bit character ID at +0x18 for SusanooCondParam and PartnerSlotParam. Remainder +0x1A..+0x1F remains opaque. Unknown selectors and duplicate character IDs fail closed, rather than using unproven Switch mappings. PC source association mapping is informational; the Switch native factory ABI remains unverified.

Commit fc24971ab3d635d9061b132842607d46ae2551a2 added exact public PC source fixtures, not private game assets: TheLeonX/NSC-ModManager commit 276116ebf5ba398a867793cb02ee6c33c0927645, Git blobs d983860d4bbaa58440ea1b3ba2b6e6e33fa48b17 (susanooCondParam 160 bytes / five records) and 8155d1e0a76add995051b45fe68d27f19cca49dc (partnerSlotParam 256 bytes / eight records). Git blob SHAs matched byte-identically across both repositories. Action 41969845880 PASS, SHA256 a0b1dabfa72634c71e601c1fb9cc938c9fb00820591e44972771aeee6c3aed7c (Susanoo) and f7190ee92bbcca9e157ecfc7aa497a699e32b858bb865e9012e9df40e5103055 (Partner). Ten invalid format/hash tests rejected. Fixtures are raw PC payloads despite .xfbin upstream names; they are NOT NUCC XFBINs or Switch stock data.

TheLeoNX public manager baseline NSC conditionprmManager.xfbin is 57344 bytes (512*112), NOT an original 517-record merged manager. The true merged PC manager517 and independently authenticated unmodified Switch 1.70 raw176 stock are still missing. Library common.cpk and romfs.zip remain inaccessible to local executable analysis due tool failures, and were not uploaded to GitHub. Seven parameter-family readers remain pending, two have only PC raw32 payload parsers, and two earlier families are partially covered. Full runtime integration, compressed PRMs, MovesetPlus, 53 factory unknowns and Uzuy gameplay remain unfinished.

All release flags remain false: full_moddingapi, ready_for_gameplay_test, emulator_tested. See reports/port_foundation/native_cpk_indirect_refs_summary.json and reports/port_foundation/pc_param_rows.json for narrow evidence.

## 2026-11-05 — PC stream readers and executable-target relocation tables

Verified from HEAD 2c79c9f409ac92a99f19c578af3e4da437ec46fe.
Commit 4702118dfaf574f252f79b4b6c19ded57fda831a (CI 41972748025 SUCCESS)
adds PC OugiAwakeningParam/GudoBallParam uint32 ID-array readers and CharRelationParam
count-prefixed uint32 ID-array reader, based on pinned PC source at TheLeonX/UltimateStormAPI
a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc. Exact source blobs from public
TheLeonX/NSC-ModManager 276116ebf5ba398a867793cb02ee6c33c0927645 were
copied without modification and matched upstream Git SHA. Input SHA256 for Ougi
aafe5c9d06106459ae1b56891f2cae5751596c24db3cf15898160499b7c88509
(one 4-byte uint32), Gudo 7516b57455c49ab9508b6fc12bc644aae797d96b5ef8253e2f809f0319df467f
(two uint32), CharRelation 80edf5c8fcb60825fad9a2ff4c1c82864b6b5656ecb7775e5d4c77a3ca47ce2a
(30 variable-length records over 548 bytes). CI rejected nine synthetic malformed
or mismatched inputs. These are PC ModdingAPI raw payloads despite .xfbin extension;
NO native Switch loader or gameplay proof is implied.

The same commit added pinned native nearby-target census around CPK manager
(0x115E80C), adapter (0x115FBB8), file-open (0x1170FB0), fileload status
(0x1207EFC) and fileload_process (0x106F404). Exact main SHA256 is
2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9.
Around 0x106F404, the scan found 2 BL edges from outside the bounded
window, 5 local BL and 7 local B edges, plus BLR sites at 0x106ED9C and
0x106EDD0. RELATIVE relocation addends near this region include slots
0x212B5F0->0x106EDB8, 0x212B5F8->0x106EDC4,
0x212B600->0x106EDE0, 0x212B608->0x106EDE8.
These facts supersede the earlier narrow statement of zero references to
the exact 0x106F404 address; the original exact-address result remains valid.

Commit ef738a5eba5738f40d9f8ca2384912496210e148 (CI 41973202913 SUCCESS)
extends this analysis to adjacent eight-byte executable-target relocation
groups. Eight candidate groups were counted, and all four known exact
slot/addend pairs reproduced. Some groups contain 13 consecutive slots
with repeated code targets; ownership, vtable class, method ordinals,
calling ABI, async completion/unbind and runtime archive winner remain
UNVERIFIED. This does NOT justify installing hooks yet. The static graph
results are in the full CI artifact and summary JSON report.

User Library searches did not find a byte-verifiable original merged
PC conditionprmManager517 in this turn. Existing named common.cpk cannot
be authenticated as unmodified stock through metadata; programmatic local
container inspection failed. No actual stock-vs-candidate raw176 comparison
was made. No private stock CPK was committed to the public repository.

Five previously pending families now have PC-only reader validation
(SusanooCond, PartnerSlot, Ougi, Gudo, CharRelation). Four still have no
reader (pairSpSkill, bgmManager, specialInteraction, guardEffect). The five
PC readers are not wired to Switch; lifecycle, actor/resource ownership,
MovsetPlus, 53 factory placeholders and compressed PRMs remain incomplete.
full_moddingapi=false; ready_for_gameplay_test=false;
emulator_tested=false; GAMEPLAY_UNVERIFIED.

## 2026-11-05 — Four remaining PC readers, pinned ARM64 register disassembly correction

Starting GitHub HEAD 747e4c17725c5a53fad9d9d9afed255984ac7f9e verified against Actions 41973648462 SUCCESS.
Commit ef0bd858ef7d1f139ddce5672066957bae591866 (Actions 41976177875 SUCCESS)
adds `tools/portlib/pc_param_remaining.py`, CLI and 4 public exact-Git-blob fixtures.
Source format derives from pinned TheLeonX/UltimateStormAPI PC C++ at
a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc; raw samples from
TheLeonX/NSC-ModManager 276116ebf5ba398a867793cb02ee6c33c0927645.
PC raw reader record counts: pairSpSkillManager 55x0x18, BGM 1x0x68,
SpecialInteraction 4 variable records, GuardEffect 2x0xF8; exact public
input SHA256 and Git blob SHA verified in CI. 14 invalid cases rejected.
All nine PC raw parameter formats have source-grounded readers but are
NOT connected to native Switch game loader or actor lifecycle.

Commit 90be75437ecfc6a7e67a0a6d82eade3db8ee8131 (Actions 41976417627 SUCCESS)
adds 9 bounded Capstone AArch64 disassembly windows; verified exact
pinned v1.70 NSO main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9.
The historical `fileload_process 0x106F404` label was imprecise:
0x106F404 is an actual BL to 0xFFF6A0, NOT a verified function entry.
Two BLR instructions at 0x106ED9C and 0x106EDD0 are preceded by
loads from [X20] then [X8,#0x20] and [X0] then [X8,#0x10] respectively.

Commit 9dfbf05bfebbab38f93b1a66812e8c76c2aa7a36
(Actions 41977060825 SUCCESS) adds seven exact instruction-word register
witness assertions. A RELATIVE pointer 0x215C478 -> 0x106F394 reaches
code beginning SUB SP,SP,#0x40, but function identity and extent are NOT
verified. Runtime class/vtable ownership, correct native calling ABI, CRI
async completion, archive lookup priority, unbind/destructor and engine
resources all remain unknown. Do not install ABI-guess hooks.

Library `common.cpk` 363755660 bytes and `romfs.zip` 59806528 bytes
were materialized to runtime in this turn, but container and Python
binary execution both raised ClientError. No actual game CPK SHA256
or untouched-stock provenance established; no authentic manager517
found; no real stock/raw176 comparison performed. Do not conflate
materialization or file size with stock proof.

Storm Modding Lab immutable checkpoint ID e864bb82-5156-413c-9cdf-6d7177e0da61.
Full API remains INCOMPLETE; full_moddingapi=false,
ready_for_gameplay_test=false, emulator_tested=false. No new native
hooks/PC DLL emulation/gameplay package; no game playback tested.

## 2026-11-05 — Follow-up native CFG, real-input intake and nine-PC-family index

Verified branch HEAD before modification: 293f3a3f3a92c7551548e641d1b0e2823f32fe05,
GitHub Actions 41980021960 SUCCESS. Existing parser, compiler, Event236,
Sakura aura107, CPK overlap, direct and indirect scans were NOT rewritten.

Commit 1c40470550195e200e39c9537856736e69d5d191
(Actions 41986733558 SUCCESS) added bounded Capstone AArch64 static CFG
analysis for exact SHA-pinned original main
2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9.
Candidate 0x106F394: 147 syntactically reachable words, no inbound direct
B/BL, one pinned RELATIVE pointer at slot 0x215C478, four observed
return/termination addresses and the legacy 0x106F404 BL callsite reachable.
Candidate 0x106EDB8: 3 reachable words, 0 direct B/BL inbound,
RELA slot 0x212B5F0. Native file-open 0x1170FB0: 52 reachable words
and one direct B/BL inbound. These are bounded static candidates, not
vtable ownership, confirmed function boundaries or live CRI lifecycle.

Commit f441c5a54bd370b6e01ee263b8e76cac4805286b
(Actions 41987276792 SUCCESS) added `tools/audit_real_condition_intake.py`
for Android/Termux: byte-stream SHA256 real CPK and merged PC manager517,
reject 512 public baseline, optionally discover exactly one validated
517-row PC manager, then invoke existing `condition_archive_audit.inspect`
for original stock512 and candidate517 raw176 CPK entries. CI proved only
SYNTHETIC manager517/CPK pair with 7 malformed inputs rejected. It does
NOT prove the user Library common.cpk is untouched Switch stock or that a
genuine original merged manager517 has been located. The previously
materialized actual `common.cpk` remains byte-uninspected due container
and Python errors. No real original stock-vs-candidate raw176 comparison.

Commit 85e14efd4bf6269be148810a9175766351ec063a
(Actions 41987853686 SUCCESS) added SHA-validated union manifest of
all NINE public PC raw parameter families, invoking prior validated
readers rather than reimplementing them. Nine unresolved BGM sound/Guard
effect name candidates were enumerated, seven malformed source specs
rejected, deterministic index SHA256
7b3b07919a14356ca91bd5b0ec0bb6bef80178607d12d017d1c10143b07c03ca.
Manifest is PC ONLY. There are ZERO verified Switch reader/actor/factory
integrations, and no real user mod package was loaded as test input.

Native hook ABI, CRI async completion and resource/actor lifecycle,
archive precedence, unbind/teardown, complete MovesetPlus, 53 PC
factory placeholders, compressed PRM, SFX/audio/effect banks and
Uzuy gameplay are NOT verified. No gameplay patch/installation candidate
was produced. full_moddingapi=false, ready_for_gameplay_test=false,
emulator_tested=false. Storm Modding Lab checkpoint
80be5308-6dfa-44d8-91e9-71c92a4f00e2.

## 2026-11-05 — Corrected original FileLoad lifecycle hypothesis and guarded native status setter

Verified live GitHub HEAD a1bd96f348ef009b91869bf07b75fb93d1df6f10, already 7 commits ahead of last handoff; compared to b15178b3188a263350a14197900e63480bfb9635 and did not overwrite their new source. Prior Actions 41994096469 SUCCESS.

Seven preexisting commits b882d5a, e3171e7, 4f50223, 8de85f6, 5bd5859, be0d074, a1bd96f introduced: original CPK relocation data-slot use witnesses, exact PC literal resource-string vs CPK-TOC scanner on synthetic archives, correction of dormant bad FileLoad hook fingerprint, original 0x116F404 eight-word native function prologue, two native status5 callsites (0x116F520 and 0x116F5C0) to original setter 0x120661C, and execution of 32 original ARM64 setter scenarios with modeled external lock/unlock (terminal statuses 3 and 5 preserved). A lock mock does not prove real lock or CRI async. The CPK TOC scanner has not been run against authentic stock Switch archives.

New commit a256dcf5702525ea4ea71ec386f95060868b6fb3, Actions 41994695967 SUCCESS: tools/portlib/native_fileload_corridor_cfg.py performs SHA-pinned bounded AArch64 CFG at the corrected 0x116F404 prologue. It finds 166 syntactically reachable decoded instructions. Original BL at 0x116F47C -> 0x1170FB0 (file open) and BL at 0x116F520 / 0x116F5C0 -> 0x120661C (status5 helper) are all reachable. This is an important control-flow witness; it is NOT proof that failing file open causes status5, not a native status setter ABI proof for hooking, and not live CRI async, vtable ownership, unbind, priority or gameplay evidence.

Original stock common.cpk and merged PC manager517 provenance/actual SHA remain unauthenticated. Local container failed to read materialized CPK. Tools/audit_real_condition_intake.py only passed synthetic manager517 CPK pair. Nine PC families have format-validated readers and data-only manifest; zero native integrations. MovesetPlus, 53 factory placeholders, compressed PRM and SFX/audio/effect/model handling remain incomplete.

Release flags stay full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. No new hook or playable package.

## 2026-11-05 — Branch-sensitive FileOpen zero-return status5 research

Commit d6b357cc93fc14ef36d8aa0bf218f5ab84167de3 (Actions 41995755104 SUCCESS) adds an original SHA-pinned static branch-flow audit, directly after the corrected native FileLoad entry 0x116F404. FileOpen BL at 0x116F47C -> 0x1170FB0 is immediately followed by 0x116F480 CBZ W0,0x116F4D8. When that machine-code branch is taken, there is a syntactic original CFG path to the first status5 setter BL at 0x116F520 -> 0x120661C. The other status5 BL at 0x116F5C0 is NOT reachable from that zero branch under the bounded original CFG scan: its previous code checks the separate [X22,#0x1D8] field against 1 and branches over the setter if nonmatching. This is a meaningful distinction for the next API failure-path port.

A follow-up regression added exact expected true/false static reachability and explicit original-branch operand checks. This is not live FileOpen failure execution; all native async completion, source ownership, lock ABI, archive precedence, unbind and gameplay remain unverified. No hooks installed or resources modified. Original stock CPK and PC merged manager517 still not authenticated. Release flags remain false.

## 2026-11-05 — Native FileOpen zero branch argument/body witness (read-only)

Before writing code, live branch HEAD was verified at 96789dc835c0b2d4b552347b8658fff93be834c2 (11 commits ahead of requested b15178b). Its Actions 41996479494 completed SUCCESS. New code commit 696629615085cd0e586d00f9665d5f07d0e2b495, Actions 42000801083 completed SUCCESS, verified by jobs/steps and original job log. Tool tools/audit_native_fileload_result_flow.py and CI test tests/test_native_fileload_result_flow.py use exact SHA-pinned original v1.70 main, not edited main. Original W0==0 CBZ at 0x116F480 reaches first status5 BL 0x116F520 on a selected 19-instruction static path with no extra conditional decisions along that chosen path. Exact instructions stage W1=5 / X0=X20 and native helper performs X0->X21, W1->W20 and conditional status store at [X21,#0x68], with original guards on old status 3/5. The second +0x1D8-guarded status5 is not reachable from the zero-branch subgraph. Tests include synthetic conditional alternative/loop and corrupted-main SHA rejection. This is machine-code and static CFG evidence, not native FileOpen return semantics, real CRI error/lock execution, object ownership, safe hook ABI, async/unbind or gameplay. No CPK or game files changed. Genuine stock common.cpk, candidate CPK and true merged original PC manager517 still not independently authenticated. Nine PC-only family readers remain unbound to native Switch actors, 53 PC factory placeholders and complete MovesetPlus/SFX/effects/voice unresolved. All three release flags remain false.

## 2026-11-05 — Original FileOpen W0 return literals and FileLoad inbound object/context argument registers

Before any change HEAD was verified at cb9ee9f28cfccb2f1b38308e8d9a902cbc14aa46 with Actions 42001534476 SUCCESS. Code commits 943f4406f93888e507f2f849b7642edba950d07e (CI 42011552173 SUCCESS), 80dd4b420e1c2675421f9634152392464f33e756 (CI 42012372858 SUCCESS), e5e3e4deacfe5987710921628840e3a5609c5735 (CI 42013112991 SUCCESS), c32b1d2235e54b17c334081063132aa6df389424 (CI 42013833559 SUCCESS) added read-only SHA-pinned original ARM64 FileOpen return-W0 and FileLoad object-register origin analysis. 0x1170FB0 bounded original CFG has 52 reached instructions and two RETs, 0x1171068 from 0x1171058 MOV W0,#1, and 0x117107C from 0x117106C MOV W0,WZR (zero), with no other non-RET bounded CFG exit assuming calls return. This is machine-code literal evidence, NOT proof zero means CRI failure or actual runtime return conditions. Original FileLoad has 0x116F434 MOV X20,X2, 0x116F438 MOV X22,X1; first/second status setter X20 pointer and second +0x1D8 guard X22 pointer. X2/X1 unchanged since candidate entry until captures under bounded syntactic CFG with caller-saved clobbers modeled; native object class/ownership, API ABI and lifetime remain UNPROVEN. Tests include synthetic branch/loop/call clobber, source SHA mismatch rejection, original pinned values and register witnesses. No hooks, CPK edits, or new gameplay release. Genuine stock Switch common.cpk, candidate CPK and original merged PC manager517 still lack independently authenticated bytes, so raw176 actual compare not performed. Nine PC-only readers still not native wired, 53 selectors unresolved; MovesetPlus, compressed PRM, effects/model/SFX/JP voice remain open. All three release flags remain false.

## 2026-11-05 — Original FileOpen branch-predicate and opaque-call dependency census (read-only)

Before mutation verified actual HEAD 53eaf0af1a3b58b9460ea78ab3600620e9b5a953, five commits ahead of user checkpoint cb9ee9f. Did NOT repeat previous verified W0-return or X20/X22 register tracing. New code 9a9b6cd755e19598735df3c85a5bb637254b36c6 and GitHub Actions 42016068823 completed SUCCESS. Original job 127206799099 logs verified: FILEOPEN_BRANCH_DEPENDENCIES_STATIC_PASS 3 4 NOT_CRI_OR_GAMEPLAY. Added tools/portlib/native_fileopen_branch_dependencies.py, CLI tools/audit_native_fileopen_branch_dependencies.py, tests/test_native_fileopen_branch_dependencies.py and workflow step. The exact SHA-pinned original main 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 yielded 3 reachable conditional branch sites and 4 original external callsites in bounded native FileOpen CFG; each branch successor's syntactic possible RET endpoints and per-call postreturn endpoints are recorded to proof-work/native_fileopen_branch_dependencies.json. Independent synthetic branch/out-of-window and incorrect-main-SHA guard tests pass. This proves neither feasibility of all source paths nor CRI success/error return meaning, actual foreign call effects, native callbacks/locks/async/rollback, object ownership/destruction, CPK precedence or ABI safety. No native hook or installable release. Real original stock common.cpk, PC manager517 and candidate archive bytes still unauthenticated. Nine PC families/factory/MovesetPlus/audio/model remain unported to verified native runtime. All release flags remain false.

## 2026-11-05 — Original native FileOpen four callee windows, imported strncpy, public PC 512 identity and native X0+0x18 tail

Verified branch HEAD 107a5bd58e323c9aac6778c2db5862381cb658c4 before edits. Code 6c9b18db4bf80b07b4227dde6da8c58144b9df83 (Actions 42034757420 SUCCESS, job 127269892400) traced three exact original branch-register producers (CBZ X0 at 0x1171010 <- LDR [X23], CBZ X21 at 0x1171030 <- LDR [X23], B.LT at 0x1171048 <- CMP W0,#1) and all four reachable BL targets in SHA-pinned original 1.70 main. Two targets begin a direct RET stub; the others are a native thunk/tail wrapper and PLT. No native runtime or ABI claim.

Code ed3e32ac03b492000e8eb1cf410312b639200603 (Actions 42035689408 SUCCESS, job 127273107976), original job log: PLT_GOT_RELOCATION_PROOF [('R_AARCH64_JUMP_SLOT', 52, 'strncpy')]; original FileOpen call 0x1171028 -> 0x12F39A0 accesses GOT 0x2142080 and imports C-library strncpy, not a native CRI FileOpen symbol. Independently checked actual public NSC Mod Manager 2.1.2.1 commit 276116ebf5ba398a867793cb02ee6c33c0927645 PC conditionprmManager.xfbin (57,344 bytes = 512*112) Git blob 0e7133223f10eb2dbbb39d2166fdca9352e84c3e, SHA256 fae4c1e1a510f895a7b9b9acbf5b710e7472e9b47f3471087dd4b1c97b7b86c5. New read-only Termux CLI verifies both hashes; CI checked exact reconstructed baseline against Git object identity. This is authentic public PC 512 template only; no private merged manager517 or unmodified Switch CPK authenticated.

Code 51639ef9bba9a64a45f26abc0b58d13b79b20e65 (Actions 42036653763 SUCCESS, 57 steps, raw job log job 127276447046): FileOpen 0x117103C BL to 0x115FC2C, machine ADD X0,X0,#0x18 then B to 0x115EBD8; FileOpen checks return W0 via CMP W0,#1 and B.LT 0x117106C. Native target 0x115EBD8 bounded CFG reached 53 ARM64 instruction words, one observed local RET at 0x115ECA8, eight BL callsites 0x115EC18, 0x115EC28, 0x115EC48, 0x115EC68, 0x115EC84, 0x115EC88, 0x115EC90, 0x115EC94. No exits in this chosen bounded scan assuming each called routine returns; no dynamic CRI/failure/lock/callback, object lifetime, unbind/destructor, archive priority, safe hook ABI or Uzuy gameplay proven. Full port still incomplete. Three release flags false.

## 2026-11-05 — Eight genuine native FileOpen tail BL targets and sourced Android PC mod ZIP intake

Initial eight-native-callee code 93153c6 CI 42040639506 FAILED (_decode_window return tuple unpacked backward), corrected code 3ad8b12 CI 42041112374 SUCCESS with original job 127291860119 logs read. Eight original callsites map exactly: 0x115EC18->0x115ECAC; 0x115EC28->0x1160290; 0x115EC48->0x10ACBE0; 0x115EC68->0x12155A0; 0x115EC84->0x116B6E8; 0x115EC88->0x116D3C0; 0x115EC90->0x116B3F0; 0x115EC94->0x116D420. W0 reaching definitions at the local 0x115ECA8 RET are static only. All eight original BL instruction words and callee windows source SHA pinned, NOT safe hook lifecycles.

Additional code 3e78cc5 CI 42042384779 FAILED because an out-of-window branch target was mistakenly passed to decoded CFG predecessors; 4df44e6 CI 42043283000 inherited the same failure. Corrected HEAD d7abbf28bcd3c3d4a36ec3fdb48d2de87c556818 CI 42043526861 COMPLETED SUCCESS, original job 127300266132 61 steps, log reviewed. Source writer witnesses: indirect BR X1 at 0x116B724 <- LDR X1,[X8,#0xC0] at 0x116B71C; indirect BR X2 at 0x116B430 <- LDR X2,[X8,#0x58] at 0x116B424. At first tail call 0x115EC18, input X0 comes from ADD X0,SP,#8 (0x115EC0C), X1 from MOV X1,X19 (0x115EC10). Second call 0x115EC28 uses X0=X20 (0x115EC20), X1=X19 (0x115EC24), X2=SP+8 (0x115EC1C). These are original bounded dataflow candidates, not class/vtable/ownership or CRI API semantics.

Latest PC NSC Mod Manager 2.1.2.1 C# source TheLeonX/NSC-ModManager commit 276116ebf5ba398a867793cb02ee6c33c0927645 ViewModel/TitleViewModel.cs Git blob f7ca7602d12cf9689a08fd6b7e55abc4dc8fd4ca shows InstallMod accepts .uns/.unse/.nsc/.ensc via System.IO.Compression.ZipFile.ExtractToDirectory; .nus4 has a distinct ExtractNus4 method. New Termux offline importer tools/stage_pc_nsc_mod.py and tools/portlib/pc_nsc_archive_stage.py stage source-verified original ZIP input bytes in a NEW directory without overwriting files and report SHA256 per member, preserving CPK/XFBIN/audio identifiers; rejects 12 malicious/wrong-input negative cases in CI including traversal, symlink, duplicate case, invalid SHA, .nus4, compressed bomb and preexisting destination. It is not a Switch CPK recompiler, loader, native API or gameplay proof. No authentic PC user-provided .nsc sample was executed in CI. No original merged manager517/true stock common.cpk/candidate authenticated, thus real raw176 audit not performed. Nine PC parameters and 53 factories, MovesetPlus, compressed PRM, resources/models/effects/SFX/Japanese voice incomplete. Release flags remain false.

## 2026-11-05 — CPK source-pinned multi-mod staging and native X8 indirect dispatch proof

Verified HEAD before any change 28a4a9ce09bdc5afc36cb71b8617234fc3dc9d1d; reviewed handoff, status, prior CI and workflows. New code commit 23aba1b0fa5375b37e718aaf89641296dd02308e, Actions 42049654252 COMPLETED SUCCESS, original job 127322007659 logs read (62 steps). New tools/portlib/pc_nsc_cpk_candidates.py and tools/assemble_pc_nsc_cpk_candidates.py add a real byte-copying offline multi-mod candidate assembly stage: require exact original main SHA256, original PC archive SHA256 and selected member bytes, verify stage manifests and selected CPK bytes match the original ZIP, inspect actual CPK TOC, reject all colliding casefold TOC names across all CPK candidates and optional SHA-pinned reference archives (do not guess CRI priority), generate CPK registration profile binary through existing runtime cpk_profile.encode() and round-trip decode, and place exact byte-copied CPKs under candidate_data_root/data/moddingapi/.... Test tests/test_pc_nsc_cpk_candidates.py passed 2 positive source-pinned synthetic CPK tests and 13 negative tests including TOC conflict, malicious stage changes, incorrect main/source SHA, duplicate runtime priority, wrong path/missing entry and existing source mismatch. No source/game/CPK bytes changed and NO Atmosphere/Uzuy installer produced. Original non-synthetic user CPKs were not tested and real Switch runtime priority/bind ABI unverified.

Native code commit 372cfa1a7a2bb256628c84032fa6a9804e2a3a76, Actions 42050734300 COMPLETED SUCCESS, original job 127325814383 log reviewed (63 steps). Source-pinned original main exact A64 sequences: 0x116B718 LDR X8,[X0] then 0x116B71C LDR X1,[X8,#0xC0] and 0x116B724 BR X1; second 0x116B41C LDR X8,[X0] then 0x116B424 LDR X2,[X8,#0x58] and 0x116B430 BR X2. These are genuine original loaded function-pointer dispatch patterns and bounded X8/X0 provenance candidates, NOT proof of actual object instance/class/vtable layout, ABI safe hooks, caller lifetimes, archive lookup order or CRI callback/locks/async/unbind/destructor. SHA mismatch rejection and standalone CLI parity passed. Prior aura107/Event236 tests were retained in same CI. The source compiler nine-PC families/53 factory placeholders/MovesetPlus/compressed PRM/model/effects/audio/SFX/JP voice remain native-incomplete. No original manager517/stock v1.70 common.cpk/candidate source provenance for actual raw176 audit. All three release flags remain false.

## 2026-11-05 — Nine PC raw format readers compiled into actual ARM64 module; source PC parity and ARM64 execution

Starting live branch HEAD verified as e4deb084ab670ebf3a937f0fca4df50b0ce07201; read handoff/checkpoint.json, PORT_STATUS.json, prior report, workflow, progress and overlay native code. Added stand-alone, no-heap raw source C++ API in overlay/source/program/nsc_pc_raw.hpp/.cpp. Versioned extern C API via nsc_pc_raw_get_api() contains nsc_pc_raw_validate and nsc_pc_raw_row_at, bound to nine PC formats: Susanoo/Partner raw 0x20; Ougi/Gudo uint32 ID; CharRelation variable count-prefixed arrays; PairSpSkill raw 0x18 (+ optional ONE terminal byte); BGM raw 0x68; SpecialInteraction variable count, main ID and triggers; GuardEffect raw 0xF8. Strict prevalidated byte size <=4 MiB, SHA256 required, buffer read-only, no PC game allocator, unknown semantics not invented, outputs only record offsets/widths and known raw numeric fields. runtime_core calls API presence on ARM64 and logs no engine consumers; no original main/file hook changed. Added host cross-language regression with 9 authentic public PC 2.1.2.1 fixtures already in tests/fixtures/pc_source (previous Git blob provenance proofs preserved) and standalone native AArch64 Unicorn execution test.

CI history accurate: 3fde9d9 Actions 42054426581 FAILED missing header/source in prepare_exlaunch.sh; ca5790e Actions 42054951462 FAILED host bootstrap unresolved native symbol; fixed via copied native files and AArch64-only runtime API use, commit 912ef38 Actions 42055285084 SUCCESS, 64 steps job 127341886598, host test NATIVE_PC_RAW_NINE_FAMILY_CPP_PASS 9 123 38 NO_GAMEPLAY. Found zero-record PairSpSkill one terminal byte mismatch with PC reader, fixed size>=0x18 and added negative; first ARM64 test 76a450b Actions 42056338732 FAILED due ELF symbol lookup substring collision, then exact symbol fixed in code 9af5c5357e11e944e82f14babe0c95fe120e778a Actions 42057187119 COMPLETED SUCCESS (65 steps, job 127348672877 raw log inspected). Original markers NATIVE_PC_RAW_NINE_FAMILY_CPP_PASS 9 123 39 NO_GAMEPLAY and NATIVE_ARM64_PC_RAW_NINE_FAMILY_PASS 9 30 19 NOT_A_GAMEPLAY_RELEASE. All nine PC formats now have callable native reader, but no real game-file discovery/CRI ownership, no actual Switch consumer patches, no MovesetPlus factory/asset/audio/voice gameplay proof, no Uzuy test. Original main SHA guard, Sakura aura107 and Event236 native marker regressions still present, no new original game patches. Release flags remain false.

## 2026-11-05 — Source-verified PC ZIP data to real AArch64 nine-family packed reader

LIVE HEAD verified at start c3c703e3a762ebe7502c760514916c001b196de3. Added tools/portlib/pc_nsc_param_pack.py, tools/assemble_pc_nsc_param_pack.py, overlay/source/program/nsc_pc_pack.cpp/.hpp and copied into exlaunch; C++ API nsc_pc_pack_get_api() (version=1, 9 families), nsc_pc_pack_validate() and nsc_pc_pack_row_at(). A binary NSC_PC_PACK_V1 header + nine canonical directory rows contains SHA256 for full pack and each authentic original PC raw source, no heap/no owned pointers; reader re-validates original 9-family raw semantic layouts, count, padding, offsets, missing families and exact source hashes. Builder requires source-verified PC ZIP, staged manifest and staged bytes, cross-checks original ZIP selected bytes, uses Python family readers with explicit family mapping, refuses cross-mod same-family precedence guessing, and outputs atomic non-installable pc_native_sources.pack + manifest.json. Supports raw-format payloads even when named .xfbin, never assumes NUCC. No game engine hooks, new slots, effect/model/audio runtime or CPK ordering introduced.

Initial code 8fb8a1f1cbc3e04de73d07d45fe93fb81dcbe542 CI42064991061 SUCCESS but pre-regression. Added tests in de15cec CI42065320767 FAILED: original CLI parity could not validate deliberately forged manifest (test cleanup). Test fixed in dae9998e CI42065447433, native AArch64 test FAILED because unreferenced pack API symbols were removed from binary. Added AArch64 runtime API presence log (without game hooks) in 4ecbeeaec573eaf9eddad42b0d50c07d7a297ba4. GitHub Actions 42065894664 COMPLETED SUCCESS, all 67 steps, raw job 127379739873 checked. Original job markers: PC_NSC_NATIVE_PACK_HOST_PASS 24 26 NO_GAMEPLAY, PC_NSC_NATIVE_PACK_AARCH64_PASS 22 12 NOT_NATIVE_ENGINE_OR_UZUY; RELEASE_FLAGS_FALSE_STATIC_CI_GUARD_PASS 26 NO_UZUY_PROOF. Host 24 positive and 26 negative, ARM64 Unicorn 22 positive and 12 negative. Upstream family template bytes are authentic pinned PC source fixtures wrapped in a SYNTHETIC .nsc ZIP for test; not a real user mod, and not actual Switch game engine consumer ABI. Real PC merged manager517, genuine stock v1.70 common.cpk and mod candidate CPK provenance unavailable, so actual raw176 audit not done. Full API release flags remain all false; original v1.70 main, Sakura aura107 and Event236 invariants not modified by this work.


## 2026-11-06 — Offline staging lease full-arena overlap guard (CI pending)

Fix NSCPcPackLease::bind to reject source intersection with the entire destination storage_size, not only copied source_size. Reject pointer-end overflow using full destination capacity. Regression covers source inside unused arena tail and adjacent non-overlap. No engine hook or gameplay proof; all release flags false. Await full GitHub Actions logs before PASS.

## 2026-11-06 — Staging lease CI harness failure diagnosed and repaired (pending new CI)

Original GitHub Actions run 42143523682 completed FAILURE, job 127649363979 original logs inspected: generated lease_test.cpp used literal backslash-n between #include directives; compiler -Werror rejected extra tokens. Also corrected stale expected PASS marker from 15 to 17 and added explicit source-inside-unused-arena-tail rejection regression. No original main changes or game hook. Pending new CI; no PASS claim; release flags false.


## Offline lease handle ownership (CI pending)

2026-11-06: Actions 42149995458 for c220690b COMPLETED SUCCESS, job 127670617607 original log inspected (68 successful steps, PC_PACK_STAGING_LEASE_PASS 17 NO_ENGINE_ABI). New change: delete copy/move on NSCPcPackLease; four compile-time regressions guard against aliasing caller-owned arena. Await CI for this new commit. No engine hook or gameplay proof.
\n## 2026-11-06 — Offline native row copy boundary (pending CI)\n\nPrior c05e2fb Actions 42162289717 COMPLETED SUCCESS, original job 127710548290 log inspected: lease 21 and release guard 26. Added NSCPcPackLease::copy_row to copy validated raw source row bytes into disjoint caller-owned output, rejecting invalid family, insufficient output, arena alias and bounds. Four host assertions added. No engine consumer ABI or gameplay proof; release flags false. Pending CI.\n

## Offline PC pack row copy integrity regression (CI pending)

2026-11-06: Added byte-exact offline copy_row regression (family-relative source offset), sentinel preservation, and fail-closed destination/length integrity checks; NO engine consumer ABI or Uzuy proof. Await GitHub Actions COMPLETED SUCCESS and original job logs before PASS.


## 2026-11-06 — Offline copy_row length-output alias safety (pending CI)

Verified prior HEAD 1029358a Actions 42181003271 COMPLETED SUCCESS, job 127770356486 original logs checked, staging lease 33 assertions PASS. New guard rejects `copied` length pointer overlapping staging arena or consumer output buffer, before any writes; host regressions assert no mutation on rejection. No engine ABI or gameplay claims. CI for this new change pending; all release flags false.

## 2026-11-06 — CI harness marker correction for copy_row metadata alias guard (pending CI)

GitHub Actions 42202487601 for f95de8be completed FAILURE; original job 127840924176 logs inspected. Native test printed 37 while Python harness asserted 33; failure was an AssertionError at tests/test_pc_pack_staging_lease.py:113, not evidence of a native gameplay failure. Updated harness to expect 37 while retaining the metadata alias regression. Await new CI and original logs; no engine ABI, Uzuy, or release claim. All release flags false.


## 2026-11-06 — Offline copy_row lease self-metadata alias guard (pending CI)

2026-11-06: CI 42209580169 for 5d771838 COMPLETED SUCCESS, original job 127864601452 logs inspected: PC_PACK_STAGING_LEASE_PASS 37 NO_ENGINE_ABI; release guard 26. New offline copy_row metadata self-alias rejection (lease capacity/length) with fail-closed regression; pending CI for this commit. NO engine ABI or Uzuy proof.


## 2026-11-06 — Offline bind lease-self storage overlap rejection (pending CI)

Prior 0f1a4077f8d743c5750da4b0d1db70cbf9e0feca Actions 42224723618 COMPLETED SUCCESS, original job 127915210617 log inspected: PC_PACK_STAGING_LEASE_PASS 41 NO_ENGINE_ABI, release guard 26. Added bind() reject-before-copy for destination arena overlapping lease control fields (full and partial), with regression and source/state integrity checks. New CI pending. No engine ABI or Uzuy proof; release flags false.

- 2026-11-06: Actions 42234005102 for ac115effca12c1f61f18181fc57e5b19388fdb70 COMPLETED SUCCESS; original job 127946790864 log inspected, PC_PACK_STAGING_LEASE_PASS 45 NO_ENGINE_ABI and RELEASE_FLAGS_FALSE_STATIC_CI_GUARD_PASS 26 NO_UZUY_PROOF. Added offline row() metadata alias rejection for arena/lease object with regression; new commit pending CI. No engine ABI or Uzuy proof.


## Offline staging lease guard (CI pending)

`copy_row` now rejects destination spans overlapping the lease control object, including partial overlap, before copying payload. Regression verifies rejected writes preserve lease state and output. This is an offline consumer-owned buffer safety improvement only; it does not establish native engine ABI, lifecycle, CRI callbacks, archive precedence, or Uzuy gameplay.


## 2026-11-07 — Native pack metadata-output alias rejection (pending CI)

2026-11-07: Offline native PC pack metadata-output alias protection: validate() and row_at() reject output structs overlapping caller-owned pack, including partial end overlap. Four host regression cases preserve original bytes. No game consumer ABI or Uzuy proof; pending CI. All release flags false.

## 2026-11-07 PC native pack host CI harness repair

Actions 42278736419 for 42d064bde2509899950146f83da08518022715b8 FAILED. Original job 128101803373 log showed `UnboundLocalError` at test_pc_native_pack.py:121: four newly added negative metadata-output alias tests incremented `negatives` before it was initialized. Counter initialization moved before these cases, preserving all four regression assertions and the other negative cases. Fix awaits new CI; this does not establish native game consumer ABI or gameplay.

2026-11-07: Offline PC pack staging lease now rejects source pointers overlapping the lease control object before invoking the pack validator, including partial overlap. Added two fail-closed host regressions (expected lease marker 55). Code bffe2fde7a4987fb125eb55583f0b7ed4206b590; CI PENDING, no original engine consumer ABI or Uzuy proof. Original main, Sakura aura107 and Event236 untouched; release flags remain false.
\n\n## Multi-mod PC source-path ownership guard (pending CI)\n\nThe nine-family offline pack intake now rejects exact or casefold-colliding PC source paths even when mapped to different parameter families or mods. Five isolated regression cases cover disjoint ownership, cross-mod exact/casefold conflicts, intra-mod duplicate paths and existing family conflicts. This does not establish native CRI archive precedence or game consumer ABI.\n
## 2026-11-08 — CRILAYLA full-output bound (pending CI)

Read-only decoder previously bounded only the post-prefix decoded size; the returned buffer includes an additional 0x100 bytes. Enforce the caller's limit against the entire output, reject invalid undersized limits before allocation, and test exact boundary and negative cases. Synthetic only, no original game archive fixture, consumer ABI, repacker or Uzuy proof. Prior HEAD e4e08cc; new commit CI pending; all release flags remain false.

2026-11-08 — SOURCE-PINNED CPK PAYLOAD EVIDENCE (PENDING CI)
Upstream evidence reviewed: TheLeonX/NSC-ModManager/releases/tag/2.1.2.1 and TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1 (2026-08-30, both PC/Steam-specific, new Switch Projectiles Target MovesetPlus); kamikat/cpktools/cpk/crilayla.py for CRILAYLA 0x100 output prefix and reverse-bitstream format. The original Switch v1.70 main's SHA256 remains 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. No inference of Switch native consumer ABI is made from PC features.
Implemented: tools/inspect_cpk_payloads.py; SHA256 pin to actual input CPK bytes; explicit TOC path selections, aggregate decoded-byte cap, output generated only after all CPK entries pass validation and decoding; fixed numbered output filenames; immutable source; deterministic payload SHA256 provenance manifest with engine/runtime flags false. Added tests/test_cpk_source_evidence.py verifying exact recovered bytes, corrupt streams, wrong SHA, ambiguous paths, limits, existing destination and CLI behavior; CI step included. Synthetic fixture only. Running against real user stock CPK is a future independent evidence action, not claimed as done. No CPK write/repack/hook/new gameplay build. Do not mark PASS until current HEAD Actions COMPLETED SUCCESS and raw logs are inspected.

2026-11-08 — CPK SOURCE-PINNED TOC INVENTORY (PENDING CI)
Upstream source verification: NSC Mod Manager 2.1.2.1 commit 276116ebf5ba398a867793cb02ee6c33c0927645 (2026-08-30), NSC Toolbox commit 6f780cb6814f07e03c16b3e78d97dde4e4368983, REA main 03a3fcbcea87d6cb7485bffaee77d0338a0ab635 (2026-11-08), CRI cpktools reference eff288cf9c5b844269b215a920fe36e198aee4c9 (2015). Source formats do not prove Switch engine ABI. Prior HEAD 84725b77, Actions 42486846899 completed/success, raw job 128750472495 read; synthetic collector tests 4/4 passed. New --inventory read-only mode emits source-SHA-validated exact TOC paths, stored SHA256, offsets, sizes and CRILAYLA/identity/unknown classification, optionally suffix filtered. Added end-to-end CLI and negative tests. No game-original CPK present in repo for this feature, so evidence remains synthetic. No engine hook, CPK repack, runtime test or release flag changes.

## 2026-11-08 — Memory-mapped authenticated CPK intake (pending HEAD CI)
Parent: 5ea1885292ef70bfa0aeff34bcb016ea6e3c07ea. Primary source refs checked: NSC ModManager main 276116ebf5ba398a867793cb02ee6c33c0927645 (release 2.1.2.1), NSC Toolbox main 6f780cb6814f07e03c16b3e78d97dde4e4368983 (release 2.1.2.1), REA main c5ed046d6e7000b27a12c01a1444f28cc1651c4a, CRI CPK reference kamikat/cpktools eff288cf9c5b844269b215a920fe36e198aee4c9. The Switch original main is already pinned at 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; no consumer ABI is inferred.
The previous Android evidence intake read the entire source CPK into a Python bytes object (common.cpk v1.70 is ~364MB), causing avoidable whole-archive memory allocation before TOC scanning. New read-only mmap backed by a streamed SHA256 hash removes the whole-archive bytes allocation in both --inventory and --entry paths. Selected decoded payloads remain caller-owned bounded bytes and archive metadata is parsed unchanged. The source is never opened for writing. Synthetic 4MiB padded CPK regression mocks Path.read_bytes to raise and proves both inventory and two payload extractions still succeed, exact SHA/bytes preserved. This is a memory-efficiency enabling change for original large CPK intake, NOT authentic game-CPK verification, native consumer proof, or Uzuy gameplay. Await CI HEAD completed/success and authentic raw log.

2026-11-08 — CPK BATCH INTAKE ONE-TOC-PARSE (PENDING CI)
Primary sources rechecked: NSC Mod Manager and NSC Toolbox latest releases 2.1.2.1 (2026-08-30), REA main 08637b0c24b98ac9b32b925f1237aff57cabe601, kamikat/cpktools eff288cf9c5b844269b215a920fe36e198aee4c9. Parent 59325a90f5f069c91b440391c5fe1d1896093e4b, prior CI run 42494676424 job 128774317728 completed success; raw log inspected. Existing CPK collector reparsed the whole @UTF TOC for every selected entry, even though capture had already validated the index. Now pass the index to read_payload, validating per-entry bounds and decoded size, so batch intake parses TOC once. New synthetic tests assert exact bytes for both encodings, single parse, truncated bounds and size limit rejection. No game-original CPK proof, native consumer ABI, hook, or Uzuy. Preserve pinned original main SHA and all false release flags. New commit CI pending.

2026-11-09 — SHA-pinned static cross-CPK collision comparison (PENDING CI)
Source context: TheLeonX NSC-ModManager/NSC-Toolbox releases 2.1.2.1 (2026-08-30), REA main 559083be29bd8502a7feefcbe981380b2bbf4cd9, kamikat/cpktools eff288cf9c5b844269b215a920fe36e198aee4c9, and existing original-main SHA-pinned native FileOpen graph. The original game main is not changed. Implemented tools/compare_cpk_overlays.py to compare two to sixteen separately SHA-validated original CPK TOC inventories and report casefold path conflicts, stored hashes and divergent bytes, never claiming archive precedence or engine consumer binding. Synthetic CLI, positive, negative, and input-integrity regressions in tests/test_cpk_overlap_evidence.py. Parent 00e070e4b722f534434a66121f079ab52b4fb7bf; pending current-HEAD CI and authentic CPK input. This is a concrete conflict-evidence producer, not a gameplay patch. Release flags remain false.

2026-11-09 — CI regression repair: run 42504646489 job 128804531513 raw logs show two-archive compare positive case passed; negative test failed solely at unordered Path.iterdir() comparison. Fixed test to compare exact path sets, retaining all negative source pin and byte checks. Await new HEAD CI completed/success and raw log before PASS. This is harness correction, not engine ABI or gameplay evidence.

2026-11-09 — DECODED MULTI-CPK RESOURCE EQUIVALENCE (PENDING CI)
Parent 60ff29de50dcc383aaef62ab71e455559e84f328. Prior static overlay fix GitHub Actions 42510044675 COMPLETED SUCCESS, job 128820917454 original log inspected: 2/2 overlap tests PASS, release flags false. Primary sources: NSC ModManager/NSC Toolbox release 2.1.2.1 (2026-08-30); REA commit 25d3c7237ffeffc4f9e6ab87be2f83a643cf5cbb; kamikat/cpktools eff288cf9c5b844269b215a920fe36e198aee4c9. Implemented --compare-decoded in tools/compare_cpk_overlays.py: only intersecting TOC resources are decompressed under a shared 64MiB cap, and byte-hashed, allowing distinct compressed vs uncompressed storage to be classified as identical decoded resource, or genuinely different. Fail-closed on corrupt CRILAYLA, over-budget, invalid pins. Tests cover positive/negative/boundary/CLI/source integrity. This remains static synthetic evidence, not archive precedence or native consumer ABI; no original game archive or hook changed. Await HEAD CI and original job logs before PASS.

2026-11-09 — PC MOVESET FUNCTION INDEX CATALOG (PENDING CI)
Parent 819b398a32f85a62c453905cdf5911ce7413bb22; previous decoded CPK comparison run 42514577509 job 128834676559 COMPLETED SUCCESS, authentic log read: four CPK overlay tests PASS, release flags false. Research primary: TheLeonX/NSC-Toolbox 2.1.2.1 commit 6f780cb6814f07e03c16b3e78d97dde4e4368983 Properties/Program.cs Git blob 9d5f3e0dfa4ed51cf7924b503081a87b12146f64; NSC-ModManager 2.1.2.1 commit 276116ebf5ba398a867793cb02ee6c33c0927645; REA 25d3c7237ffeffc4f9e6ab87be2f83a643cf5cbb; cpktools eff288cf9c5b844269b215a920fe36e198aee4c9. New source-pinned catalog profiles/pc_moveset_function_names_2121.json records exact 289 NS4 and 300 NSC PC function index names; 289 index-identical, 11 NSC-only appended. tools/pc_moveset_functions.py enables strict JSON lookup and diff, rejects unsupported indices; tests/test_pc_moveset_function_names.py positive/negative/boundary/CLI. Release notes mention Switch Projectiles Target, but this pinned public ME_NSC_LIST does NOT name it or Start/Stop Deflect. These indices are explicitly UNRESOLVED, not guessed. This is a practical PC editor semantic catalog, NOT verified native Switch function IDs, PRM offsets, callback ABI, gameplay, or engine consumer. No game hook or original main modification. New HEAD CI pending.

2026-11-09 — PC MOVESETPLUS EDITOR EVENT PREFLIGHT (PENDING CI)
Parent f1b0c71373f5367e60196891c5bd549be5f1c1a1; CI 42520148080 job 128851655064 COMPLETED SUCCESS, original log inspected, four catalog tests PASS. Primary source NSC Toolbox 2.1.2.1 commit 6f780cb6814f07e03c16b3e78d97dde4e4368983 Properties/Program.cs blob 9d5f3e0dfa4ed51cf7924b503081a87b12146f64; FunctionIndexConverter.cs blob c16391bb0a83f2e27bb6ddfb8215717caf609095 confirms PC editor indexes ME_NSC_LIST using Int16. NSC ModManager/Toolbox releases 2.1.2.1 published 2026-08-30; REA main 25d3c7237ffeffc4f9e6ab87be2f83a643cf5cbb; cpktools master eff288cf9c5b844269b215a920fe36e198aee4c9. Added tools/pc_moveset_event_preflight.py to accept only explicitly authored PC event_id/function_index JSON manifest with exact SHA256 source, preserve verified NS4->NSC prefix indices and reject out-of-range, duplicate IDs, unsupported payload semantics. Reports names and index correspondence without binary rewrite or native Switch IDs. Tests positive/negative/boundary and CLI byte-integrity. This is PC editor workflow only; no original main mutation, no engine ABI or Uzuy. Await HEAD CI and log before PASS.

2026-11-09 — ORIGINAL MAIN NINE-FAMILY LITERAL/XREF CENSUS (PENDING CI)
Parent 67bc7af359636580ce75800c5c708fcff870110a. Original main source SHA 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. Reviewed TheLeonX NSC ModManager and Toolbox latest 2.1.2.1 (2026-08-30), cpktools eff288cf9c5b844269b215a920fe36e198aee4c9, and existing native_cpk_graph.py / native_conditions.py. Prior run 42524985034 job 128866493906 COMPLETED SUCCESS, original logs inspected: 3 PC MovesetPlus preflight tests PASS, release flags false. Added tools/portlib/native_pc_family_xrefs.py and CLI/test. CI executes on authentic SHA-pinned original main, checks exact nine PC family NUL-terminated literals across all 3 verified NSO segments, scans text for adjacent register-matched ADRP/ADD address formation, records exact segment hashes and candidate xrefs in machine-readable JSON. Test rejects mutated main, exercises positive/negative ARM64 instruction decoder and CLI output. This provides falsifiable real-main negative/positive evidence, NOT proof of actual consumer, indirect references, PC name equivalence, async ownership, native ABI, archive precedence or Uzuy. No runtime hooks, no modifications to main, release flags false. Await new HEAD CI and raw logs.

2026-11-10 candidate: read-only FileOpen BR def-use evidence now records Capstone ARM64 memory operand base/index/displacement, retaining unknown runtime values. Synthetic offset/base regression added; original pinned main execution pending HEAD CI. Does not establish memory contents, CFG merge, consumer ABI, lifecycle, archive precedence, or Uzuy.

2026-11-10 — PINNED FILEOPEN DIRECT CFG EDGE CENSUS (PENDING CI)
Parent 026fcc22153d314ebf85873ca3769491c17c6a7d. Original main pinned SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. Upstream NSC-ModManager and NSC-Toolbox releases 2.1.2.1 (2026-08-30) checked; PC release functions do not establish Switch engine ABI. Added tools/portlib/native_fileopen_cfg_edges.py: deterministic bounded AArch64 B/BL, B.cond, CBZ/CBNZ, TBZ/TBNZ edge enumeration and in-window merge census for both authentic BR sites. Unknown external predecessors and memory values explicitly unresolved. Synthetic branch diamond, negative/boundary, SHA mutation and original-byte CI regression added. Not complete CFG, not engine consumer, no runtime hook, no Uzuy; release flags remain false. Await new HEAD Actions success and authentic job logs.


## Entry instruction reaching definition correction (PENDING CI)
2026-11-10: Code 8d635163a6ab7f0c632db795293ffac1f73ca051 fixes bounded FileOpen reaching_writers missing the hypothetical window-entry instruction as a valid register writer. Two synthetic boundary cases added: entry MOV X1,X2 is reported; entry NOP leaves unknown. Original main is not changed; test/Actions for this HEAD pending; no ABI, ownership, archive precedence or Uzuy proof. Upstream source pins: ModManager 276116eb README 8e9560b2; Toolbox 6f780cb Program.cs 9d5f3e0; REA README 4e525c0; cpktools CRILAYLA b15f325. Next: obtain push-run job/log for this HEAD, repair failures, then prove real external predecessors/callee effects without runtime hooks. All release flags false.

2026-11-10 — PATH-SENSITIVE REGISTER-COPY ORIGIN TRACING (PENDING HEAD CI)
Parent 39739a567646a6619d461e79aae8c00eff838b2c. Research source checks: TheLeonX/NSC-ModManager and NSC-Toolbox release 2.1.2.1 (2026-08-30), morluto/rea@b2f3dc81fa503c2b9ff0d8625336ed2e74d1e829 and kamikat/cpktools@eff288cf9c5b844269b215a920fe36e198aee4c9. Last HEAD run 42798965337 job 129771266132 COMPLETED SUCCESS and actual job log inspected; CFG/FileOpen tests PASS. Implemented trace_copy_origins in tools/portlib/native_fileopen_cfg_edges.py: follows register-copy origins across reachable CFG predecessors and conditional merges rather than stopping at the final writer, keeps memory-load displacement/base but marks pointer value unknown, stops at opaque calls, preserves unknown external predecessors. Production original-main report includes per-register byte-grounded nodes; synthetic regression tests positive chained MOV, split paths, skipped/dead writer, BLR unknown call, LDR unknown runtime value, wrong register and unreachable authenticated return plus actual original-main byte hash/roundtrip. This is STATIC BOUNDED PROVENANCE, not a native PC parser consumer, ownership/async/callback/rollback proof, archive precedence or Uzuy gameplay. Original main, Sakura aura107, Event236 marked/unmarked unchanged and full_moddingapi/ready_for_gameplay_test/emulator_tested remain false. Await new HEAD completed/success plus authentic log before PASS.

2026-11-10 — COMPLETE ORIGINAL-TEXT DIRECT INBOUND FILEOPEN BRANCH CENSUS (PENDING HEAD CI)
Parent e24bde771b7ad2884ab450eb75f3d1519f3a5b51, prior real push Actions run 42829761016 job 129876430933 COMPLETED SUCCESS, raw log inspected (PINNED_FILEOPEN_CFG_EDGES_PASS 2 NO_ABI). Source pins: TheLeonX/NSC-ModManager 2.1.2.1 commit 276116ebf5ba398a867793cb02ee6c33c0927645 README blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709; NSC-Toolbox 2.1.2.1 commit 6f780cb6814f07e03c16b3e78d97dde4e4368983 Program.cs blob 9d5f3e0dfa4ed51cf7924b503081a87b12146f64; REA b2f3dc81fa503c2b9ff0d8625336ed2e74d1e829 README blob 4e525c0c458b7b5a0b5381d45c6f43a925ab45f5; cpktools eff288cf9c5b844269b215a920fe36e198aee4c9. New native_fileopen_external_edges.py scans complete original main SHA-pinned executable text for direct B/BL/B.cond/CBZ/CBNZ/TBZ/TBNZ inbound from OUTSIDE two 128-insn FileOpen indirect BR windows; emitted original byte-backed addresses/edges, out-of-text and indirect unknowns. New synthetic positive/negative/boundary/reverse-edge and original-main integrity tests, new workflow step. This can reveal true syntactic external direct references but cannot prove source executed, real caller ABI, ownership, lifecycle, archive precedence, engine resource consumption or Uzuy. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 marked/unmarked unchanged and three release flags false.

2026-11-10 — EXTERNAL FILEOPEN INBOUND TARGETS AND BOUNDED BR PATH CLASSIFICATION (PENDING NEW CI)
Parent 4603dbb13dbed1dc76cbeb76ce26ace06bd65c8a. Previous original-main whole-text scan GitHub Actions run 42833466211 job 129889325820 COMPLETED SUCCESS, authentic job log inspected: PINNED_FILEOPEN_EXTERNAL_EDGES_PASS 2 FULL_TEXT_NO_ABI; release flags guard PASS. Artifact 13772627999 proves original executable text SHA bbf6c62af46ce08c15a753c078accb2f638ad775e1f695256e452f9f197d7d21; 4,970,484 instruction words and 930,281 direct transfers. Bounded BR X1 window [0x116b524,0x116b724] has 16,672 SYNTACTIC external incoming direct branch words (16,669 BL); X2 [0x116b230,0x116b430] has 7,901 (7,894 BL). None directly targets either BR site. Most target a few apparent high-fanout callees inside those windows; this DOES NOT make calls feasible or prove they reach BR. Added grouped exact target counts and bounded local CFG reachability per unique destination to separate callers of other local functions from possible BR-chain predecessors. Synthetic tests cover 3 distinct targets, duplicate callsite aggregation, terminal return barrier, cycle, whole original main byte integrity and flags. PENDING HEAD CI. Source anchors: ModManager 2.1.2.1 commit 276116eb, Toolbox 2.1.2.1 commit 6f780cb, REA b2f3dc81, cpktools eff288cf9, original main pinned SHA 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. Preserve Sakura aura107, Event236 with/without 0x4E53 +0x2A, three false release flags, no native hook or Uzuy claims.


## Call-free FileOpen BR witness classification (PENDING CI)
2026-11-11: Call-free bounded BR witness classification added: shortest syntactic paths which do not traverse opaque BL/BLR, with positive, call-only negative, bypass, and authentic main byte replay regressions. This is NOT actual call feasibility, consumer ABI, ownership, archive precedence or Uzuy. Parent 91325517c4ff7b4eedfef0ce55bfdbf18a66c8fb; CI PENDING. Upstream ModManager release 2.1.2.1; Toolbox 6f780cb; REA b2f3dc81; cpktools eff288cf9. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 unchanged; three release flags false.

2026-11-11: non-call inbound BR candidate separation, code 1b8b9f317a8e281844e721398eecc2b057ec66f9; jump/conditional inbound distinguished from high-fanout BL; call-free local paths remain syntactic. Synthetic regressions and pinned original-main replay updated. CI PENDING; ABI/ownership/archive precedence/Uzuy UNPROVEN; all release flags false.

2026-11-11: Candidate read-only FileOpen call-free witness per-instruction Capstone register read/write and memory-operand effects, byte backed; CI PENDING. No ABI, memory ownership, callback or runtime inference. Prior HEAD ec69f316 Actions run 42922943327 job 130202079582 completed SUCCESS and authentic log inspected. Preserve pinned main and false release flags.

2026-11-11: Verified parent 13531c0 Actions push run 42965602532 job 130341975871 COMPLETED SUCCESS; authentic job log PINNED_FILEOPEN_EXTERNAL_EDGES_PASS 2 FULL_TEXT_NO_ABI and RELEASE_FLAGS_FALSE_STATIC_CI_GUARD_PASS 26. Code ea8dd5476d836d6401ee012d272d83b74178c861 adds read-only call-free BR register immediate-writer boundary, memory-load unknown, external-input unknown; synthetic and original pinned-main tests. New CI PENDING; no runtime ABI/ownership/precedence/Uzuy. Research: NSC-ModManager release 2.1.2.1 (2026-08-30), NSC-Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983, REA 0e88049d59124abfab0bf1bc57b5ee32d0430afb; cross-platform ABI not inferred. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 preserved; Sakura aura107/Event236 marked and unmarked unchanged; three release flags false.

2026-11-12: Authentic failed Actions 43019655654 job 130519359288: STR memory direction assertion. Fix ordinary STR/STUR/STP transfer stores, add negative-read regressions; no ABI claims. New CI pending.

2026-11-12: Parent 5e506b6 Actions 43077934240 job 130722597543 COMPLETED SUCCESS, authentic 187406-character job log inspected; FileOpen external edges PASS 2 and false flags guard PASS 26. New read-only correction separates loaded values from address-register origins, with negative address-to-value and positive copy-chain regressions. CI PENDING for new HEAD. Research pins: NSC-ModManager 276116eb README blob 8e9560b2; NSC-Toolbox 6f780cb Program.cs blob 9d5f3e0; REA 0e88049d README. No PC-to-Switch ABI assumption. Original main 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 untouched; Sakura aura107, Event236 both forms, all release flags false.


## Compressed PRM decoded Event236 feasibility (PENDING CI)
2026-11-12: Added read-only compressed CRILAYLA CPK PRM Event236 decoded-byte feasibility report (tools/portlib/compressed_prm_events.py) with synthetic compressed NUCC PRM positive, negative SHA/path/size/corruption/uncompressed tests. No compressed repacking, native consumer, runtime ABI, ownership, archive precedence, or Uzuy proof. Parent 2ee0a9b9f004310822203dfc8f92d2c63b56334f; CI PENDING. Original main pinned SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 untouched; Sakura aura107, Event236 both forms, three release flags false. Source anchors: NSC-ModManager/NSC-Toolbox 2.1.2.1 released 2026-08-30; REA b2f3dc81fa503c2b9ff0d8625336ed2e74d1e829; cpktools eff288cf9c5b844269b215a920fe36e198aee4c9. Next verify Actions HEAD success and authentic logs; obtain real compressed game PRM fixture and confirm decoded marker positions before any repacker.

2026-11-12 — OFFLINE COMPRESSED PRM DECODED CANDIDATE EXPORT (PENDING CI)
Parent e91040ec9978b493bc530d5489b80efdfbc9540b; code 424716d42c9391f5f752a6f33c712c1cd19831e2; test dc2a211b787ee47aef5f4387af086ba6b8e6c4ea. Added extract_candidate() returning validated decoded Event236 marker candidate and evidence, without modifying CPK. Positive byte offsets, digest, deterministic replay, negative SHA, absent path, size bound regression. Synthetic only; no compressed repacker or game ABI, archive precedence, ownership, runtime/Uzuy. CI pending, do not claim PASS. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 and release flags false unchanged. Research: ModManager 2.1.2.1 README blob 8e9560b2; Toolbox 2.1.2.1 README blob 657f1613; REA README blob 4e525c0c.

2026-11-12: Prior HEAD 48744a1 Actions push run 43161324058 job 130992957575 COMPLETED SUCCESS, authentic 189146-character log inspected; decoded CLI and false release flags covered. New offline batch decoded PRM candidate exporter stages SHA-pinned multi-member candidates before output, rejects duplicate/casefold paths and destinations, and rolls back created files on write failure. Synthetic-only tests; no native consumer ABI, CPK repacking or Uzuy. CI PENDING for new HEAD. Primary release NSC-ModManager 2.1.2.1 published 2026-08-30; NSC-Toolbox commit 6f780cb6814f07e03c16b3e78d97dde4e4368983; pinned original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 untouched. Preserve Sakura aura107, both Event236 variants and three false flags.

2026-11-12: Added deterministic offline literal-only CRILAYLA encoder and exact decode roundtrip/boundary/corruption regressions. New CI PENDING; synthetic bytes only, not a CPK repacker or native consumer. Parent 2d7c3b2057bceeb4186cc51bc7f8d379b9a825f7; prior run 43217216938 job 131179401384 SUCCESS authentic log read. Preserve pinned main SHA, Sakura aura107, Event236 variants and three false flags. Upstream NSC-ModManager release 2.1.2.1 (2026-08-30), NSC-Toolbox 6f780cb, REA b2f3dc81; cross-OS ABI not established.

2026-11-13 — COMPRESSED PRM BATCH DISK STAGING (PENDING CI)
Parent 4497049b202251f1b39b2f34061615c4a3dcc0cd; previous batch CI 43344883463 job 131621709606 SUCCESS with authentic log read; foundation CI 43344883497 job 131621709754 completed success (job status checked). Research pins: NSC-ModManager@276116eb README blob 8e9560b2; NSC-Toolbox@6f780cb README blob 657f1613; REA@b2f3dc81 README blob 4e525c0. PC tools do not establish Switch ABI. Disk-stage each validated candidate and publish via same-filesystem exclusive hard link with rollback; unlike prior implementation, do not retain all 128 packed candidates. Two new synthetic regressions cover stage failure cleanup and link publication cleanup; existing source integrity/rollback regressions preserved. Pending HEAD CI and original job logs; no authentic compressed PRM fixture, native consumer ABI, archive precedence, CPK repack or Uzuy proof. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 and Sakura aura107/Event236 marked/unmarked untouched; all release flags false.

2026-11-13: Compressed PRM batch source SHA256 and CPK TOC now validated once per archive before processing all members; internal validated-index path avoids repeated full archive hashing/parsing, while public extract_candidate retains its independent SHA verification. Synthetic tests added for one TOC parse and wrong SHA rejection before parsing/output. Parent 0a1b83b1e81389abffc37f4cd319a7ff7bdf9de7; code HEAD 0b0bb8b40f0c6f9ab1ddd016391cd9252f583dfe. PENDING CI and authentic job logs. Source anchors ModManager 276116eb README blob 8e9560b2, Toolbox 6f780cb README blob 657f1613, REA b2f3dc81 README blob 4e525c0c. No authentic PRM, engine ABI, archive precedence, Uzuy or gameplay proof; preserve original main SHA and all three release flags false.

2026-11-15: Source-bound offline compressed PRM candidate verifier added. Reopens SHA-pinned source CPK, validates original decoded Event236 provenance, compares every output's decompressed bytes to independently regenerated expected candidate, and rejects tampered compressed bytes even if report hashes are rewritten. Synthetic positive, mutation, provenance, symlink and duplicate-output regressions; no CPK writes or game consumer hooks. Original main pinned SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 unchanged. Upstream ModManager release 2.1.2.1 (2026-08-30), Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983; REA current unrelated desktop code, no Switch ABI proof. PENDING HEAD CI and original job log. full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false.

2026-11-15: Independent source-bound compressed candidate verifier commit 5f7985a9f5247ab7a030b77d0e5a5092832085bc; compressed workflow 43626046959 job 132541961625 completed SUCCESS, raw log inspected (30 synthetic tests). Foundation run 43626046905 pending; no original game PRM, runtime consumer or Uzuy proof. Three flags false.

2026-11-15 PENDING CI: New offline PC MovesetPlus multi-mod index composer merges 1..64 SHA-pinned editor manifests, rejects duplicate mod names and cross-mod event IDs, preserves source order and provenance. Three regression cases (positive mixed NS4/NSC, negative collision/hash/range, boundary count) added to dedicated workflow. No binary moveset, native Switch consumer ABI, game-authentic fixture, or Uzuy evidence. Parent 4a07a44a9c38166aad7e0317506b00ec86ee2894. Primary pins: NSC-ModManager tag 2.1.2.1 README Git blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709; NSC-Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983 README blob 657f161390c4abe8afe10cea11a2b9a28e6bf6b0; REA f3b697da5a698a5548afd3b19d044ec623bdda0b README blob 78b7064b8053b0076b4329013611881f395b6aba (not engine ABI). Pinned original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not modified; Sakura aura107, Event236 variants preserved; all three flags false. Next: verify HEAD CI job logs, then prioritize authentic native consumer ownership/lifecycle evidence.

2026-11-15: Added offline PC MovesetPlus per-mod removal from SHA-verified merged editor indices; retained mod byte provenance can be independently replayed from original source, negative tests cover forged evidence, missing/final mod and exclusive CLI outputs. Native Switch ABI/consumer and game-authentic bytes still unverified. Parent c5862b6adc54fb1372e02220c96297af45b41645; HEAD CI pending. Primary references: NSC-ModManager release 2.1.2.1; NSC-Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983; REA 2e1e6593f266b859d2f0fc858d51ed2f280b6849 is not Switch ABI. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 untouched; Sakura aura107, both Event236 variants and three false flags preserved.

2026-11-15: PC MovesetPlus removal CLI now requires original SHA-pinned PC source manifests in exact order, authenticates full pre-removal merge and independently replays retained sources post-removal before publication. Negative tests cover reordered, omitted, mutated and forged sources; offline editor index only, no binary or native ABI. Parent 65c0bbedda31523e2849a5e10a824a21d0730ad2. CI PENDING; original main pinned SHA unchanged, Sakura aura107/Event236 both variants unchanged; release flags false. Upstream primary README blob anchors ModManager 8e9560b2, Toolbox 657f1613, REA 78b7064b (REA not Switch ABI). Next inspect HEAD push workflow and raw job logs; obtain original main bytes for consumer ABI proof.

# PC MovesetPlus append-only editor manifest slice — 2026-11-17

Research: NSC-ModManager tag 2.1.2.1 commit 502c38d3ee832509f9ee3951b7d3339826538fec (release 2026-08-30, Switch Projectiles Target); NSC-Toolbox commit 6f780cb6814f07e03c16b3e78d97dde4e4368983 (PC editor index); REA commit d5a942177fad030d3caf0f8d39856c116e3e5cda (unrelated desktop tool, NOT Switch engine ABI). Pinned Switch main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; original game bytes not analyzed in this slice.

Capability: batch editor manifest transaction now accepts --add NAME PATH SHA256 alongside --remove and --replace. Old merged payload and source list are authenticated before any edits. New source manifests are SHA-authenticated through merge(); appended in declared order. Duplicate mod names, event collisions, invalid source hashes, 65-mod boundary and forged old proof fail closed. Source provenance remains independently replayable. This does NOT convert moveset binary, identify v2.1.2.1 new function numeric IDs, prove Switch consumer ABI or test Uzuy.

Tests: tests/test_patch_pc_moveset_nsc_mods.py positive add, combined remove/replace/add, provenance replay, duplicate names, event collision, SHA mutation, 64/65 mod boundary and forged old proof. Workflow: verify-pc-moveset-multimod.yml already runs that test. Status PENDING_CI until HEAD push-run completed/success and original job logs inspected. No runtime hooks. All three release flags false.

2026-11-17: PC MovesetPlus source-authenticated append transaction implemented at 5b482d578c193a137dc2729bd77b0191a1b4c821. HEAD push Actions: multi-mod 43995597662 job 133746734402 COMPLETED SUCCESS, raw log 9 patch tests PASS; compressed 43995597642 job 133746734613 COMPLETED SUCCESS; foundation 43995597649 job 133746734362 COMPLETED SUCCESS; original job logs read. Editor-index-only, no native ABI, game archive or Uzuy proof. Release flags remain false.

2026-11-17 PENDING_CI: commit 47bf6df1eda645679745b159716f525e21e1db35 (parent b288d3a7711870231a5b6ba62abebf3267b21f8d) adds source-authenticated selective PC editor manifest restoration (--name) preserving original numeric index and untouched neighboring files. Two synthetic positive/negative tests added. No local tests executed (GitHub DNS inaccessible in container); commit-scoped GitHub Actions connector returns PR-only empty list, so push CI run/job/log NOT verified. ModManager 2.1.2.1 README blob 8e9560b2, NSC-Toolbox 6f780cb README blob 657f1613, REA b2f3dc81 README blob 4e525c0c; none establishes Switch ABI. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 marked/unmarked unchanged. Native consumer/ownership/lifecycle/archive precedence and Uzuy unverified; all release flags false. NEXT obtain HEAD push-run via direct Actions REST and inspect raw job logs, fix failures before PASS.


2026-11-18: Offline CRILAYLA bounded-distance encoding slice. Parent c6625cb95730fd521d55a02499543f87c19551fe. Replace distance-3-only greedy selection with deterministic best-length search over distances 3..34, max match 1024; no game CPK writes. Positive periodic 5/7/13/31, random and long-run roundtrip, size reduction, exact deterministic replay. Independent local prototype passed 49 synthetic decode roundtrips; repository tests and HEAD Actions PENDING. Upstream anchors: NSC-ModManager 2.1.2.1 (release 2026-08-30, PC Switch Projectiles Target/Start-Stop Deflect; no Switch ABI); NSC-Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983 README blob 657f161390c4abe8afe10cea11a2b9a28e6bf6b0; REA 237b1ea5b39ea9fc5373aa08a9f54d25715c4873 README blob a01452f5e21b50d1b6233a1761e1536a22b1271d (not engine ABI). Original main pinned SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not changed. Synthetic only, no authentic PRM, native consumer ownership/lifecycle/archive precedence, or Uzuy. All three release flags false. NEXT: inspect HEAD foundation push-run and raw job logs; fix CI if necessary.

2026-11-18 VERIFIED OFFLINE SYNTHETIC: bounded-distance CRILAYLA encoder code 05e376d01731eaf60b83fc09108c97561ef6b14c; foundation run 44179052280 job 134378140592 COMPLETED SUCCESS, authentic raw job log read (5/5 encoder tests including periodic 5/7/13/31, random, deterministic replay, long run). Compressed run 44179052253 job 134378140460 SUCCESS, MovesetPlus run 44179052312 job 134378141078 SUCCESS; both raw logs read. Workflow step description updated only in this followup; new HEAD CI pending. Synthetic only, no authentic game PRM or engine consumer ABI/Uzuy; all release flags false.


# CRILAYLA long-period offline encoding — 2026-11-18

2026-11-18 PENDING_CI: offline CRILAYLA encoder expanded deterministic match search from distances 3..34 to 3..258 with four-byte candidate prefilter, plus periods 127/251 roundtrip, deterministic replay and compression-ratio regressions. Parent e4f132a6487066f970f965cc2505ce2b083f0912. Synthetic only; CI HEAD run/job/log not yet verified. Original main blob 8af900db0d7003255b4ddb3cbd1289cd5a15458e is tracked in repository (27,701,509 bytes), but SHA256 not independently checked in this session; do not infer native consumer ABI. Upstream NSC-ModManager release 2.1.2.1 published 2026-08-30; NSC-Toolbox HEAD 6f780cb6814f07e03c16b3e78d97dde4e4368983; REA HEAD c78e6e3aa54facde2d7610f203dd740e47611090; none proves Switch ABI. No runtime hooks; Sakura aura107/Event236 marked/unmarked untouched; three release flags false.

2026-11-18 VERIFIED OFFLINE SYNTHETIC: code 61403b49750938ff7710cc5b04bf38d0c2b29c39 extends CRILAYLA match distance to 258 with 4-byte prefilter; 6 encoder tests PASS incl 127/251 periodic payloads. Foundation push run 44189015312 job 134413108606 COMPLETED SUCCESS and authentic log read (6/6). MovesetPlus run 44189015390 job 134413110690 and compressed PRM run 44189015431 job 134413108835 COMPLETED SUCCESS; both authentic logs read. Synthetic/offline only; original game archive and native consumer ABI/lifecycle/Uzuy unverified. No hooks or release flags changed. This documentation followup HEAD CI is pending.

2026-11-18 FileLoad CFG path-witness slice: code cef593fa0d2369ca16623722e817c16f35c2696b parent 436807c8510cf430b0ffa8e46ff013ac4426de7c; rejects stack write/read pairs across exclusive branches and opaque calls; positive join and linear synthetic tests. Original main pinned SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. Prior HEAD foundation push run 44312970061 job 134831603454 COMPLETED SUCCESS and authentic log inspected; current code CI pending. No actual engine ABI, register value, ownership, lifecycle or Uzuy proof. All release flags false. Research: ModManager 2.1.2.1 2026-08-30; Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983; REA 23adfc610f277d87630375991da08d5efaafb4f4; none proves Switch ABI. NEXT inspect HEAD Foundation authentic logs, fix failures, then trace register provenance on CFG path witnesses.

2026-11-18 VERIFIED_CI_STATIC_ONLY: code cef593fa0d2369ca16623722e817c16f35c2696b (parent 436807c8510cf430b0ffa8e46ff013ac4426de7c) adds CFG state path witness to FileLoad stack candidate filtering, excluding mutually exclusive branches and opaque calls. Foundation push run 44334444138 job 134907198707 COMPLETED SUCCESS, authentic log read PINNED_FILELOAD_SP_CFG_PASS 166 10 NO_CONSUMER_ABI; MovesetPlus 44334444289 job 134907199676 SUCCESS log read; compressed PRM 44334444230 job 134907199446 SUCCESS log read. All refer to docs-parent aa323017506a99cb3fec518676cf810e4c73fa66. Still not register value/ownership/lifecycle/engine consumer ABI/Uzuy evidence; flags false. Next trace register provenance across witnessed CFG paths, no runtime hooks.


2026-11-18 PENDING_CI: FileLoad CFG candidate path witness now rejects an earlier stack writer when an intervening same-entry-SP-slot write occurs on the witness; different-slot stores remain allowed. Synthetic positive/negative regressions added. This is conservative static possible-path evidence only, not register provenance, same-value proof, consumer ABI or ownership. Research pins NSC-ModManager 2.1.2.1 README blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709 (Steam only), NSC-Toolbox 6f780cb README blob 657f161390c4abe8afe10cea11a2b9a28e6bf6b0, REA main README blob 4ccd45edee2a6d3b7229f591123954f2d1df1a86 (not Switch ABI). Parent 1df62942b111f459db4283549e6ca737d10db44d; Actions HEAD log pending. Preserve original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9, Sakura aura107, Event236 marked/unmarked; all three release flags false. NEXT verify HEAD Foundation original job log; then trace path-sensitive register values and pointer ownership, no runtime hook.

2026-11-19 PENDING_CI: FileLoad CFG path witness now rejects overlapping partial-width writes, not only identical start offsets; single/pair recognized ARM64 transfer widths are byte ranges, unknown width fails closed. Added synthetic STR W partial-overwrite negative and adjacent-write positive tests. Source e629afe31fccb8230d5111775cd1614a4396ffbc; tests dd7632afde07a6952765128ffefeeef6fb50d4da; parent 477ac57ea4e420a54833d0ab8a34d078eef5bc65. No local Capstone; Actions HEAD raw logs unverified, NOT PASS. Upstream ModManager 2.1.2.1 README blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709; Toolbox 6f780cb README 657f161390c4abe8afe10cea11a2b9a28e6bf6b0; REA main README 4ccd45edee2a6d3b7229f591123954f2d1df1a86; none proves Switch ABI. Pinned main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 unchanged. Sakura aura107, Event236 marked/unmarked untouched. No consumer ownership/ABI or Uzuy; three release flags false. NEXT inspect HEAD Foundation raw job log; fix failures; then register provenance.

2026-11-19 PENDING_CI STATIC: FileLoad CFG witness now fails closed on intervening non-SP-base memory stores, which can alias the tracked stack slot until base-register provenance is established. Synthetic regressions test unknown-base STR rejection and unrelated LDR acceptance. Code 606396709b4a1a78c8a1b07d2ac62823c2415a01 parent a5cb045ec0ed6f700f8df20037be137a0944aeb1. Local Capstone unavailable; commit Actions job/log unverified. No ABI/ownership/lifecycle/archive precedence/Uzuy proof, no hooks. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 and Sakura aura107/Event236 both forms untouched; all release flags false.

2026-11-19: Recovered authentic Foundation push-run 44390924739 job 135108023312 for parent ee1b77baab796b63e2164b5cb39d226f29de59c0: COMPLETED FAILURE, raw log proves Python SyntaxError at tools/portlib/native_fileload_sp_cfg.py line 130 (missing closing parenthesis). Fixed one-line syntax in code 8ff037581cd49ebfe50be905876687c8e61127e9 (parent ee1b77baab796b63e2164b5cb39d226f29de59c0). New Foundation run 44419953534 job 135209989291 pending at checkpoint; MovesetPlus 44419953656 job 135209988828 and compressed PRM 44419953633 job 135209989361 COMPLETED SUCCESS, authentic logs read. This fixes a real import blocker, not ABI/ownership/lifecycle/Uzuy. No runtime hooks; three release flags false. NEXT inspect Foundation 44419953534 original job log and repair any failure, then pursue register provenance.

2026-11-19 PENDING_CI: FileLoad CFG witness now tracks path-local ADD Xn,SP,#imm aliases, permits a non-SP-base store only when its recognized byte range is provably disjoint, and kills aliases on register writes. Synthetic positive disjoint, negative overlap, negative clobber regressions added. Code 49e8081e873140520120a90b887af2e92b64db94 parent 18685003b34cc6e5f0673667646183d769fb5440. Upstream ModManager 2.1.2.1 README blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709; NSC-Toolbox 6f780cb README 657f161390c4abe8afe10cea11a2b9a28e6bf6b0; REA main README bb4828fb62da9283985a16b2051cc98efac8c7ec. None establishes Switch consumer ABI. No local Capstone or original runtime test; HEAD Actions log unverified, NOT PASS. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 pinned; Sakura aura107/Event236 both variants untouched; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT inspect Foundation push-run original job log for code HEAD, repair failures, then extend path-sensitive provenance and native consumer ownership evidence.

2026-11-19 PENDING_CI: code 96c14d38f8f2897d48583aa4893b6d93b5d6ebd9 parent cbf830a162e483a209c4e6f3d42e8242d130f61d propagates path-local SP-derived aliases through MOV and ADD/SUB immediate, with synthetic positive MOV+ADD disjoint, negative SUB overlap, and negative source-clobber regressions. Upstream primary README blobs: ModManager 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709 (Steam only), NSC-Toolbox 657f161390c4abe8afe10cea11a2b9a28e6bf6b0 (PC editor), REA bb4828fb62da9283985a16b2051cc98efac8c7ec (generic RE). No Switch ABI proof. Local Capstone unavailable due DNS, authentic HEAD Actions push-run/job/log not obtained; NOT PASS. No hook, no Uzuy test, original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 unchanged; Sakura aura107 and both Event236 variants unchanged; full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false. NEXT inspect Foundation push-run authentic log, fix any regression, then advance consumer ownership evidence from pinned main.

2026-11-19 PENDING_CI: compressed PRM offline CRILAYLA payload re-encoding added with independent decode roundtrip, stored size delta and SHA256, source CPK immutable. Positive marker/zero-change, invalid SHA, missing entry, decoded budget regressions. NOT a CPK repacker or engine consumer; original main SHA256 pinned 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; Sakura aura107/Event236 both variants untouched; three release flags false. NEXT inspect HEAD Actions authentic compressed PRM/Foundation logs, repair failures; prove native ABI/ownership before hooks.

2026-11-19 PENDING_CI: implementation 856f8c7d3b9a300e2a529af0c3fecbb2325fcbe9 adds offline source-SHA-bound compressed Event236 conversion through exact-size independently verified CPK publication, with real synthetic parser positive/negative/integrity regression and no-op/size-change fail-closed. CI HEAD authentic job log pending; not native consumer or Uzuy proof. Evidence handoff/evidence_compressed_same_size_20261119.md. Original main pinned; Sakura aura107 and both Event236 variants untouched; all three release flags false.

2026-11-20 PENDING_CI: authenticated read-only partition of explicit-owner PC editor merged events into selected per-mod manifests with SHA256 per partition; discarded collision rows are not reconstructed. Positive and tamper regression added. Parent 10ef48963b5031531f8c128a893ab2f27cf424b4. Primary references ModManager 2.1.2.1 README blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709; Toolbox 657f161390c4abe8afe10cea11a2b9a28e6bf6b0; REA 6cbd8d77f786b2f71b952a1282fda93a2fbdc13d. No consumer ABI evidence. Original main pinned 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; Sakura aura107, both Event236 variants, three false flags unchanged. Host/HEAD Actions log not verified.

2026-11-23 PENDING_HEAD_CI: independent offline compressed batch verifier now requires exact original CRILAYLA stored bytes for unchanged Event236 payloads, not merely equivalent decoded data and rewritten digest; verifies original reuse and changed encoder provenance. Synthetic negative regressions forge equivalent alternate stream and metadata. Code 227fd1d8e593eb3d1955a1f59b4842b688ab6b15 parent 878885c126daf4d24a08de0df319f7a4f8c876db. Prior parent push compressed run 45152168102 job 137616007681, Foundation 45152168149 job 137616007854, factory 45152168330 job 137616008310, MovesetPlus 45152168100 job 137616007543 all COMPLETED SUCCESS and original logs read; new HEAD CI pending. Upstream ModManager 2.1.2.1 commit 276116ebf5ba398a867793cb02ee6c33c0927645, Toolbox 6f780cb6814f07e03c16b3e78d97dde4e4368983; PC-only, no Switch ABI. Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not rehashed. No hooks, authentic CPK or Uzuy proof; Sakura aura107, Event236 marked/unmarked unchanged; full_moddingapi=false ready_for_gameplay_test=false emulator_tested=false.


# FileLoad indexed-memory alias evidence — 2026-11-27

2026-11-27 VERIFIED_CI_STATIC_ONLY: FileLoad SP/FP alias evidence now records AArch64 register-indexed memory operands and refuses displacement-only stack claims when the index is unresolved. Synthetic regressions prove indexed SP STR/LDR pairs do not create constant stack candidates, shifted index operands are inventoried unresolved, and indexed stores through SP-derived aliases invalidate apparently disjoint witnesses; existing immediate-only positives remain. Code df9a3e1e41db4d1b2063f2ac7b31e5adc6ef3dea (parent 840f92aa7d6dc5b812a07c2fc8c4ae8589b58ac3). Foundation push run 45976679056 job 140430025592 COMPLETED SUCCESS; raw job log inspected: PINNED_FILELOAD_SP_CFG_PASS 166 10 NO_CONSUMER_ABI and RELEASE_FLAGS_FALSE_STATIC_CI_GUARD_PASS 26 NO_UZUY_PROOF. Other HEAD workflows also COMPLETED SUCCESS with raw logs inspected: compressed 45976679041/job 140430025502, factory 45976679120/job 140430025333, MovesetPlus 45976679117/job 140430026222. Foundation proof artifact 15187631793 (263930 bytes). Host/static and original-main SHA-guarded test passed; this slice is not an emulated ARM64 runtime test or Uzuy test. Native consumer ABI, ownership/lifecycle, callback, async, rollback/unbind/destructor, archive precedence and gameplay remain unresolved; all release flags remain false.
Evidence note: `handoff/evidence_fileload_indexed_memory_20261127.md`. Foundation run 45976679056/job 140430025592 completed successfully; raw log inspected. Related compressed/factory/MovesetPlus push runs 45976679041, 45976679120, 45976679117 also completed successfully with raw logs inspected. Artifact 15187631793 contains machine-readable Foundation JSON proofs. This is host/static evidence only, not native consumer ABI or Uzuy gameplay.


Evidence note: `handoff/evidence_fileload_indexed_memory_20261127.md`. The Foundation workflow already executes `tests/test_native_fileload_sp_cfg.py`; its step name now explicitly includes indexed memory. The fixture instruction words were assembled with Clang 17 and verified by LLVM objdump. CI is pending for the code commit. No runtime hooks or release flags changed.


2026-11-27 PENDING_CI — FileLoad status-service evidence. Added a 128-byte exact-main disassembly window at 0x1215358..0x12153d8 (not a function boundary), register/memory operand capture, and full-text direct xref census for 0x1215358/0x1215374. Regressions require the known status-helper and FileLoad-request direct edges and reject unaligned, reversed, or out-of-bounds synthetic windows. Research-first resolved the ModManager pin 276116eb as a child of the 2.1.2.1 tag 502c38d; relevant Toolbox SkillEditorViewModel/SkillEditorModel/Program parser blobs are unchanged between 2.1.2.0 and 2.1.2.1, so no Event236 ID or Switch ABI is inferred. Parent 0e84462e75faa2912bca6a5698987d38d23920eb; CI pending. Lock/unlock semantics, function boundaries, ownership/lifecycle, async/rollback/unbind/destructor, archive precedence and Uzuy remain unresolved. All three release flags remain false.


## 2026-11-27 — FileLoad service dispatch target bodies (PENDING HEAD CI)

The prior service-entry slice is now confirmed by Foundation push run 46013548161/job 140554824874 (COMPLETED SUCCESS; raw log inspected), artifact 15205855931. The exact 128-byte service window SHA256 is 57ceb7351df052e968a1431e70c39812c323d0880d00d36380c01814af58976e. It proves direct dispatches 0x1215364 B 0x1158c90, 0x1215380 B 0x1158d10, and cleanup call 0x12153a8 BL 0x1158d30; it does not prove lock/unlock.

New implementation extends tools/portlib/native_fileload_status.py and tests/test_native_fileload_status.py with a 256-byte exact-main target window 0x1158c90..0x1158d90, bounded direct CFG traces rooted at all three targets, and whole-text direct B/BL inbound edges. Synthetic regressions cover B/conditional branch, BL non-recursion, indirect BR, out-of-window edges, trace budget, and invalid boundaries. Parent c89d815a2a8e6004ff14d4dd7d950e9d95bfc35e; current code commit is pending CI. See handoff/evidence_fileload_status_target_bodies_20261127.md.

The trace deliberately does not infer function boundaries, lock/unlock, ownership, async completion, rollback, unbind/destructor, archive precedence, or consumer ABI. The ModManager 2.1.2.1 release advertises Switch Projectiles Target, but the relevant Toolbox SkillEditorViewModel and SkillEditorModel parser blobs are unchanged between 2.1.2.0 and 2.1.2.1. No new Event236 numeric ID or Switch ABI is inferred. Preserve original main SHA256, Sakura aura107, both Event236 variants and all three false release flags.


2026-11-27 CI FAILURE ANALYSIS: Foundation run 46017177259/job 140567169891 failed only in synthetic_bounded_trace because [0,12) was mistakenly placed in the invalid-window list despite being an aligned in-bounds range of the 16-byte fixture. Raw job log was inspected. The regression now treats [0,12) as a positive truncated-window case and expects its fallthrough at 0xC to be recorded out-of-window; the true negative is [0,20). No production-code change or semantic claim resulted.


## 2026-11-27 — FileLoad service dependency wrappers (PENDING HEAD CI)

2026-11-27 PENDING_HEAD_CI: FileLoad status-service evidence now follows the four exact direct dependencies of the 0x1158c90/0x1158d10 wrappers, records SHA-pinned bounded disassembly/CFG/xrefs, and adds an emulated-ARM64 test that executes the original wrapper bodies while modeling only four leaf targets. Regressions cover first/reentrant acquire, non-final/final release, underflow, zero provider result, different owner token and 32 status-helper cases. This proves only the literal wrapper owner/count transitions under modeled leaf returns; no OS mutex semantics, concurrency, native consumer ABI, lifecycle, archive precedence or Uzuy proof. Parent 5efd93a9d5d23ab96f3fd7a4404a46e50153c6ac; CI pending. Research pins ModManager 2.1.2.1 tag 502c38d (pinned project commit 276116e is its direct child), Toolbox 2.1.2.1 tag 789fe96 (relevant parser blobs unchanged from 2.1.2.0), PyCriCodecs 755055ee, REA 0386efd1. Original main blob 8af900db, SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. No hooks; preserve Sakura aura107, both Event236 forms and all three false flags.
See `handoff/evidence_fileload_service_wrapper_slice_20261127.md`. The new Unicorn case executes the original wrapper instructions but models four external leaf addresses; it is emulated ARM64 evidence only, not Uzuy or real concurrent lock proof.


2026-11-27 CI FAILURE ANALYSIS / REPAIR: Foundation run 46021414045/job 140581709219 failed at synthetic_service_dependency_window: entry 0x8 is NOP and falls through to RET at 0xc, so the expected return PC is corrected to 0xc. The exact dispatch window also shows ADD X0,X0,#8 at 0x1215360 and 0x121537c; wrapper X0 is caller subobject +8, so the emulated owner/count offsets are corrected to original status object +0x28/+0x2c. Raw job log inspected. New HEAD CI pending; no mutex/concurrency/consumer ABI or Uzuy claim.


2026-11-27 CI FAILURE ANALYSIS 2: Foundation run 46022245151/job 140584543848 failed in test_native_fileload_status.py with KeyError `service_target_semantics_verified`; the report field was inadvertently dropped when adding machine-readable dispatch offsets. Restored the explicit false field. Raw log inspected. Three non-Foundation workflows for that HEAD passed with raw logs inspected; corrected HEAD CI pending.


## 2026-11-27 — FileLoad PLT/GOT dynamic-symbol resolver (PENDING_CI)

Parent HEAD: \`39fe92c5c8c45463ba3c9e34d84627480b5dbc45\`. Research pins: ModManager 2.1.2.1 tag \`502c38d3ee832509f9ee3951b7d3339826538fec\`; Toolbox 2.1.2.1 tag \`789fe96f99cdaa77f952b90b563c6e3f49b6d697\`; PyCriCodecs \`755055ee7b056c9c1aefc6505a3daa3e45e2e111\`; REA \`0386efd1e1dfa41af41f804a6be56c6f5b7615d4\`. Source hashes and the Switch main blob/hash are recorded in \`handoff/evidence_fileload_imports_20261127.md\`.

Implemented a SHA-pinned analyzer for four FileLoad PLT stubs. It checks the original wrapper callsites and two pointer-dereference adapters, verifies each ADRP/LDR/ADD/BR sequence, computes the GOT slot independently from LDR and ADD, then resolves a unique original DT_RELA/DT_JMPREL record and ELF64 dynamic symbol name when possible. Slots: \`0x2142a28\`, \`0x2142a78\`, \`0x2142a80\`, \`0x2142c20\`. The output deliberately distinguishes a dynamic symbol name from the imported implementation and runtime binding.

Local syntax and isolated synthetic positive/negative/boundary checks passed. Authentic original-main integration and Actions are pending. No native hook or runtime flag changed. No consumer ABI, lock concurrency, provider semantics, ownership/lifecycle, archive precedence, or Uzuy claim.


## 2026-11-27 — FileLoad leaf imports resolved to original Nintendo nn::os symbols

Implementation commit \`0620f7dc5b532e11ef868926aa0a4777e763e40c\` passed all four push workflows. Foundation run/job \`46025160592/140594557183\` passed the new analyzer and produced artifact \`15210669622\` (ZIP SHA256 \`c65fa78688060b689524193f1f7648c85ab80f4fa59afcb278c60709af503412\`). Raw logs for Foundation, factory, MovesetPlus, and compressed PRM were inspected.

The original main's four unique \`R_AARCH64_JUMP_SLOT\` records resolve to \`nn::os::GetCurrentThread()\`, \`nn::os::GetThreadId(nn::os::ThreadType const*)\`, \`nn::os::LockMutex(nn::os::MutexType*)\`, and \`nn::os::UnlockMutex(nn::os::MutexType*)\`. Relocation records and symbol indices are in \`handoff/evidence_fileload_imports_20261127.md\`. The bounded wrapper code passes the current-thread pointer into GetThreadId, uses its W0 result as the owner token at wrapper offset +0x8, keeps a count at +0xc, and calls the acquire/release adapters on owner mismatch / count reaching zero. This is static flow only; imported symbols are undefined in main (st_shndx=0), and their runtime provider, implementation, object lifetime and true concurrency semantics remain unresolved.

The analyzer and tests are committed. No hook, runtime patch, or release flag changed. Next: identify the actual Switch loader provider module for these imports, then trace the wrapper object's allocation and destruction before any runtime integration.


## 2026-11-28 — FileLoad caller X19 reaching definitions with exact-callee preservation (PENDING_CI)

Parent HEAD: `95dda35fb5424425a720ced7c95db1f9ea6fdbee`. The existing unique FileLoad caller at `0x116f29c` passes X1=`SP+0x30` and X2=`X19`; this slice extends the bounded caller-origin analysis to X19 and records exact direct callees before that call. X19 crosses a call only if the exact direct target passes the existing recursive bounded no-write/all-return proof (`prove_register_preservation`); otherwise the analyzer emits a call barrier. No AAPCS64 or platform ABI assumption is used. The pinned caller window remains `[0x116f09c,0x116f2a0)`, SHA256 `e18c0fcb01a040df2b232820813420313e623c5747bd0734507920507ba0775d`; original main SHA256 remains `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`. Synthetic regressions cover preserved leaf, missing/negative proof, mismatched target and conditional merge. Evidence: `handoff/evidence_fileload_caller_x19_20261128.md`. CI is pending. This does not prove X19 numeric value, pointer type, object ownership/lifetime, consumer ABI, archive precedence or Uzuy. All three release flags remain false.


### CI failure and correction — 2026-11-28

The first code HEAD `04cd926fe4af8144e53fc7eb92c9c5096ce38fd0` triggered all four push workflows. Factory `46046167081/140665869136`, compressed PRM `46046167126/140665868803`, and MovesetPlus `46046167216/140665868954` completed successfully; their raw logs were inspected. Foundation `46046167094/140665868834` failed in `tests/test_native_fileload_inbound_args.py::synthetic` before original-main analysis: the exact expected `single_definition_proven_within_window` mapping still contained only X1/X2 after X19 was added to `TRACKED`. This is a stale test expectation, not a decoder or original-byte mismatch. Correction: include `x19: false` for the untouched window-entry value; dedicated X19 positive, negative, mismatched-target and branch-merge regressions remain. New push CI is pending; no PASS claim.


## 2026-11-28 — FileLoad caller X19 direct-call inventory and provenance (VERIFIED_STATIC_CI_ONLY)

Implementation parent `95dda35fb5424425a720ced7c95db1f9ea6fdbee`; X19 source commit `04cd926fe4af8144e53fc7eb92c9c5096ce38fd0`; regression correction commit `ac71215f23bd645119f830cc4c63d0b5b2f1974b` (parent `5187073633307e43985684325ebdce9821948849`). The initial synthetic-map expectation failure was fixed. A subsequent failure exposed a more substantive test-fixture error: the manually transcribed direct-call list contained only ten calls, while independent decoding of raw little-endian A64 instruction words found 23 direct BL instructions in the pinned caller window. The test now independently decodes signed imm26 BL targets, excludes unconditional B, and compares all site/target pairs with the exact-callee proof inventory. Synthetic cases cover forward/backward BL, B exclusion, malformed/unaligned words, ordering and invalid boundaries.

Original main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`. Unique FileLoad caller remains `BL 0x116f404` at `0x116f29c`, word LE `5a000094`. Caller window `[0x116f09c,0x116f2a0)`, SHA256 `e18c0fcb01a040df2b232820813420313e623c5747bd0734507920507ba0775d`, 129/129 decoded instructions, zero decode failures, one external direct inbound edge, four out-of-window control-flow edges; the bounded window is therefore not complete or a proven function extent.

Of the 23 direct BLs, only four exact targets pass the strict recursive bounded no-write/all-return proof for X19: `0x116f0b8 -> 0x116d3c0`, `0x116f11c -> 0x116d3c0`, `0x116f130 -> 0x12163d8`, and `0x116f1c0 -> 0x116d3c0`. At the FileLoad sink, X19 remains a call barrier at `0x116f280 -> 0x120a6c8`. The bounded target writes X19 at `0x120a6cc: mov x19,x0` and `0x120a724: ldp x30,x19,[sp],#0x10`; no matching saved incoming-X19 slot or all-return restoration proof exists yet. X1 has a local candidate definition `add x1,sp,#0x30` at `0x116f284`; X2 is copied from X19 at `0x116f294`, so its value remains unresolved. No pointer type, object ownership/lifetime, consumer ABI, async/rollback/unbind/destructor, archive precedence, or gameplay proof.

All four push workflows for code/test HEAD `ac71215f23bd645119f830cc4c63d0b5b2f1974b` completed SUCCESS and raw job logs were inspected:
- Foundation run/job `46048379870/140673240478` — `PINNED_FILELOAD_INBOUND_ARGUMENTS_PASS`, `RELEASE_FLAGS_FALSE_STATIC_CI_GUARD_PASS`; artifact `15223636352`.
- Factory `46048379872/140673240433`.
- Compressed PRM `46048379855/140673240097`.
- MovesetPlus `46048379836/140673240368`.

Foundation artifact ZIP SHA256 `389c894d70f8f8fda4186e9a86352944427caf22bfe302a5637f2ca1f210c2ee`; `native_fileload_inbound_args.json` SHA256 `28892246edbb718743c1f8bd4ea43d28086f7a65453ab41221aa6725fd57d3fd`. Evidence: `handoff/evidence_fileload_caller_x19_20261128.md`.

Next: prove exact SP-relative save/restore of incoming X19 in `0x120a6c8` and every other X19-writing callee, with path-sensitive SP deltas, same-slot identity, no intervening overwrite and restoration on every return. Keep barriers where any condition is unresolved. No runtime hooks. All release flags remain false.


2026-11-28 PENDING_CI — FileLoad X19 stack-slot dataflow. Parent HEAD ace04f5ea7a8a21b9a625eb69fdce3d95eb767e6. Added path-sensitive SP-delta/register-origin/stack-slot analysis for exact X19 save/restore in bounded AArch64 callees; X19-writing callees remain barriers unless every observed return restores the exact entry value, SP is balanced and trusted, and no nested call/unknown alias store/unresolved edge remains. Synthetic positive/negative/boundary cases cover exact STP/MOV/LDP, wrong destination, slot overwrite, nested BL, unknown-base store, conditional untouched/clobbered paths, unbalanced SP and invalid windows. Primary source pins: ModManager 2.1.2.1 tag 502c38d3 (release notes Switch Projectiles Target), prior 2.1.2.0 tag a4a6e7e2 (patchnotes blob 37c3d8b0 shows Start/Stop Deflect); Toolbox tags 789fe96f/dfe371dd with identical SkillEditorModel blob e1654716; PyCriCodecs 755055ee (CPK blob 2ed2cbb2, UTF blob d1662d14); REA 0386efd1 (README 474ecfbe, CLI 35f686aa). Original main Git blob 8af900db, expected SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. Existing Foundation workflow already executes the modified test. CI pending; no consumer ABI, ownership/lifecycle, archive precedence or Uzuy claim. Preserve Sakura aura107, Event236 marked/unmarked, and all three false release flags. NEXT inspect the four exact HEAD push runs/jobs/raw logs and Foundation artifact; only relax the X19 call barrier if the authentic result satisfies every proof condition.


2026-11-28 FAILED_CI — first X19 stack-slot analyzer commit b58222f63414caf0dcb47a25add4d18dad434d70. Direct push API found four runs: Foundation 46057774996/job 140704341842 FAILED at step 42 because the first synthetic exact STP/MOV/LDP positive case returned preservation_proven=false; factory 46057774990/job 140704342069, compressed candidate 46057775108/job 140704342091 and MovesetPlus 46057774991/job 140704342005 COMPLETED SUCCESS with raw logs inspected. Root cause is not yet asserted; diagnostic test now prints the full synthetic proof report. X19 caller remains a barrier. Next: inspect the printed report, fix pre/post-index SP effective-address tracking, rerun all push workflows, then inspect the authentic original-main report. No ABI/runtime claim.


2026-11-28 FIXED_PENDING_CI — Diagnostic Foundation run 46058304370/job 140706108304 failed the first synthetic positive at step 42. Raw log showed STP x30,x19 [sp,#-0x10]! and LDP x30,x19 [sp],#0x10 decoded with correct SP writeback; return SP delta was 0/trusted, but save_sites and restore_sites were empty. Root cause: Capstone 5.0.6 exposes X30/X29 aliases as lr/fp; reg_width accepted only xN/wN and rejected lr, so pair transfer rows were discarded. Updated reg_width to accept fp/lr as 8-byte aliases; removed temporary diagnostic print. Authentic FileLoad X19 barrier remains unchanged. Rerun all four push workflows and inspect raw logs/artifact.


2026-11-28 TEST_EXPECTATION_FIX_PENDING_CI — After the fp/lr alias correction, Foundation run 46058845472/job 140707894811 passed the exact STP/MOV/LDP positive, wrong destination, overwritten slot, nested-call barrier and unknown-base-store cases. It failed only the bypass test at line 212: the branch path and fallthrough path converge at the same RET PC with identical state, so the path-sensitive worklist correctly deduplicates them to one return state. Corrected expectation to one return state and five reachable instructions; the proof must still be true. Compressed candidate 46058845542/job 140707894934 (39+16 tests), factory 46058845543/job 140707894897 (13+5+2+13 tests), and MovesetPlus 46058845462/job 140707894631 (3+4+13+3 tests) all succeeded; raw logs inspected. Rerun Foundation and companions on new HEAD.


## 2026-11-28 — Recursive FileLoad X19 proof tree (VERIFIED_CI_STATIC_ONLY)

2026-11-28 VERIFIED_CI_STATIC_ONLY: Fixed recursive FileLoad X19 proof-tree serialization. `analyze_stack_register_restore()` returns `nested_call_proofs` as a list; the parent serializer incorrectly called `.values()`, causing Foundation step 42 to raise AttributeError. Changed it to copy the list directly. Existing regression covers list shape, nested-call failure and cycle evidence. Code commit dbc23b155335c61602437c72e7f1ceabbe35553d (parent 255adab51824809ca8920c4b65dba6a3d326fb41). All four push workflows COMPLETED SUCCESS with raw logs inspected. Foundation artifact 15231780092 (336355 bytes, SHA256 598559d70ee9d2911c52fc6109b722465b87b96d3e5b9b77f2de8b99f38fc7aa); inbound-args JSON SHA256 d3a1ece8b05743da15643babe98d77fffa0995532477f0bf6e769bbec66102e5. Authentic original main SHA256 guard passed. Exact local X19 save/restore at SP-8 is proven, but nested call stack effects and unknown-base writes keep X19 at 0x116f280 -> 0x120a6c8 unresolved. Static proof only; no consumer ABI, ownership/lifecycle, archive precedence or Uzuy claim. All three release flags remain false.

The original-main report proves the local X19 slot roundtrip at entry-SP-8: STP at `0x120a6c8`, LDP at `0x120a724`, return at `0x120a728`. However SP trust remains false because four nested direct callees have unresolved stack/alias effects. The recursive proof tree identifies `0x116b698` (nested `0x116b6c0 -> 0x116b7b0`), `0x1188104` (five unknown X0 stores), `0x1170f7c` (nested `0x11704c4`), and `0x1160c64` (three unknown X0 stores). Keep the X19 call barrier. See `handoff/evidence_fileload_x19_recursive_proofs_20261128.md` for exact hashes, nested failure sites, upstream source comparisons and CI evidence.

Code/test HEAD `dbc23b155335c61602437c72e7f1ceabbe35553d` (parent `255adab51824809ca8920c4b65dba6a3d326fb41`) passed all four push workflows; raw job logs inspected: Foundation `46066250617/140732155719`, Factory `46066250621/140732155517`, Compressed PRM `46066250642/140732155515`, MovesetPlus `46066250702/140732155859`. Foundation artifact `15231780092`, ZIP SHA256 `598559d70ee9d2911c52fc6109b722465b87b96d3e5b9b77f2de8b99f38fc7aa`; inbound args JSON SHA256 `d3a1ece8b05743da15643babe98d77fffa0995532477f0bf6e769bbec66102e5`. All release flags remain false; no ABI, ownership/lifecycle, archive precedence or Uzuy claim.


## 2026-11-28 — FileLoad guard-state and registration-helper candidate (PENDING_CI)

Parent HEAD `261e4aab417b1aebaaeddb9a83160a46dc812255`. Research-first source comparison rechecked ModManager 2.1.2.1 / 2.1.2.0 and Toolbox 2.1.2.1 / 2.1.2.0; the inspected ModManager `SkillCustomizeParamModel.cs` blob `6a891e23` and Toolbox `SkillEditorModel.cs` blob `e1654716` are unchanged across the release tags. PyCriCodecs CPK/UTF blobs `2ed2cbb2` / `d1662d14` provide format reference only; REA commit `0386efd1` provides a reproducible reverse-engineering workflow, not game-specific ABI.

New read-only analyzer `tools/portlib/native_fileload_guard_state.py` and regressions `tests/test_native_fileload_guard_state.py` decode original-main ADRP/ADD and ADRP/LDR chains, map exact guard/object addresses and explicit store ranges into NSO image regions, cross-check the two `__cxa_guard_*` DT_JMPREL names, and record the bounded `0x290` atomic 24-byte three-register registration-helper candidate. It does not identify the callback/destructor or helper, resolve imported implementations/provider, or prove native ABI. Foundation workflow step added; CI pending. Keep the parent X19 call barrier and all release flags false. See `handoff/evidence_fileload_guard_state_20261128.md`.


## 2026-11-28 — FileLoad registration code-pointer target CFG (PENDING_CI)

Parent HEAD: `9975550ae11657970ae8905a808aa0360ad36710`. Research-first comparison revalidated ModManager 2.1.2.1 (Switch Projectiles Target) versus 2.1.2.0 (Start/Stop Deflect) and Toolbox 2.1.2.1/2.1.2.0. The inspected skill model/viewmodel and XFBIN parser blobs are unchanged across the release tags; no parser ABI delta is established. PyCriCodecs CPK/UTF blobs `2ed2cbb2` / `d1662d14` are generic archive-format references. REA `morluto/rea@0386efd1` is methodology/evidence workflow only.

The verified guard-state artifact resolves pointer cell `0x215d2b0` through one `DT_RELA R_AARCH64_RELATIVE` record at `0x1976d80` to link-time text addend `0x116b888`. New source `tools/portlib/native_fileload_registration_target.py` traces the bounded `[0x116b888,0x116b988)` CFG and records register/memory operands, direct/indirect call barriers, returns, external edges, raw aligned-text B/BL word candidates and window SHA. New tests cover positive/negative/boundary CFG behavior and exact original-main SHA/relocation. This is not callback/destructor/function-extent/runtime-pointer/ABI/ownership proof. CI is pending; no hooks. Preserve original main SHA, Sakura aura107, Event236 marker 0x4E53 +0x2A and unmarked Event236; all three release flags remain false.


## 2026-11-28 — Registration target CFG width fix (PENDING_CI)

The first target-trace commit `c62ff2e537d845f6410b009045de423c103e0dce` had Factory, Compressed PRM and MovesetPlus workflows SUCCESS, but Foundation failed in the new synthetic memory-width test: Capstone 5.0.6 `Arm64Op` has no `.size` attribute. Raw job log `46076828184/140766410479` was read; the failure occurred before authentic-main analysis and no Foundation artifact was created. Fixed by deriving only widths supported by mnemonic/data-register class (signed byte/halfword/word, register pair, LDPSW), leaving unknown widths null. Added W-register, byte, pair and signed-word regressions. New source/test blobs: `99044155b3ddb50c4bbbae4154baac730f2187ed` / `1b298593ac37bf4da039fb27b197464d0fb949b3`. Push and verify the corrected Foundation workflow plus all three other direct push workflows; do not mark this slice PASS yet.


## 2026-11-28 — FileLoad registration pointer target CFG (VERIFIED_CI_STATIC_ONLY)

Code commit `b094f345bb27b071fcb509b1fbc7cdf3eee5ac5e` (parent `c62ff2e537d845f6410b009045de423c103e0dce`). The original-main SHA256 guard and exact `DT_RELA R_AARCH64_RELATIVE` cell `0x215d2b0` -> text addend `0x116b888` passed. Bounded window `[0x116b888,0x116b988)` SHA256 `877fcd30e1fb00f75bf143dfb499419122edb72acf95677b73219ee7f0a809ec`; 33 reachable instructions, return at `0x116b908`, one direct call `0x116b8a4 -> 0x116b390`, no indirect calls/terminators or out-of-window edges. Static register flow shows a 64-entry pointer-sized table loop starting at `0x4371800`, then 16 `STP Q0,Q0` stores clearing 0x200 bytes. The direct callee `0x116b390` is not yet analyzed; no destructor/ownership/ABI claim.

All four direct push workflows on this exact code HEAD completed SUCCESS and raw job logs were inspected: Foundation `46077330193/140768008713`, Factory `46077330238/140768008784`, Compressed PRM `46077330215/140768008716`, MovesetPlus `46077330236/140768008350`. Foundation artifact `15234858334`, ZIP SHA256 `7dad9c43345b5094a7cc3531df03c11c10dc01fd5b86c145585952551eb3207a`, report JSON SHA256 `7f70068cb9a900f95a40ed1adc9520a8441f635523acaf6c11b8a94fe43750e0`.

Research-first full release comparison found no upstream parser source delta between NSC-ModManager/Toolbox 2.1.2.0 and 2.1.2.1; the changed PC `conditionprmManager.xfbin` begins with `DUMMY` in both versions and contains no feature identifiers. Latest REA HEAD and PyCriCodecs CPK/UTF references are recorded in `handoff/evidence_fileload_registration_target_20261128.md`.

This is host/static evidence only. No new ARM64 runtime consumer or Uzuy test. No hook. Preserve original main SHA, Sakura aura107, Event236 marker `0x4E53 +0x2A`, and unmarked Event236. `full_moddingapi=false`, `ready_for_gameplay_test=false`, `emulator_tested=false`.

## 2026-11-28 — FileLoad registration-table direct callee (VERIFIED_CI_STATIC_ONLY)

Code commit dffbf1bd2fc5257a72279186545bbd8d956ab0fe (parent a859b4454fe7f8b1b18c5930bba38c483e7b7b6). Original-main SHA256 guard passed. The caller's 64-bit X0 load at 0x116b8a0 is ldr x0,[x8,#0x28], followed by BL 0x116b8a4 -> 0x116b390. The bounded callee window [0x116b390,0x116b590) has SHA256 0c12e8360c74f94b501046964810bf996668d938fabcc87a93dd34e70a7afd55 and reaches 24 decoded instructions, RET 0x116b3dc, three direct calls (0x116b39c->0x116b7b0, 0x116b3a4->0x116d380, 0x116b3b0->0x116b82c), BR X2 at 0x116b3d0, and out-of-window B 0x116b3ec -> 0x116d820. Raw aligned B/BL inbound census has 114 candidates; this is not an exact call count or function boundary proof.

All four direct push workflows on this code HEAD completed SUCCESS and raw job logs were inspected: Foundation 46082949640/job 140785901176; Factory 46082949657/job 140785901415; Compressed PRM 46082949728/job 140785901575; MovesetPlus 46082949502/job 140785901019. Foundation marker: PINNED_FILELOAD_REGISTRATION_CALLEE_PASS 0x116b390 reachable 24 direct_calls 3 indirect_calls 0 NO_CALLBACK_NO_DESTRUCTOR_NO_ABI_CLAIM. Artifact 15238645422 (513005 bytes), ZIP SHA256 0fd7633194afc59e31548bf8767ce2651776b79f2388fb3248d7695853512ed8; report JSON SHA256 2977741b1f6763aa3e80444607362c1f0429c2aa2bde486f071220e190b0103c. Static/host only; no Uzuy or new analyzer ARM64 execution. Release flags remain false.

## 2026-11-28 — FileLoad registration callee dispatch-flow trace (PENDING_CI)

New source tools/portlib/native_fileload_registration_dispatch.py and test tests/test_native_fileload_registration_dispatch.py validate the exact X0->X19 move, three direct calls, CBZ exits, 0x20 stack save/restore, X8<-*[X0], X2<-*[X8+0x58], X1<-X19 and indirect BR X2 at 0x116b3d0. The analyzer records four bounded 0x100-byte target windows for 0x116b7b0, 0x116d380, 0x116b82c and 0x116d820. It does not resolve the BR X2 target or identify a callback, vtable, destructor, object type, ownership/lifecycle, lock/unlock, async, rollback/unbind, ABI, archive precedence or Uzuy behavior. No hook. Parent HEAD dffbf1bd2fc5257a72279186545bbd8d956ab0fe; CI pending.

## 2026-11-28 — FileLoad registration callee dispatch flow (VERIFIED_CI_STATIC_ONLY)

Code commit 9c06a6bba6d5c69f49107ce3094cbee614d4f5df (parent dffbf1bd2fc5257a72279186545bbd8d956ab0fe). The original-main SHA256 guard passed. The analyzer verified X19<-X0 at 0x116b398; BL edges 0x116b39c->0x116b7b0, 0x116b3a4->0x116d380 and 0x116b3b0->0x116b82c; X8<-*[X0] at 0x116b3bc; X2<-*[X8+0x58] at 0x116b3c4; X1<-X19 at 0x116b3c0; and BR X2 at 0x116b3d0. CBZ X19 branches to 0x116b3d4; CBZ X0 branches to 0x116b3e0; alternate B at 0x116b3ec targets 0x116d820. Local stack save/restore spans 0x20 bytes.

Four bounded 0x100-byte windows: 0x116b7b0 (31 reachable, RET at 0x116b7d0/0x116b828, direct calls to 0x12f3690, 0x290 and 0x12f36a0); 0x116d380 (15 reachable, RET 0x116d3b8, no direct calls); 0x116b82c (18 reachable, RET 0x116b858/0x116b870, direct call 0x116b864->0x12155a0); 0x116d820 (6 reachable, RET 0x116d834, no direct calls). These are bounded code windows, not full function extents. BR X2 remains unresolved.

All four direct push workflows on code HEAD 9c06a6bba6d5c69f49107ce3094cbee614d4f5df completed SUCCESS and raw job logs were inspected: Foundation 46083883814/job 140788864287; Factory 46083883804/job 140788864137; Compressed PRM 46083883928/job 140788864729; MovesetPlus 46083883860/job 140788864262. Foundation marker PINNED_FILELOAD_REGISTRATION_DISPATCH_PASS targets 4 indirect_branch 0x116b3d0 NO_CALLBACK_NO_DESTRUCTOR_NO_ABI_CLAIM. Artifact 15238396702 (520490 bytes), ZIP SHA256 d33b8fdc4bb728a9d1c7337674a87e6777dcd1a69e4752e36d6f08c51659966c; dispatch JSON SHA256 f2eed43777e1679e2948f0a43ef02c0022ac623586997545573c12949214ab1a. Static/host only; no new ARM64 execution or Uzuy test. Release flags remain false.

Next exact targets to inspect are 0x12f3690, 0x290, 0x12f36a0, 0x12155a0 and alternate branch 0x12f49b0; do not infer lock/unlock or callback semantics from addresses alone.

## 2026-11-28 — FileLoad registration helper and allocator-free tail (VERIFIED_CI_STATIC_ONLY)

2026-11-28 VERIFIED_CI_STATIC_ONLY: New pinned FileLoad registration-lifecycle trace on code HEAD 2b06a49730dc3bdf9816cc7f4f984231aa34b4fe (parent 3982db7cbea721a3308870945cd29dad6598a5ba). Original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 verified. The 0x290 helper writes 24-byte records as x8/x1/x2 at offsets 0/8/16, using an atomic counter and two relocated table pointer cells both targeting 0x2161230; runtime table values remain unverified. Registered code-pointer candidate 0x116b888 walks 64 pointer-sized slots from 0x4371800, calls 0x116b390 per slot, then clears 0x200 bytes; callback/destructor identity is NOT proven. Guard imports at 0x12f3690/0x12f36a0 resolve to __cxa_guard_acquire/__cxa_guard_release for guard 0x43717d8. Alternate tail 0x116d830 -> PLT 0x12f49b0 resolves to nn::mem::StandardAllocator::Free(void*); receiver cell 0x215d2e8 relocates to BSS 0x4371a00 and X1 receives the alternate-path X19 value. Index-error call 0x116b864 -> 0x12155a0 passes rodata string 'BlockManager::GetBlock break\n'. CI run 46086093686/job 140795884030 COMPLETED SUCCESS; raw log inspected; artifact 15238478983; ZIP SHA256 7e6362c66972f6d35588a73c6ae25cc9aed3d6285b674d9ef479a4789bd87fd3; JSON SHA256 51fb342cffdb2b39ea7d3c72aa21c21afcb20b6ea1c979a15f91eba4de74c949. Host/static only; no consumer ABI, ownership, destructor, async, rollback/unbind, archive precedence, emulated ARM64 or Uzuy proof. No hook; all three release flags false.

- Exact 0x290 helper record writes: x8/x1/x2 at byte offsets 0/8/16; stride 24; table pointer cells 0x2143460 and 0x2143468 each relocate to 0x2161230; atomic counter 0x21620d8.
- Cleanup candidate 0x116b888 iterates 64 8-byte slots at 0x4371800, calls 0x116b390 per slot and clears 512 bytes. Not identified as a destructor.
- Guard imports: __cxa_guard_acquire/__cxa_guard_release for guard 0x43717d8. Alternate tail resolves to nn::mem::StandardAllocator::Free(void*) with receiver relocation target 0x4371a00 and X1 sourced from X19. Error literal: BlockManager::GetBlock break\\n.
- CI: run 46086093686 / job 140795884030 COMPLETED SUCCESS; raw log inspected; artifact 15238478983; report SHA256 51fb342cffdb2b39ea7d3c72aa21c21afcb20b6ea1c979a15f91eba4de74c949. Only the isolated FileLoad workflow ran; unrelated PASS suites were not rerun.
- Static/host only. BR X2 target, callback/destructor, ownership, runtime table values, lock/async/rollback/unbind, archive precedence, emulated ARM64 and Uzuy remain unverified. No hook; all release flags false.


## 2026-11-28 — FileLoad 64-slot table direct-reference census (IMPLEMENTED_AWAITING_CI)

Parent HEAD: 9ea102fe95646d1d595ec33335aa16a563e5ef97. Research-first re-read confirmed upstream ModManager/Toolbox 2.1.2.1 parser sources are unchanged from 2.1.2.0; UltimateStormAPI 2.1.2.1 adds PC Windows command 29 (TakeOverEnemyProjectiles) using a mutex and 250 ms pointer window, not Switch ABI. PyCriCodecs CPK/UTF and REA binary-diagnostics sources were consulted as format/evidence references only.

New analyzer tools/portlib/native_fileload_table_access.py scans every aligned ADRP targeting page 0x4371000, follows only 0x100-byte bounded linear ADRP/ADD/MOV chains, and inventories direct memory accesses overlapping [0x4371800,0x4371a00). It also inventories dynamic RELA destinations in that range and addends pointing into it. Synthetic regressions cover direct load/store/pair-store, exact end boundary, branch barrier, register clobber, malformed windows, relocation boundaries and overlapping tables. The original main SHA256 is pinned. Expected authentic checks include the slot read at 0x116b8a0 and 16 existing 32-byte clear stores at 0x116b8c4..0x116b900.

CI is pending. This is not a producer identity, callback/destructor, BR X2 target, ownership, ABI, archive-precedence or runtime proof. No hook. All release flags remain false. See handoff/evidence_fileload_table_access_20261128.md.


## 2026-11-28 — FileLoad table census workflow correction (IMPLEMENTED_AWAITING_CI)

The first push added a separate workflow file but no Actions run was emitted for that commit. Corrected the synthetic ADRP page encoder (page delta is measured in pages, not bytes), tightened table range alignment, and moved the new regression into the already active FileLoad registration lifecycle workflow. The workflow now has explicit source/test path filters and uploads the table-access JSON separately. Follow-up parent: 30a06adf117ffc4f5657044922fcff360820d8b0. No PASS claim until the new push job log and artifact are inspected.


## 2026-11-28 — FileLoad table reaching-definition correction (IMPLEMENTED_AWAITING_CI)

Raw lifecycle job 46088241951 / job 140802797820 showed why the first-slot assertion failed: X19 is set to XZR at 0x116b890, ADRP X20 is at 0x116b894, ADD X20,X20,#0x7d8 at 0x116b898, ADD X8,X20,X19 at 0x116b89c, and LDR X0,[X8,#0x28] at 0x116b8a0. The scanner only tracked immediate ADD. It now includes a bounded 0x20-byte prefix, models XZR and MOV, and propagates ADD-register only when both source values are known. Unknown values remain unresolved.

The broad foundation workflow now excludes this isolated analyzer/test to avoid rerunning unrelated PASS suites; the already active FileLoad lifecycle workflow runs the new test and uploads a separate artifact. Previous failed attempts and raw-log inspection are recorded in the checkpoint. Follow-up parent: 3ba748262c0790f781249cbb8c1eb55410aa538c. CI pending.


## 2026-11-28 — Dual FileLoad table traversal/zeroing census (IMPLEMENTED_AWAITING_CI)

The first passing table artifact (run 46088613491, job 140803970356) showed 89 ADRP page references, 34 direct accesses, 2 first-slot reads, 32 32-byte stores and zero RELA destinations/addends pointing into the 64-slot range. The 16 writes outside the first known sequence were a second matching 16-store path, not a producer.

The extension now decodes bounded CFG windows at 0x116b888..0x116b988 and 0x116b918..0x116ba18, verifies reads at 0x116b8a0 and 0x116b924, verifies two reverse 16-store 512-byte sequences, checks MOVI V0,#0 remains intact through the last Q0 store, and enumerates direct B/BL inbound callsites to helper 0x116b390. Conditional/indirect inbound edges remain outside this census. Synthetic B/BL positive, negative and alignment-boundary tests were added. CI pending.


## 2026-11-28 — Dual FileLoad table traversal/zeroing census VERIFIED_STATIC_CI_ONLY

Implementation commit: 0bc4cb45d713325cf8e33f0385b42535791fe5ab. Parent: 05afa169bc47025b0ea18f3fae2b85da9601c54d. GitHub Actions run 46089004753 (run #5), job 140805260736: COMPLETED SUCCESS. The raw job log was inspected and printed both PINNED_FILELOAD_REGISTRATION_LIFECYCLE_PASS and PINNED_FILELOAD_TABLE_ACCESS_CENSUS_PASS. Artifact 15239987914, FILELOAD_TABLE_ACCESS_STATIC_EVIDENCE, ZIP SHA256 97f2b7734baef912d6becf291ed88c2b2bc59427f641ca238b96cc29751bca28; report JSON SHA256 49b68228ce6a598471d5778e9e847bdbb10c00e11bd7ae3e806618b923f7586d.

Reproduced against original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9: table [0x4371800,0x4371a00), 64 qword slots in BSS [0x2161234,0x44cc000). The scanner found 89 ADRP page references and 34 direct memory accesses: two first-slot reads at 0x116b8a0 and 0x116b924, plus two 16-store reverse sequences of 32-byte STP Q0,Q0 at 0x116b8c4..0x116b900 and 0x116b948..0x116b984. MOVI V0,#0 sites 0x116b8b4 and 0x116b938 remain unmodified through the final Q0 store in each bounded CFG window, so both 512-byte sequences are verified zeroing operations. No direct writes were found outside these two sequences. 288,973 dynamic RELA records were scanned; zero relocation destinations and zero addends point into the table. Direct B/BL inbound census found 101 callers of helper 0x116b390, including the two table-path calls at 0x116b8a4 and 0x116b928. No direct B/BL inbound to bounded path start 0x116b918 was found; do not label it a function entry.

This materially narrows the static producer search, but it does not prove there is no indirect/dynamic writer. Conditional/indirect branches, indexed effective addresses, heap aliases, function extents, object type, destructor, BR X2 target, ownership, locks, async, rollback/unbind, native consumer ABI, archive precedence, ARM64 emulation and Uzuy remain unresolved. Release flags remain false.


## 2026-11-28 — FileLoad helper inbound caller census (IMPLEMENTED_AWAITING_CI)

Research-first comparison rechecked NSC-ModManager and NSC-Toolbox 2.1.2.1 against 2.1.2.0. The inspected XFBIN parser and skill model/editor blob IDs are unchanged across those release tags. UltimateStormAPI 2.1.2.1 adds PC Windows command 29 `TakeOverEnemyProjectiles` with a mutex and 250 ms projectile window; this is not Switch ARM64 ABI evidence. PyCriCodecs CPK/UTF is a generic format reference. The pinned REA binary-diagnostics profile explicitly does not support AArch64. Exact refs and hashes are recorded in `handoff/evidence_fileload_helper_callers_20261128.md`.

New read-only source `tools/portlib/native_fileload_helper_callers.py`, regression `tests/test_native_fileload_helper_callers.py`, and isolated workflow `.github/workflows/verify-fileload-helper-callers.yml` classify the 101 raw aligned B/BL candidates targeting `0x116b390`. For each Capstone-confirmed branch, the analyzer records a bounded 0x40-byte prelude, instruction bytes, register reads/writes, memory operand base/index/displacement/width, control-flow barriers, last syntactic writes to X0-X7 and deterministic signature clusters. It verifies the two known table-path calls at `0x116b8a4` and `0x116b928` remain preceded by `LDR X0,[X8,#0x28]` at `0x116b8a0` and `0x116b924`.

State: IMPLEMENTED_AWAITING_CI. The prelude writes are not reaching definitions; X0-X7 are architectural register candidates only. No function extent, parameter meaning, producer, writer, BR X2 target, object type, callback/destructor, ownership/lifecycle, lock/async/rollback/unbind, native consumer ABI, archive precedence or Uzuy claim. All release flags remain false.
