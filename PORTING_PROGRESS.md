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
