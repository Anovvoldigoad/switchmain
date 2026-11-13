
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
