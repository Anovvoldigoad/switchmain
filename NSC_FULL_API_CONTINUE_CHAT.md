# NSC Full ModdingAPI Switch — checkpoint dan prompt lanjutan

Update lanjutan: validasi opsional companion raw176 (hash, ukuran, jumlah, dan nama setiap indeks) sudah diimplementasikan di `tools/portlib/condition_companion.py`. Lihat bagian terbaru `PORTING_PROGRESS.md`. Packaging runtime/CPK dan semantik nilai raw masih pending. Prompt MVP di bawah adalah scope keseluruhan; jangan mengulang validator yang sudah ada.

Checkpoint runtime native yang sudah diuji: **a51dd1494d0c0d793a76fd5f43ce7ae991744cf5**.
Status: **IMPLEMENTATION_INCOMPLETE — belum full API, belum siap uji gameplay**.
Dokumen ini memindahkan konteks pekerjaan; tidak mengubah model, alat, atau kuota akun.

## Cara lanjut dari Android

1. Buka percakapan baru di Chat, atau buat Project bernama **NSC Full ModdingAPI Switch 170** jika fitur itu tersedia. Lampirkan dokumen ini.
2. Pilih **GPT Astra jika benar-benar tersedia** di pemilih model pada mode tersebut. Nama model dalam prompt tidak mengganti model yang sedang dipakai.
3. Hubungkan/pilih GitHub jika tersedia. Salin bagian **Prompt eksplisit** di bawah sebagai pesan pertama.
4. Jika chat tidak dapat mengedit repo atau menjalankan build, jangan menerima klaim bahwa kode sudah dibangun. Gunakan GitHub Actions melalui akses yang tersedia, atau lanjutkan eksekusi di lingkungan yang memiliki alat tersebut. Analisis dan penulisan patch tetap harus membedakan hasil belum diuji.

Belum ada ChatGPT Project yang dibuat atau percakapan yang dipindahkan oleh sesi pembuat checkpoint ini. Dokumen ini dapat diunggah secara manual. Model, alat, reasoning settings, dan batas penggunaan berbeda antarproduk/versi; checkpoint tidak menjamin kemampuan setara Work dan tidak menghapus batas penggunaan. Rujukan resmi: https://learn.chatgpt.com/docs/model-selection dan https://learn.chatgpt.com/docs/models .

## Sumber kebenaran

| Item | Lokasi / nilai |
| --- | --- |
| Repository | https://github.com/Anovvoldigoad/switchmain |
| Branch aktif | `port/full-api-v170` |
| Kode terakhir terverifikasi | `a51dd1494d0c0d793a76fd5f43ce7ae991744cf5` |
| Parent implementasi | `86cf8e9f7a9cb0b90cb136a90c6c4afacb9f22bf` |
| CI kode tersebut | https://github.com/Anovvoldigoad/switchmain/actions/runs/41878269717 |
| Hasil CI yang diperiksa | `completed / success`; job `126743663223`, seluruh langkah build/test lulus |
| Status dan kekurangan | `PORT_STATUS.json` |
| Penjelasan implementasi | `PORTING_PROGRESS.md` |
| Bukti lokal komponen | `reports/port_foundation/*.json` |
| Build/test yang dapat diulang | `.github/workflows/verify-port-foundation.yml` |
| Checkpoint terstruktur | `handoff/checkpoint.json` |
| Checkpoint sebelumnya di Storm Modding Lab | `c7ca5be9-1c45-47c1-84d2-312b33f0bf4f` |

CI di atas benar-benar diperiksa untuk SHA a51dd14. Commit dokumentasi yang membawa dokumen ini bukan perubahan runtime dan tidak menggantikan identitas kode yang sudah diuji. Saat melanjutkan, baca HEAD aktual: perubahan setelah checkpoint harus ditinjau sebelum digunakan. Dokumen historis berjudul R181/R183/FULL tidak membuktikan branch ini sudah full API atau playable.

## Prompt eksplisit — salin seluruh blok ini

