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
    Batch, BatchInputRaw, StatusBatch, Tangki, TransferWip, nomor_baru
)

QTY_MIN = Decimal("0.000")


class TangkiSerializer(serializers.ModelSerializer):
    # BARU — sebelumnya tidak ada di modul ini, padahal TangkiViewSet
    # di views.py sudah memakai ser.TangkiSerializer sejak awal.
    class Meta:
        model = Tangki
        fields = ["id", "kode", "nama", "aktif"]


class InputRawSerializer(serializers.Serializer):
    raw = serializers.IntegerField(required=False, allow_null=True)
    qty_kg = serializers.DecimalField(max_digits=18, decimal_places=3, required=False, allow_null=True)

    def to_internal_value(self, data):
        if isinstance(data, dict):
            d = data.copy()
            raw_val = d.get('raw') or d.get('raw_id') or d.get('produk') or d.get('produk_id') or d.get('id')
            qty_val = d.get('qty_kg') if d.get('qty_kg') is not None else (d.get('qty') if d.get('qty') is not None else 0)
            
            try:
                d['raw'] = int(raw_val) if raw_val is not None and str(raw_val).strip() != '' else None
            except (ValueError, TypeError):
                d['raw'] = None

            try:
                if isinstance(qty_val, str):
                    qty_val = qty_val.replace(',', '.')
                d['qty_kg'] = Decimal(str(qty_val)) if qty_val is not None and str(qty_val).strip() != '' else Decimal('0')
            except Exception:
                d['qty_kg'] = Decimal('0')
                
            data = d
        return super().to_internal_value(data)

    def validate(self, data):
        if not data.get('raw'):
            raise serializers.ValidationError({"raw": "Bahan baku wajib dipilih."})
        if data.get('qty_kg', Decimal('0')) <= 0:
            raise serializers.ValidationError({"qty_kg": "Kuantitas harus lebih besar dari 0."})
        return data

class InputWipSerializer(serializers.Serializer):
    batch_sumber = serializers.IntegerField(required=False, allow_null=True)
    qty_kg = serializers.DecimalField(max_digits=18, decimal_places=3, required=False, allow_null=True)

    def to_internal_value(self, data):
        if isinstance(data, dict):
            d = data.copy()
            sumber_val = d.get('batch_sumber') or d.get('sumber') or d.get('batch_sumber_id') or d.get('id')
            qty_val = d.get('qty_kg') if d.get('qty_kg') is not None else (d.get('qty') if d.get('qty') is not None else 0)
            
            try:
                d['batch_sumber'] = int(sumber_val) if sumber_val is not None and str(sumber_val).strip() != '' else None
            except (ValueError, TypeError):
                d['batch_sumber'] = None

            try:
                if isinstance(qty_val, str):
                    qty_val = qty_val.replace(',', '.')
                d['qty_kg'] = Decimal(str(qty_val)) if qty_val is not None and str(qty_val).strip() != '' else Decimal('0')
            except Exception:
                d['qty_kg'] = Decimal('0')
                
            data = d
        return super().to_internal_value(data)

    def validate(self, data):
        if not data.get('batch_sumber'):
            raise serializers.ValidationError({"batch_sumber": "Batch sumber wajib dipilih."})
        if data.get('qty_kg', Decimal('0')) <= 0:
            raise serializers.ValidationError({"qty_kg": "Kuantitas harus lebih besar dari 0."})
        return data

def _cek_duplikat(baris, kunci, kode, label):
    terlihat = set()
    for b in baris:
        i = b[kunci]
        if i in terlihat:
            raise serializers.ValidationError({
                "kode": kode,
                "pesan": f"{label} id {i} muncul lebih dari sekali. Gabungkan qty-nya di satu baris.",
            })
        terlihat.add(i)

def _validasi_input(data):
    raws = data.get("input_raw") or []
    wips = data.get("input_wip") or []
    valid_raws = [r for r in raws if r.get('raw') and r.get('qty_kg', 0) > 0]
    valid_wips = [w for w in wips if w.get('batch_sumber') and w.get('qty_kg', 0) > 0]
    
    data["input_raw"] = valid_raws
    data["input_wip"] = valid_wips

    if not valid_raws and not valid_wips:
        raise serializers.ValidationError({
            "kode": "INPUT_KOSONG",
            "pesan": "Pilih minimal satu sumber dengan qty > 0.",
        })
    _cek_duplikat(valid_raws, "raw", "RAW_DUPLIKAT", "Bahan")
    _cek_duplikat(valid_wips, "batch_sumber", "WIP_DUPLIKAT", "Batch")
    return data

