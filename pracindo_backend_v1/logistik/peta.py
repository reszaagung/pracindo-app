"""
Jarak dan rute — logistik/peta.py

Dua lapis, sengaja dipisah:

    jarak_haversine()   garis lurus antar koordinat. Tidak butuh layanan luar,
                        tidak pernah gagal, tapi selalu lebih pendek dari
                        jarak jalan sebenarnya.

    Penyedia rute       jarak dan waktu tempuh nyata dari layanan peta.
                        Belum diputuskan mana yang dipakai (PRD Logistik
                        §9.2), jadi antarmukanya saja yang disiapkan.

Selama penyedia belum dipilih, sistem memakai haversine dikali faktor koreksi.
Itu perkiraan kasar dan TIDAK boleh dipakai untuk menagih ongkos ke pelanggan
-- cukup untuk mengurutkan perhentian dan memberi gambaran biaya internal.
"""
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

# Jarak jalan di kota Indonesia rata-rata 1,3-1,4x garis lurus. Angka ini
# tebakan yang jujur, bukan hasil kalibrasi -- ganti begitu ada data nyata.
FAKTOR_JALAN = Decimal('1.35')

# Kecepatan rata-rata termasuk berhenti, macet, dan waktu bongkar.
KECEPATAN_KMJAM = Decimal('25')

RADIUS_BUMI_KM = 6371.0


def jarak_haversine(lat1, lng1, lat2, lng2):
    """Jarak garis lurus dalam km. Mengembalikan Decimal 2 desimal."""
    if None in (lat1, lng1, lat2, lng2):
        return Decimal('0.00')

    p1, p2 = radians(float(lat1)), radians(float(lat2))
    dp = radians(float(lat2) - float(lat1))
    dl = radians(float(lng2) - float(lng1))

    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    km = 2 * RADIUS_BUMI_KM * asin(sqrt(a))
    return Decimal(str(round(km, 2)))


def jarak_perkiraan(lat1, lng1, lat2, lng2):
    """Jarak jalan perkiraan: haversine dikali faktor koreksi."""
    lurus = jarak_haversine(lat1, lng1, lat2, lng2)
    return (lurus * FAKTOR_JALAN).quantize(Decimal('0.01'))


def menit_perkiraan(jarak_km):
    if not jarak_km:
        return 0
    return int((Decimal(jarak_km) / KECEPATAN_KMJAM) * 60)


def urutkan_terdekat(titik_awal, titik):
    """
    Urutan usulan dengan heuristik tetangga terdekat.

    Bukan solusi optimal, dan memang tidak diniatkan begitu. Optimasi rute
    penuh (VRP) berlebihan untuk armada sekecil ini, dan hasilnya sering
    kalah dari kurir yang hafal kondisi jalan. Yang berguna adalah usulan
    awal yang masuk akal -- keputusan akhir tetap di orang.

    titik_awal: (lat, lng) atau None
    titik: [{'id':..., 'lat':..., 'lng':...}]
    Return: daftar id sesuai urutan usulan.
    """
    sisa = [t for t in titik if t.get('lat') is not None and t.get('lng') is not None]
    tanpa_koordinat = [t['id'] for t in titik if t not in sisa]

    hasil = []
    kini = titik_awal
    while sisa:
        if kini is None:
            berikut = sisa[0]
        else:
            berikut = min(
                sisa,
                key=lambda t: jarak_haversine(kini[0], kini[1], t['lat'], t['lng']),
            )
        hasil.append(berikut['id'])
        kini = (berikut['lat'], berikut['lng'])
        sisa.remove(berikut)

    # Perhentian tanpa koordinat ditaruh di akhir, bukan dibuang.
    return hasil + tanpa_koordinat