```text
Lanjutkan implementasi proyek NSC_FULL_MODDINGAPI_SWITCH_170 dari checkpoint terlampir. Kerjakan perubahan nyata dan verifikasi hasilnya; jangan berhenti pada rencana atau meminta saya mengetik "lanjut" setiap tahap. Saya mengizinkan edit kode, tes, build, dan upload ke repo/branch proyek yang sudah disebutkan. Hindari menimpa perubahan terbaru; periksa HEAD sebelum publish.

TARGET AKHIR TIDAK BERUBAH:
Port seluruh fungsi PC NSC ModdingAPI ke Naruto Storm Connections Switch 1.70, termasuk dukungan mod new character slot dan dependency/resource lifecycle, untuk workflow Android dan emulator Uzuy/Eden/Yuzu serta emulator lain yang nanti benar-benar diuji. Bahasa teks English, voice Japanese. Jangan mengganti target menjadi sekadar clone Naruto, replacement slot, lima entri Tobi hardcoded, converter saja, atau boot probe. MVP berikut adalah milestone menuju target penuh, bukan pengurangan definisi selesai.

MULAI DARI BUKTI:
1. Nyatakan kemampuan eksekusi yang benar-benar tersedia: baca/tulis GitHub, akses file biner, shell/compiler atau GitHub Actions, serta log/artifact. Jangan mengaku memakai Astra jika pilihan model tidak menetapkannya. Jangan mengaku telah menguji bila tidak ada eksekusi yang bisa diverifikasi.
2. Buka Anovvoldigoad/switchmain branch port/full-api-v170. Baca NSC_FULL_API_CONTINUE_CHAT.md, handoff/checkpoint.json, PORT_STATUS.json, PORTING_PROGRESS.md, workflow verify-port-foundation.yml, dan source/test terkait tugas berikutnya.
3. Checkpoint kode teruji adalah a51dd1494d0c0d793a76fd5f43ce7ae991744cf5. Run 41878269717 completed/success telah diperiksa, tetapi bukan gameplay PASS. Bandingkan HEAD terbaru dengan checkpoint; jangan reset atau force-push perubahan orang lain.
4. Jangan mengasumsikan file scratch sesi lama masih ada. Pulihkan source dari GitHub. Cari input pengguna yang diperlukan dengan nama/ID checkpoint, lalu verifikasi hash. Jangan meminta ulang input yang masih dapat diakses. Jika bukti kritis tidak tersedia, lanjutkan pekerjaan independen dan jelaskan tepatnya input yang kurang.

MVP BERIKUT: PASANGAN CONDITION DESCRIPTOR + RAW CONDITION YANG KONSISTEN
Masalah konkret: compiler sekarang menerima 512..1024 descriptor PC raw112 dan mempertahankan 512 descriptor native Switch; data conditionprm raw176 terpisah belum dipaketkan bersama. Tobi.zip.cpk berisi raw512, sedangkan romfs.zip.cpk berisi raw517. Mengaktifkan lima descriptor tambahan dengan raw512 bukan paket valid.

Kerjakan berurutan:
A. Telusuri pembaca/penulis PC yang dipin, pembaca Switch, dan data input sebenarnya. Buktikan hubungan ordinal descriptor dengan raw176 serta sumber urutan/identitasnya. Count yang sama saja tidak membuktikan urutan sama. Jangan menebak layout atau menambahkan padding sebagai pengganti record asli.
B. Implementasikan validasi pasangan input dan packaging yang menjaga urutan tersebut. Validasi NUCC/chunk bounds, jumlah record, hash input, baseline, duplikasi/nama bila field tersebut memang ada, dan semua referensi yang dapat dibuktikan. Jika identitas urutan tidak dapat dibuktikan dari file, gunakan provenance/manifest yang memiliki dasar terverifikasi; jangan menyebut hash sebagai bukti semantik.
C. Tolak mismatch 517 descriptor vs 512 raw sebelum menghasilkan paket yang terlihat siap dipasang. Tolak input terpotong, overflow, baseline yang tidak didukung, urutan tidak terbukti, serta overwrite sumber. Jangan memasang descriptor saja lalu berharap game mengisi data hilang.
D. Integrasikan pasangan itu dengan profile factory/CPK dan konversi Event236 yang sudah ada. Preserve byte yang tidak ditargetkan. Pastikan semua urutan konfigurasi profil yang didukung menghasilkan keluaran yang konsisten. Jangan memilih CPK hanya dari nama zip.
E. Tambahkan regression test yang menguji kegagalan nyata dan native consumer/lifecycle yang terdampak. Jalankan build dan tes yang relevan, kemudian workflow fondasi. Simpan report dan SHA input/output. Sebutkan bagian yang distub/dimodelkan.
F. Audit alokasi, reload, release/destructor, async bind, precedence, dan effect/resource dependency yang terkait sebelum menyebut hasilnya kandidat gameplay. Jika milestone hanya menyelesaikan pasangan/packaging, status full_moddingapi dan ready_for_gameplay_test tetap false.

KRITERIA LULUS MVP KOMPONEN:
- Pasangan descriptor/raw diverifikasi dengan bukti ordinal, bukan hanya jumlah.
- Native prefix Switch utuh, termasuk Sakura index103 aura107 (PC baseline aura5).
- Kasus salah pasangan, reorder, truncation dan hash salah ditolak; tidak ada output parsial yang diberi label siap pakai.
- Input sumber dan byte tak ditargetkan utuh; profile composition dan regresi terkait lulus dengan bukti.
- Kode, tes, report, keterbatasan dan checkpoint tersimpan pada GitHub dengan commit yang dapat dibuka.
Lulus komponen tidak berarti seluruh port selesai atau game sudah playable.

SETELAH MVP, LANJUTKAN TARGET PENUH:
Tutup gap pada PORT_STATUS.json: sembilan pembaca parameter generik tersisa; 53 selector factory yang belum terbukti; operasi MovesetPlus tersisa; filter legacy UJ/Event121; lifetime actor/P64; discovery/merge/async completion/unbind CPK; compressed PRM; audio/effect/resource lifecycle; integrasi multi-mod dan new slot. Jangan aktifkan opcode dengan field native yang belum terbukti. Kerjakan berdasarkan source PC dan instruksi/data Switch nyata, bukan tebakan alamat/ID.

ATURAN MUTLAK:
- STATIC_VERIFIED, EMULATED_WITH_STUBS, BUILD_PASS dan GAME_TESTED adalah bukti berbeda. Game penuh belum dijalankan pada build checkpoint ini.
- 1024 batas PRM/condition bukan bukti 1024 slot karakter berfungsi.
- Event236 tanpa marker adalah native enemy-hide; marker API adalah uint16 0x4E53 pada record+0x2A. Jangan kembali ke heuristik charID>280.
- conditionprmManager raw112, descriptor runtime32, profile record80, raw conditionprm176 adalah format berbeda.
- Gunakan exact SHA gate main, fingerprint hook, bounded allocations, dan pertahankan baseline. Jangan abaikan guard demi lolos boot.
- Default factory/CPK/condition profiles kosong. Jangan menyebut module default sebagai Tobi siap main.
- Jangan mengubah aset Boruto/Isshiki/Minato atau menggabungkan proyek lain.
- Jangan mengaku bekerja di background setelah respons selesai jika tidak ada job nyata yang berjalan. Jika batas alat/kuota menghentikan eksekusi, simpan checkpoint yang memuat commit, bukti, blocker dan langkah tepat berikutnya.

OUTPUT YANG SAYA MAU:
Perubahan nyata yang disimpan, hasil tes yang benar, dan status jujur. Penjelasan ringkas dalam Bahasa Indonesia. Tidak perlu meminta izin ulang untuk pekerjaan yang sudah diotorisasi. Jangan pernah ngasal.
```

