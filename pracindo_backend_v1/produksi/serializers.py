"""
Serializers Produksi — produksi/serializers.py

KLIEN TIDAK PERNAH MENGIRIM HARGA

    Payload hanya memuat pengenal dan qty. Harga dan nilai dihitung
    server dari saldo saat posting. Menerima harga dari klien berarti
    menerima harga yang sudah basi, atau yang dikarang -- dan dua tempat
    yang menghitung hal sama akan berbeda; pertanyaannya hanya kapan.

DUPLIKAT DITOLAK SEBELUM VALIDASI SALDO

    Dua baris dengan sumber sama masing-masing lolos pemeriksaan
    terhadap saldo PENUH, dan bersama-sama menarik dua kali lipat dari
    yang ada. Constraint unik di DB adalah backstop-nya; ini pertahanan
    pertamanya, dan yang memberi pesan yang bisa dibaca operator.
"""
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import (
    Batch, BatchInputRaw, StatusBatch, Tangki, TransferWip, nomor_baru,
)

QTY_MIN = Decimal("0.001")


class TangkiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tangki
        fields = ["id", "kode", "nama", "aktif"]

    def validate_kode(self, v):
        # Normalisasi di SETIAP jalur tulis, bukan hanya di Model.save().
        # 'tk-0001' dan 'TK-0001' menunjuk tangki yang sama; memperlakukan
        # keduanya sebagai dua benda memecah saldo tanpa suara.
        return v.strip().upper()


# ==========================================
# BARIS INPUT
# ==========================================

class InputRawSerializer(serializers.Serializer):
    raw = serializers.IntegerField()
    qty_kg = serializers.DecimalField(max_digits=18, decimal_places=3,
                                      min_value=QTY_MIN)


class InputWipSerializer(serializers.Serializer):
    batch_sumber = serializers.IntegerField()
    qty_kg = serializers.DecimalField(max_digits=18, decimal_places=3,
                                      min_value=QTY_MIN)


def _cek_duplikat(baris, kunci, kode, label):
    terlihat = set()
    for b in baris:
        i = b[kunci]
        if i in terlihat:
            raise serializers.ValidationError({
                "kode": kode,
                "pesan": f"{label} id {i} muncul lebih dari sekali. "
                         f"Gabungkan qty-nya di satu baris.",
            })
        terlihat.add(i)


def _validasi_input(data):
    raws = data.get("input_raw") or []
    wips = data.get("input_wip") or []
    if not raws and not wips:
        raise serializers.ValidationError({
            "kode": "INPUT_KOSONG",
            "pesan": "Pilih minimal satu sumber dengan qty > 0.",
        })
    _cek_duplikat(raws, "raw", "RAW_DUPLIKAT", "Bahan")
    _cek_duplikat(wips, "batch_sumber", "WIP_DUPLIKAT", "Batch")
    return data


class PratinjauRequestSerializer(serializers.Serializer):
    """
    Kontrak kalkulator.

    `tangki` dan `nama_hasil` OPSIONAL di sini -- ini kalkulator, dan
    memblokir hitungan sampai operator mengisi nama hasil membuat umpan
    baliknya datang terlambat.
    """
    tangki = serializers.IntegerField(required=False, allow_null=True)
    nama_hasil = serializers.CharField(max_length=120, required=False,
                                       allow_blank=True)
    tekor_kg = serializers.DecimalField(max_digits=18, decimal_places=3,
                                        required=False,
                                        default=Decimal("0.000"),
                                        min_value=Decimal("0"))
    input_raw = InputRawSerializer(many=True, required=False, default=list)
    input_wip = InputWipSerializer(many=True, required=False, default=list)

    def validate(self, data):
        return _validasi_input(data)


