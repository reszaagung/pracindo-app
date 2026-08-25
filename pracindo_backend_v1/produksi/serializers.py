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
    class Meta:
        model = Tangki
        fields = ["id", "kode", "nama", "aktif"]

class InputRawSerializer(serializers.Serializer):
    raw = serializers.CharField(required=True)  # Menerima string kode/ID dari Vue
    qty_kg = serializers.DecimalField(max_digits=18, decimal_places=3, required=True, min_value=QTY_MIN)

    def to_internal_value(self, data):
        # Mencegah error jika qty_kg kosong/null dari Vue
        if 'qty_kg' not in data or not data['qty_kg']:
            data['qty_kg'] = 0
        return super().to_internal_value(data)

class InputWipSerializer(serializers.Serializer):
    batch = serializers.CharField(required=True) # Menangkap nomor batch string dari Vue
    qty_kg = serializers.DecimalField(max_digits=18, decimal_places=3, required=True, min_value=QTY_MIN)
    tangki_asal = serializers.IntegerField(required=False, allow_null=True)

    def to_internal_value(self, data):
        if 'qty_kg' not in data or not data['qty_kg']:
            data['qty_kg'] = 0
        return super().to_internal_value(data)

def _validasi_input(data):
    raws = data.get("materials") or []
    wips = data.get("wip_sources") or []
    
    valid_raws = [r for r in raws if r.get('raw') and r.get('qty_kg', 0) > 0]
    valid_wips = [w for w in wips if w.get('batch') and w.get('qty_kg', 0) > 0]
    
    if not valid_raws and not valid_wips:
        raise serializers.ValidationError({
            "kode": "INPUT_KOSONG",
            "pesan": "Pilih minimal satu sumber bahan baku atau WIP dengan kuantitas lebih dari 0.",
        })
        
    return {"materials": valid_raws, "wip_sources": valid_wips}

class PratinjauRequestSerializer(serializers.Serializer):
    tangki_tujuan = serializers.IntegerField(required=False, allow_null=True)
    nama_hasil = serializers.CharField(max_length=120, required=False, allow_blank=True)
    tekor_kg = serializers.DecimalField(max_digits=18, decimal_places=3, required=False, allow_null=True)
    materials = InputRawSerializer(many=True, required=False, default=list)
    wip_sources = InputWipSerializer(many=True, required=False, default=list)

    def validate(self, data):
        return _validasi_input(data)

class BatchCreateSerializer(serializers.Serializer):
    tangki_tujuan = serializers.PrimaryKeyRelatedField(
        queryset=Tangki.objects.filter(aktif=True),
        required=True,
        error_messages={"required": "Tangki tujuan wajib dipilih."}
    )
    nama_hasil = serializers.CharField(max_length=120, required=True)
    batch = serializers.CharField(max_length=30, required=False, allow_blank=True)
    tekor_kg = serializers.DecimalField(max_digits=18, decimal_places=3, required=False, default=Decimal("0.000"))
    materials = InputRawSerializer(many=True, required=False, default=list)
    wip_sources = InputWipSerializer(many=True, required=False, default=list)
    catatan = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, data):
        data.update(_validasi_input(data))
        return data

    def create(self, validated):
        raws = validated.pop("materials", [])
        wips = validated.pop("wip_sources", [])
        
        jenis = "BLENDING" if wips else "MIXING"
        awalan = "BD" if wips else "MX"
        
        req = self.context.get("request")
        user = getattr(req, "user", None)
        
        # Menerima nomor batch dari Vue atau membuat baru jika kosong
        nomor_batch = validated.get("batch")
        if not nomor_batch:
            nomor_batch = nomor_baru(awalan, timezone.now().strftime("%Y%m"))

        batch = Batch.objects.create(
            nomor=nomor_batch,
            jenis=jenis,
            nama_hasil=validated["nama_hasil"],
            tangki=validated["tangki_tujuan"],
            tekor_kg=validated.get("tekor_kg") or Decimal("0.000"),
            catatan=validated.get("catatan", ""),
            status=StatusBatch.DRAFT,
            created_by=user if getattr(user, "is_authenticated", False) else None,
        )

        # Menyimpan baris material
        if raws:
            # Karena frontend mengirim string 'raw' (kode/ID), pastikan ini selaras dengan DB
            # Asumsi: frontend mengirim ID integer yang di-cast sebagai string
            BatchInputRaw.objects.bulk_create([
                BatchInputRaw(batch=batch, produk_id=int(r["raw"]), qty_kg=r["qty_kg"])
                for r in raws
            ])
            
        # Menyimpan baris WIP dengan mencari ID Batch berdasarkan string nomor batch
        if wips:
            wip_objects = []
            for w in wips:
                try:
                    batch_sumber = Batch.objects.get(nomor=w["batch"])
                    wip_objects.append(TransferWip(
                        batch_tujuan=batch, 
                        batch_sumber_id=batch_sumber.id,
                        qty_kg=w["qty_kg"]
                    ))
                except Batch.DoesNotExist:
                    raise serializers.ValidationError({"wip_sources": f"Batch WIP {w['batch']} tidak ditemukan."})
            TransferWip.objects.bulk_create(wip_objects)

        return batch

class BatchSerializer(serializers.ModelSerializer):
    tangki_kode = serializers.CharField(source="tangki.kode", read_only=True)
    tangki_tujuan_nama = serializers.CharField(source="tangki.nama", read_only=True)
    batch = serializers.CharField(source="nomor", read_only=True)
    
    class Meta:
        model = Batch
        fields = "__all__"