## Fakta teknis yang wajib dipertahankan

- Source PC: `TheLeonX/NSC-ModManager@276116ebf5ba398a867793cb02ee6c33c0927645`; runtime terkait `TheLeonX/UltimateStormAPI@a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`. Runtime ditelusuri sebagai dependency manager, bukan diasumsikan otomatis setara seluruh DLL distribusi.
- `ConditionPrmManager.cpp` blob `3e7aacadca117b56e43f1a5c1d04cdd02aed7b1f`. Baseline PC raw512x112 blob `0e7133223f10eb2dbbb39d2166fdca9352e84c3e`, SHA256 `fae4c1e1a510f895a7b9b9acbf5b710e7472e9b47f3471087dd4b1c97b7b86c5`.
- Input R180 main dalam repo: `original/atmosphere/contents/0100FA10190A0000/exefs/main`, SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`. Jangan mengganti dengan main lama yang hash-nya berbeda.
- Stock text hasil rekonstruksi terverifikasi: `f6ec83dad4537b0fa53cf707c10f48a438117905581e2ed3f42cf3cf29a731d7`. Gunakan `tools/prepare_test_images.py`; jangan menebak patch balik.
- Profile condition 41024 byte berisi hingga 512 tambahan. Baseline 512 dipertahankan; angka ini menghitung kondisi, bukan slot karakter.
- Native descriptor table `0x20736c8`, getter `0x754a80`, raw getter `0x754aa0`. Field descriptor: reaction+8, state+12, icon+16, status+20, aura+24. Instruksi consumer di test mengikat interpretasi ini.
- Empat bound lookup `0x7774dc`, `0x777770`, `0x777938`, `0x777a6c` berasal dari jumlah profil yang sama. Name resolver `0x777758`, hash resolver `0x777920`, CRC native `0x12154d0`.
- `tools/compile_condition_profile.py` hanya mengompilasi descriptor/profil NSO; tidak memaketkan raw176 atau membuktikan efek/gameplay. Compiler menolak edit/reorder baseline PC dan nama tambahan yang bertabrakan.
- Tobi raw512 XFBIN SHA256 `ee8bea3caab274333b466d3e44fcf5129249dbb649c1dd0ddeecb983e948d123`.
- Varian romfs raw517 XFBIN SHA256 `b92c71cb791dd6b2b25f18e2822da97c723a4e8a75b4222dff4f0bd546c710ce`.
- Pada kedua arsip, path entri adalah `data/spc/conditionprm.bin.xfbin`. Parse CPK dengan `portlib.cpk_events.entries`, lalu `portlib.prm_events.binary_chunks`; count uint32 little-endian pada binary payload+4, panjang payload yang diamati `8 + count*176`. Hubungan semantic/order masih perlu dibuktikan.

## Bukti yang sudah ada

Build ARM64 lokal dan CI a51dd14 lulus. Tes kondisi menolak 41037 profil rusak dan 9 tabel PC invalid; menjalankan 2578 kasus getter, 124 lookup, 135 field consumer, 4 konfigurasi installer, dan 21 kegagalan fingerprint sebelum hook. Komposisi tiga profil lolos dalam enam urutan. Regresi bootstrap/storage/factory/events/controls/CPK/binary lulus. Tes actual Tobi PRM adalah bukti lokal tersendiri di report, bukan input yang dijalankan oleh semua langkah CI.

ELF lokal: `bba662ab22e0b4993ce5a3163d5a4504a8f8fff016ac434949cdb5632237c5aa`.
NSO lokal: `d9d2c43d3270d413e71a4472fabbc8403a634ab37c2ec30381b1ff40595778ef`.
Hash build lokal bukan janji bahwa setiap build baru memiliki hash sama; laporkan hash keluaran aktual dan cocokkan segmen ELF/NSO.

Hook publication, allocator/libc dan sebagian konteks caller/OS dimodelkan. Resource loading, efek, konstruksi/destruksi actor secara penuh, serta game di emulator belum terverifikasi. Tidak ada paket instalasi baru dalam checkpoint ini.

## Memulihkan workspace tanpa sesi Work lama

Source dan sebagian input tes dapat dipulihkan dari GitHub; `analysis/`, toolchain lokal, dan output build pada sesi lama bukan penyimpanan yang harus diasumsikan tersedia. Clone branch melalui akses GitHub yang tersedia. Pada Termux yang sudah memiliki git:

```bash
git clone --branch port/full-api-v170 --single-branch https://github.com/Anovvoldigoad/switchmain.git NSC_FULL_API_SWITCH_170
cd NSC_FULL_API_SWITCH_170
git log -1 --oneline
git status --short
sha256sum -c SOURCE_SHA256SUMS.txt
```

Periksa perubahan setelah SHA checkpoint sebelum menjalankan source baru. Manifest memeriksa byte file, bukan keabsahan semantik atau gameplay. Workflow di GitHub adalah urutan build/test kanonis. Image build dipin ke `devkitpro/devkita64@sha256:82575ea78651b530b2e232bb3799cfd1fe331514e053d5f724bb4b28191fb79d`; exlaunch dipin ke `229bbd659b4e8d14077baec53f3e43e1eb3c196a`. Jangan menyuruh pengguna Android menjalankan Docker lokal. Packer Python standar dapat dipakai di Termux; build native dan test ARM64 membutuhkan lingkungan yang benar.

Input pengguna yang pernah tersedia, untuk pencarian kembali jika diperlukan:

| Nama | Referensi persisten yang diketahui |
| --- | --- |
| NSC-RUNTIME-R180-dpad-native-gate-rollback.zip | Library ID `libfile_4790aaa8f068819196dd7c29c5c0bacd` |
| NSC_SWITCH_PORT_CHECKPOINT_BELUM_SIAP_UJI.zip | Library ID `libfile_01a8449d8a648191bba13eabed7ec725` |
| ANALISIS_FULL_MODDINGAPI_SWITCH_R180.zip | Library ID `libfile_ff1f70b4cfa48191845fa4bbd34b2160` |
| Tobi.zip / romfs.zip / conditionprmManager.xfbin | Cari nama/aset terkait melalui akses file pengguna; ID tidak diketahui di checkpoint ini |

Daftar ini membantu menemukan file; bukan klaim bahwa seluruh isi arsip lama sudah sesuai HEAD. Baca dan hash ulang input yang akan dipakai. Jangan mendistribusikan ulang seluruh aset game untuk membuat checkpoint kecil.

## Setelah setiap milestone

Simpan kode/test/report dan status gap ke branch dengan commit baru; periksa CI untuk SHA yang benar. Perbarui checkpoint dengan input/output hashes, apa yang benar-benar diuji, apa yang belum terbukti, serta langkah berikut yang bisa langsung dieksekusi. Pertahankan scope full API walaupun milestone kecil sudah lulus. Jika gameplay belum diuji, tandai demikian secara eksplisit.
