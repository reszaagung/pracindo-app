# Modul Logistik — catatan pemasangan

Sepuluh berkas, tahap 1 dan 2 dari rencana lima tahap di PRD.

```bash
# 1. Tambahkan Role.KURIR dulu — lihat PATCH-staff-user.md
# 2. Daftarkan app dan rutenya
#    settings: INSTALLED_APPS += ['logistik']
#    urls:     path('api/logistik/', include('logistik.urls')),
python manage.py makemigrations logistik
python manage.py migrate
python manage.py test logistik
```

Butuh `Pillow` untuk ImageField.

## Berkas

| Berkas | Isi |
|---|---|
| `models.py` | Kendaraan, TarifOngkos, Pengiriman, Perhentian, JejakPosisi, BuktiTerima, Retur |
| `services.py` | seluruh logika bisnis |
| `integrasi_warehouse.py` | **satu-satunya** sambungan ke warehouse |
| `peta.py` | jarak haversine, heuristik urutan |
| `serializers.py`, `views.py`, `urls.py`, `permissions.py` | lapisan API |
| `admin.py`, `tests.py` | |

## Batas modul, ditegakkan bukan didokumentasikan

**Logistik tidak pernah menulis stok.** Tidak lewat model, tidak lewat
`inventory.services`. Warehouse yang menulis; logistik memicu lewat
`integrasi_warehouse`.

Empat tes di `TidakMenulisStokTest` menjaga ini. Tambalan warehouse di tes
sekaligus jadi alat ukur: kalau kode logistik diam-diam menulis stok sendiri,
panggilan ke tambalan tidak tercatat dan tesnya gagal.

**Rujukan ke Distribusi memakai integer, bukan ForeignKey.** Aturan impor
satu arah melarang logistik mengimpor model warehouse.

## Yang harus disediakan `warehouse`

Empat fungsi di `warehouse/services.py`. Kontrak lengkapnya ada di kepala
`integrasi_warehouse.py`:

```
distribusi_siap_kirim(entitas_id=None) -> list[dict]
rincian_distribusi(distribusi_id)      -> dict
tandai_terkirim(distribusi_id, waktu, oleh)
kembalikan_stok(distribusi_id, alasan, oleh)
```

Selama belum ada, endpoint yang membutuhkannya menjawab **503** dengan pesan
yang menyebut fungsi mana yang kurang. Bukan 400, karena ini bukan kesalahan
pengguna. Dan bukan daftar kosong, karena layar perakitan akan terlihat
"tidak ada yang perlu dikirim" padahal sebenarnya belum tersambung.

Sisa modul tetap jalan penuh: pengiriman yang sudah dirakit bisa berangkat,
dilacak, difoto, dan diretur.

## Endpoint

| Method | Path | Catatan |
|---|---|---|
| GET/POST | `pengiriman/` | POST merakit dari distribusi |
| GET | `pengiriman/{id}/` | dengan perhentian dan bukti |
| PUT/PATCH/DELETE | `pengiriman/{id}/` | 405 |
| GET | `pengiriman/tugas-saya/` | layar utama kurir, array polos |
| POST | `pengiriman/{id}/urutkan/` | urutan manual menimpa usulan |
| POST | `pengiriman/{id}/hitung-rute/` | `{pakai_usulan}` |
| POST | `pengiriman/{id}/berangkatkan/` | |
| POST | `pengiriman/{id}/batalkan/` | hanya DISIAPKAN |
| POST | `pengiriman/{id}/posisi/` | hanya saat BERANGKAT |
| GET | `pengiriman/{id}/jejak/` | |
| POST | `pengiriman/{id}/perhentian/{hid}/sampai/` | |
| POST | `pengiriman/{id}/perhentian/{hid}/bukti/` | multipart, foto |
| POST | `pengiriman/{id}/perhentian/{hid}/retur/` | multipart |
| GET | `retur/` | |
| POST | `retur/{id}/setujui/` | hanya Supervisor |
| GET/POST | `kendaraan/` | |
| GET | `distribusi-tersedia/` | dari warehouse |

Aksi bukti dan retur menerima header `Idempotency-Key`. Antrean offline
klien mobile harus memakai kunci yang sama saat mengirim ulang.

## Keputusan yang saya ambil

**Nomor pengiriman per entitas armada, bukan per entitas barang.** Satu
perjalanan bisa membawa muatan beberapa badan hukum — stiker sudah menutup
klaimnya masing-masing, jadi tidak ada yang perlu diselesaikan. `entitas`
pada Pengiriman adalah pemilik armada.

**Usulan rute tidak menimpa urutan.** `urutan_usulan` disimpan terpisah dari
`urutan`. Setelah beberapa bulan, selisih keduanya menunjukkan apakah usulan
sistem berguna atau selalu diabaikan.

**Bukti terima tidak mensyaratkan status BERANGKAT.** Foto dari antrean
offline bisa tiba berjam-jam setelah perjalanan selesai. Yang disyaratkan
hanya pengirimannya belum dibatalkan.

**Posisi ditolak di service, bukan sekadar tidak dikirim klien.** Aplikasi
yang lupa mematikan pelacakan akan terus mengirim, dan merekamnya berarti
melacak kurir di luar jam bertugas.

**`peta.py` memakai haversine × 1,35.** Cukup untuk mengurutkan perhentian
dan memberi gambaran biaya internal. **Tidak boleh dipakai menagih ongkos ke
pelanggan.** Ganti dengan layanan peta sungguhan setelah PRD §9.2 diputuskan
— antarmukanya sudah siap.

## Belum dikerjakan

Tahap 3–5 dari PRD: layanan peta sungguhan, aplikasi kurir Android, dan
penanganan retur barang rusak yang menunggu keputusan PRD §9.4.

`bersihkan_jejak_lama()` sudah ada di services tapi belum dijadwalkan —
butuh cron atau Celery beat, 30 hari sebagai default.
