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