class PratinjauRequestSerializer(serializers.Serializer):
    tangki = serializers.IntegerField(required=False, allow_null=True)
    nama_hasil = serializers.CharField(max_length=120, required=False, allow_blank=True)
    tekor_kg = serializers.DecimalField(  # diubah dari CharField -> DecimalField
        max_digits=18, decimal_places=3, required=False, allow_null=True
    )
    input_raw = InputRawSerializer(many=True, required=False, default=list)
    input_wip = InputWipSerializer(many=True, required=False, default=list)

    def to_internal_value(self, data):
        if isinstance(data, dict):
            d = data.copy()
            tekor = d.get('tekor_kg') if d.get('tekor_kg') is not None else d.get('tekor')
            if tekor is not None:
                if isinstance(tekor, str):
                    tekor = tekor.replace(',', '.')
                try:
                    d['tekor_kg'] = Decimal(str(tekor))
                except Exception:
                    d['tekor_kg'] = Decimal('0.000')
            else:
                d['tekor_kg'] = Decimal('0.000')
            data = d
        return super().to_internal_value(data)

    def validate(self, data):
        return _validasi_input(data)

class BatchCreateSerializer(serializers.Serializer):
    tangki = serializers.PrimaryKeyRelatedField(
        queryset=Tangki.objects.filter(aktif=True),
        required=False, allow_null=True
    )
    nama_hasil = serializers.CharField(max_length=120, required=False, allow_blank=True)
    tekor_kg = serializers.DecimalField(  # diubah dari CharField -> DecimalField
        max_digits=18, decimal_places=3, required=False, allow_null=True
    )
    catatan = serializers.CharField(required=False, allow_blank=True, default="")
    input_raw = InputRawSerializer(many=True, required=False, default=list)
    input_wip = InputWipSerializer(many=True, required=False, default=list)

    def to_internal_value(self, data):
        if isinstance(data, dict):
            d = data.copy()
            if not d.get('tangki') and d.get('tangki_id'):
                d['tangki'] = d.get('tangki_id')
            
            tekor = d.get('tekor_kg') if d.get('tekor_kg') is not None else d.get('tekor')
            if tekor is not None:
                if isinstance(tekor, str):
                    tekor = tekor.replace(',', '.')
                try:
                    d['tekor_kg'] = Decimal(str(tekor))
                except Exception:
                    d['tekor_kg'] = Decimal('0.000')
            else:
                d['tekor_kg'] = Decimal('0.000')
            data = d
        return super().to_internal_value(data)

    def validate(self, data):
        if not data.get('tangki'):
            raise serializers.ValidationError({"tangki": "Tangki tujuan wajib dipilih."})
        if not data.get('nama_hasil'):
            raise serializers.ValidationError({"nama_hasil": "Nama hasil wajib diisi."})
        return _validasi_input(data)

    def create(self, validated):
        raws = validated.pop("input_raw", [])
        wips = validated.pop("input_wip", [])
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
            BatchInputRaw(batch=batch, produk_id=r["raw"], qty_kg=r["qty_kg"])
            for r in raws
        ])
        TransferWip.objects.bulk_create([
            TransferWip(batch_tujuan=batch, batch_sumber_id=w["batch_sumber"],
                        qty_kg=w["qty_kg"])
            for w in wips
        ])
        return batch

class BatchInputRawSerializer(serializers.ModelSerializer):
    raw_kode = serializers.CharField(source="produk.kode", read_only=True)
    raw_nama = serializers.CharField(source="produk.nama", read_only=True)
    raw = serializers.IntegerField(source="produk_id", read_only=True)
    class Meta:
        model = BatchInputRaw
        fields = ["id", "raw", "produk", "raw_kode", "raw_nama", "qty_kg",
                  "harga_per_kg", "nilai", "menghabiskan"]
        read_only_fields = ["harga_per_kg", "nilai", "menghabiskan"]

class TransferWipSerializer(serializers.ModelSerializer):
    sumber_nomor = serializers.CharField(source="batch_sumber.nomor", read_only=True)
    sumber_nama = serializers.CharField(source="batch_sumber.nama_hasil", read_only=True)
    sumber_tangki = serializers.CharField(source="batch_sumber.tangki.kode", read_only=True)
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
                "pesan": f"Batch {self.instance.nomor} sudah {self.instance.status} dan tidak bisa diubah.",
            })
        return data