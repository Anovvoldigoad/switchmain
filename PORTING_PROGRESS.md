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
  1 prasyarat P67, 24 word koridor P128. Batas raw 512 dibiarkan utuh sampai
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
CPK masih satu path Tobi; descriptor kondisi dan membership ougi masih generated
untuk data lama. Factory berbasis profil sekarang terintegrasi untuk 228 selector yang namanya
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
menjadi importer `.nsc` umum atau loader multi-CPK.

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
