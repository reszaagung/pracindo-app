# Perubahan yang dibutuhkan di `staff_user`

Peran KURIR belum ada. Tanpa ini, `logistik/permissions.py` gagal impor.

## 1. `staff_user/models.py`

Tambahkan ke `class Role(models.TextChoices)`:

```python
KURIR = 'KURIR', 'Kurir'
```

Taruh setelah `SALES`, sebelum `STAFF`.

## 2. `staff_user/permissions.py`

Ubah satu baris di `AKSES_MODUL`:

```python
'logistik': [Role.GUDANG, Role.SALES, Role.KURIR],
```

Kurir **tidak** ditambahkan ke `'dashboard'`. Portal kurir adalah daftar
tugasnya, bukan kartu modul — dan memberi akses dashboard berarti memberi
pintu ke tempat yang tidak dia butuhkan.

## 3. Migrasi

```bash
python manage.py makemigrations staff_user
```

`Role` adalah `choices`, jadi migrasinya hanya mengubah metadata field.
Tidak ada data lama yang perlu diisi ulang.

## Kenapa akses modul saja tidak cukup

`AKSES_MODUL` menjawab "boleh masuk modul logistik?". Dia tidak menjawab
"baris yang mana". Kurir yang punya akses modul tanpa penyaringan queryset
bisa membaca seluruh perjalanan, termasuk alamat semua pelanggan dan
perjalanan rekannya.

Penyaringannya ada di `logistik/permissions.batasi_ke_kurir()`, dipanggil
dari `get_queryset()` — bukan dari `has_object_permission`, karena izin objek
di DRF tidak berlaku untuk endpoint list. Ada tes yang menjaga ini di
`CakupanKurirTest`.
