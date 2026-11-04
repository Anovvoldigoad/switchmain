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
- Rantai installer compiled mengajukan 19 lokasi hook berbeda. Getter raw
  memakai replacement, sehingga diperlukan 18 trampoline dari kapasitas 20.
  Publikasi hook dan pemetaan executable oleh OS dimodelkan dalam tes ini.
- Tiga segmen NSO identik dengan ELF, checksum cocok, segment permissions RX/R/RW,
  tanpa DT_NEEDED; dua import `nn::ro` sesuai bootstrap yang digunakan.

Allocator, memset, diagnostic logging, serta bagian konteks OS/RTLD yang tidak
sedang diuji dimodelkan. Tes ini tidak menjalankan game penuh dan tidak membuktikan
ketersediaan resource, konstruksi/destruksi actor secara lengkap, atau kecocokan
emulator Android.

## Pekerjaan yang masih menghalangi port penuh

Dispatcher masih menyaring berdasarkan ID karakter; operasi 12/13/18 dan banyak
operasi lainnya masih tanpa efek, kontrol 14/15 terbatas selector 1, opcode 23
terbatas koridor UJ tertentu, voice belum setara, projectile 27–29 belum dipetakan.
CPK masih satu path Tobi; descriptor kondisi dan membership ougi masih generated
untuk data lama. Factory generik, seluruh parameter API, kepemilikan event,
lifecycle timer/actor, kamera, audio, serta multi-mod belum selesai diintegrasikan.

Tidak ada dasar untuk menyebut binary ini “full API” atau meminta pengguna
memasang ini sebagai hasil selesai. `PORT_STATUS.json` mempertahankan status false.

## Mengulangi pemeriksaan

Workflow `verify-port-foundation.yml` menyediakan build/toolchain yang dipin.
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
