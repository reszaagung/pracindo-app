"""
Seed entitas dan grup bahan.

Data ini bukan sekadar contoh -- CounterDokumen.berikutnya() memakai
Entitas.kode untuk membentuk nomor dokumen, jadi tanpa baris ini tidak ada
satu pun transaksi yang bisa dibuat.

Karena itu tempatnya di migrasi, bukan di shell: setiap mesin dan setiap
server mendapat data yang sama, otomatis.

CATATAN: `kode` masuk ke setiap nomor dokumen. Setelah ada transaksi,
nilai itu tidak boleh diubah lagi.

Simpan sebagai:
    core/migrations/0003_seed_entitas.py
"""
from django.db import migrations

GRUP = [
    ('PT',      'Pool bahan PT'),
    ('BERSAMA', 'Pool bahan bersama'),
]

ENTITAS = [
    # kode,      nama,                       jenis,         grup
    ('PT',      'PT Pracindo Jaya Mandiri', 'BADAN_HUKUM', 'PT'),
    ('CV',      'CV Marsini',               'BADAN_HUKUM', 'BERSAMA'),
    ('AGUS',    'Agus',                     'PERORANGAN',  'BERSAMA'),
    ('MARSINI', 'Marsini',                  'PERORANGAN',  'BERSAMA'),
]


def tanam(apps, schema_editor):
    GrupBahan = apps.get_model('core', 'GrupBahan')
    Entitas = apps.get_model('core', 'Entitas')

    grup = {}
    for kode, nama in GRUP:
        obj, _ = GrupBahan.objects.get_or_create(kode=kode, defaults={'nama': nama})
        grup[kode] = obj

    for kode, nama, jenis, kode_grup in ENTITAS:
        Entitas.objects.get_or_create(
            kode=kode,
            defaults={
                'nama': nama,
                'jenis': jenis,
                'grup_bahan': grup[kode_grup],
            },
        )


def cabut(apps, schema_editor):
    Entitas = apps.get_model('core', 'Entitas')
    GrupBahan = apps.get_model('core', 'GrupBahan')
    Entitas.objects.filter(kode__in=[e[0] for e in ENTITAS]).delete()
    GrupBahan.objects.filter(kode__in=[g[0] for g in GRUP]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(tanam, cabut),
    ]