class BatchCreateSerializer(serializers.Serializer):
    """Membuat DRAFT lengkap dengan baris inputnya dalam satu request."""
    tangki = serializers.PrimaryKeyRelatedField(
        queryset=Tangki.objects.filter(aktif=True))
    nama_hasil = serializers.CharField(max_length=120)
    tekor_kg = serializers.DecimalField(max_digits=18, decimal_places=3,
                                        required=False,
                                        default=Decimal("0.000"),
                                        min_value=Decimal("0"))
    catatan = serializers.CharField(required=False, allow_blank=True,
                                    default="")
    input_raw = InputRawSerializer(many=True, required=False, default=list)
    input_wip = InputWipSerializer(many=True, required=False, default=list)

    def validate(self, data):
        return _validasi_input(data)

    def create(self, validated):
        raws = validated.pop("input_raw", [])
        wips = validated.pop("input_wip", [])

        # `jenis` adalah label TURUNAN, bukan percabangan logika.
        # Mixing dan blending memakai satu jalur valuasi yang sama.
        jenis = "BLENDING" if wips else "MIXING"
        awalan = "BD" if wips else "MX"

        req = self.context.get("request")
        user = getattr(req, "user", None)

        batch = Batch.objects.create(
            nomor=nomor_baru(awalan, timezone.now().strftime("%Y%m")),
            jenis=jenis,
            nama_hasil=validated["nama_hasil"],
            tangki=validated["tangki"],
            tekor_kg=validated.get("tekor_kg") or Decimal("0.000"),
            catatan=validated.get("catatan", ""),
            status=StatusBatch.DRAFT,
            created_by=user if getattr(user, "is_authenticated", False) else None,
        )
        BatchInputRaw.objects.bulk_create([
            BatchInputRaw(batch=batch, raw_id=r["raw"], qty_kg=r["qty_kg"])
            for r in raws
        ])
        TransferWip.objects.bulk_create([
            TransferWip(batch_tujuan=batch, batch_sumber_id=w["batch_sumber"],
                        qty_kg=w["qty_kg"])
            for w in wips
        ])
        return batch


# ==========================================
# BACA
# ==========================================

class BatchInputRawSerializer(serializers.ModelSerializer):
    raw_kode = serializers.CharField(source="raw.kode", read_only=True)
    raw_nama = serializers.CharField(source="raw.nama", read_only=True)

    class Meta:
        model = BatchInputRaw
        fields = ["id", "raw", "raw_kode", "raw_nama", "qty_kg",
                  "harga_per_kg", "nilai", "menghabiskan"]
        read_only_fields = ["harga_per_kg", "nilai", "menghabiskan"]


class TransferWipSerializer(serializers.ModelSerializer):
    sumber_nomor = serializers.CharField(source="batch_sumber.nomor",
                                         read_only=True)
    sumber_nama = serializers.CharField(source="batch_sumber.nama_hasil",
                                        read_only=True)
    sumber_tangki = serializers.CharField(source="batch_sumber.tangki.kode",
                                          read_only=True)

    class Meta:
        model = TransferWip
        fields = ["id", "batch_sumber", "sumber_nomor", "sumber_nama",
                  "sumber_tangki", "qty_kg", "harga_per_kg", "nilai",
                  "menghabiskan", "waktu"]
        read_only_fields = ["harga_per_kg", "nilai", "menghabiskan"]


class BatchSerializer(serializers.ModelSerializer):
    input_raw = BatchInputRawSerializer(many=True, read_only=True)
    input_wip = TransferWipSerializer(many=True, read_only=True)
    tangki_kode = serializers.CharField(source="tangki.kode", read_only=True)

    class Meta:
        model = Batch
        fields = "__all__"
        read_only_fields = [
            "nomor", "jenis", "total_qty_input", "total_nilai_input",
            "nilai_susut", "qty_hasil", "nilai_hasil", "harga_masuk_per_kg",
            "harga_hasil_per_kg", "status", "created_by", "created_at",
            "updated_at", "posted_by", "posted_at", "posting_key",
        ]

    def validate(self, data):
        if self.instance and self.instance.status != StatusBatch.DRAFT:
            raise serializers.ValidationError({
                "kode": "BATCH_TERKUNCI",
                "pesan": f"Batch {self.instance.nomor} sudah "
                         f"{self.instance.status} dan tidak bisa diubah.",
            })
        return data