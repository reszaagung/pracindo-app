"""
Bagan akun awal.

Kode akun di sini WAJIB cocok dengan dict AKUN di posting_rules.py.
Kalau tidak, posting() gagal di baris pertama dengan pesan akun hilang.

COA dipakai bersama keempat entitas. Saldo per entitas didapat dari
filter jurnal, bukan dari akun yang digandakan -- empat COA terpisah
berarti empat daftar yang harus dijaga tetap sinkron.

Simpan sebagai: akunting/migrations/0005_seed_coa.py
"""
from django.db import migrations

# (kode, nama, tipe, parent, boleh_diposting)
AKUN = [
    ('1000', 'ASET',                        'ASET',       None,   False),
    ('1100', 'Kas dan Bank',                'ASET',       '1000', True),
    ('1200', 'Piutang Usaha',               'ASET',       '1000', True),
    ('1300', 'Persediaan',                  'ASET',       '1000', True),
    ('1800', 'Piutang Antar Entitas',       'ASET',       '1000', True),

    ('2000', 'KEWAJIBAN',                   'KEWAJIBAN',  None,   False),
    ('2100', 'Hutang Usaha',                'KEWAJIBAN',  '2000', True),
    ('2190', 'GRNI - Barang Diterima Belum Difaktur', 'KEWAJIBAN', '2000', True),
    ('2800', 'Hutang Antar Entitas',        'KEWAJIBAN',  '2000', True),

    ('3000', 'EKUITAS',                     'EKUITAS',    None,   False),
    ('3100', 'Modal',                       'EKUITAS',    '3000', True),
    ('3900', 'Laba Ditahan',                'EKUITAS',    '3000', True),

    ('4000', 'PENDAPATAN',                  'PENDAPATAN', None,   False),
    ('4100', 'Penjualan',                   'PENDAPATAN', '4000', True),

    ('5000', 'HARGA POKOK',                 'BEBAN',      None,   False),
    ('5100', 'Harga Pokok Penjualan',       'BEBAN',      '5000', True),
    ('5900', 'Selisih Harga Pembelian',     'BEBAN',      '5000', True),

    ('6000', 'BEBAN OPERASIONAL',           'BEBAN',      None,   False),
    ('6100', 'Beban Umum',                  'BEBAN',      '6000', True),
    ('6200', 'Beban Gaji',                  'BEBAN',      '6000', True),
    ('6300', 'Beban Penyusutan',            'BEBAN',      '6000', True),
]


def tanam(apps, schema_editor):
    Akun = apps.get_model('akunting', 'Akun')

    # Header dulu supaya FK parent selalu ketemu.
    for kode, nama, tipe, parent, posting in AKUN:
        if parent is None:
            Akun.objects.get_or_create(
                kode=kode,
                defaults={'nama': nama, 'tipe': tipe, 'boleh_diposting': posting},
            )
    for kode, nama, tipe, parent, posting in AKUN:
        if parent is not None:
            Akun.objects.get_or_create(
                kode=kode,
                defaults={
                    'nama': nama, 'tipe': tipe, 'boleh_diposting': posting,
                    'parent': Akun.objects.get(kode=parent),
                },
            )


def cabut(apps, schema_editor):
    Akun = apps.get_model('akunting', 'Akun')
    kode = [a[0] for a in AKUN]
    Akun.objects.filter(kode__in=kode, parent__isnull=False).delete()
    Akun.objects.filter(kode__in=kode).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('akunting', '0004_trigger_jurnal_seimbang'),
    ]

    operations = [
        migrations.RunPython(tanam, cabut),
    ]
