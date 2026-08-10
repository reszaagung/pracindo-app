"""
Pemetaan kejadian bisnis ke baris jurnal — akunting/posting_rules.py

Aturan disimpan sebagai DATA, bukan percabangan if di views.py.
Menambah jenis transaksi = menambah entri dict, bukan mengubah logika.

Format: (kode_akun, sisi, nama_field_nilai)
    sisi 'D' = debit, 'K' = kredit

Setiap aturan HARUS seimbang: jumlah nilai sisi D sama dengan sisi K.
Kalau tidak, trigger database akan menolak seluruh transaksi saat COMMIT.

Kalau nanti Supervisor perlu mengubah pemetaan akun sendiri, pindahkan
dict ini ke tabel AturanPosting. Untuk sekarang dict sudah cukup --
jangan over-engineer.
"""


AKUN = {
    'KAS':          '1100',
    'PIUTANG':      '1200',
    'PERSEDIAAN':   '1300',
    'RESIPROKAL_D': '1800',   
    'HUTANG':       '2100',
    'GRNI':         '2190',   
    'RESIPROKAL_K': '2800',   
    'PENJUALAN':    '4100',
    'HPP':          '5100',
    'SELISIH_BELI': '5900',
    'BEBAN_UMUM':   '6100',
}

ATURAN = {

    'AUDIT_GUDANG': [
        (AKUN['PERSEDIAAN'], 'D', 'nilai_terima'),
        (AKUN['GRNI'],       'K', 'nilai_terima'),
    ],

    'FAKTUR_MASUK': [
        (AKUN['GRNI'],   'D', 'nilai_faktur'),
        (AKUN['HUTANG'], 'K', 'nilai_faktur'),
    ],

    'FAKTUR_LEBIH': [
        (AKUN['SELISIH_BELI'], 'D', 'selisih'),
        (AKUN['GRNI'],         'K', 'selisih'),
    ],

    'FAKTUR_KURANG': [
        (AKUN['GRNI'],         'D', 'selisih'),
        (AKUN['SELISIH_BELI'], 'K', 'selisih'),
    ],

    'BAYAR_HUTANG': [
        (AKUN['HUTANG'], 'D', 'nominal'),
        (AKUN['KAS'],    'K', 'nominal'),
    ],

    'RETUR_BELI': [
        (AKUN['GRNI'],       'D', 'nilai_retur'),
        (AKUN['PERSEDIAAN'], 'K', 'nilai_retur'),
    ],

    'PENJUALAN': [
        (AKUN['PIUTANG'],    'D', 'nilai_jual'),
        (AKUN['PENJUALAN'],  'K', 'nilai_jual'),
        (AKUN['HPP'],        'D', 'hpp'),
        (AKUN['PERSEDIAAN'], 'K', 'hpp'),
    ],

    'TERIMA_PIUTANG': [
        (AKUN['KAS'],     'D', 'nominal'),
        (AKUN['PIUTANG'], 'K', 'nominal'),
    ],

    'BEBAN_KAS': [
        (AKUN['BEBAN_UMUM'], 'D', 'nominal'),
        (AKUN['KAS'],        'K', 'nominal'),
    ],


    'KLAIM_HUTANG': [
        (AKUN['PERSEDIAAN'],   'D', 'nilai'),
        (AKUN['RESIPROKAL_K'], 'K', 'nilai'),
    ],
    'KLAIM_PIUTANG': [
        (AKUN['RESIPROKAL_D'], 'D', 'nilai'),
        (AKUN['PERSEDIAAN'],   'K', 'nilai'),
    ],
}
