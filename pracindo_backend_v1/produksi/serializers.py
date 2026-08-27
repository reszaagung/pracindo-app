from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from rest_framework import serializers
from .models import (
    Batch, BatchInputRaw, StatusBatch, Tangki, TransferWip
)

QTY_MIN = Decimal("0.000")

# Asumsi ada fungsi helper nomor_baru, jika tidak ada sesuaikan dengan import Anda
def nomor_baru(awalan, periode):
    # Dummy placeholder, pastikan fungsi nomor_baru Anda terimport dengan benar dari utils
    pass

class TangkiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tangki
        fields = ["id", "kode", "nama", "aktif"]

class InputRawSerializer(serializers.Serializer):
    raw = serializers.CharField(required=True)
    qty_kg = serializers.DecimalField(max_digits=18, decimal_places=3, required=True, min_value=QTY_MIN)

    def to_internal_value(self, data):
        mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'qty_kg' not in mutable_data or not mutable_data['qty_kg']:
            mutable_data['qty_kg'] = 0
        return super().to_internal_value(mutable_data)

class InputWipSerializer(serializers.Serializer):
    batch = serializers.CharField(required=True)
    qty_kg = serializers.DecimalField(max_digits=18, decimal_places=3, required=True, min_value=QTY_MIN)
    tangki_asal = serializers.IntegerField(required=False, allow_null=True)

    def to_internal_value(self, data):
        mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'qty_kg' not in mutable_data or not mutable_data['qty_kg']:
            mutable_data['qty_kg'] = 0
        return super().to_internal_value(mutable_data)

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
        
    if valid_wips:
        nomor_wip = [w["batch"] for w in valid_wips]
        found_wip = set(Batch.objects.filter(nomor__in=nomor_wip).values_list("nomor", flat=True))
        missing_wip = [n for n in nomor_wip if n not in found_wip]
        if missing_wip:
            raise serializers.ValidationError({
                "wip_sources": f"Batch WIP {', '.join(missing_wip)} tidak ditemukan."
            })
            
    return {"materials": valid_raws, "wip_sources": valid_wips}

class PratinjauRequestSerializer(serializers.Serializer):
    tangki_tujuan = serializers.IntegerField(required=False, allow_null=True)
    nama_hasil = serializers.CharField(max_length=120, required=False, allow_blank=True)
    susut_kg = serializers.DecimalField(max_digits=18, decimal_places=3, required=False, allow_null=True)
    materials = InputRawSerializer(many=True, required=False, default=list)
    wip_sources = InputWipSerializer(many=True, required=False, default=list)

    def validate(self, data):
        data.update(_validasi_input(data))
        return data

class BatchCreateSerializer(serializers.Serializer):
    tangki_tujuan = serializers.PrimaryKeyRelatedField(
        queryset=Tangki.objects.filter(aktif=True),
        required=True,
        error_messages={"required": "Tangki tujuan wajib dipilih."}
    )
    nama_hasil = serializers.CharField(max_length=120, required=True)
    batch = serializers.CharField(max_length=30, required=False, allow_blank=True)
    harga_per_kg = serializers.ReadOnlyField()
    susut_kg = serializers.DecimalField(max_digits=18, decimal_places=3, required=False, default=Decimal("0.000"))
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
        
        nomor_batch = validated.get("batch")
        if not nomor_batch:
            nomor_batch = nomor_baru(awalan, timezone.now().strftime("%Y%m"))

        with transaction.atomic():
            batch = Batch.objects.create(
                nomor=nomor_batch,
                jenis=jenis,
                nama_hasil=validated["nama_hasil"],
                tangki=validated["tangki_tujuan"],
                susut_kg=validated.get("susut_kg") or Decimal("0.000"), # FIX
                catatan=validated.get("catatan", ""),
                status=StatusBatch.DRAFT,
                dibuat_oleh=user if getattr(user, "is_authenticated", False) else None, # FIX
            )

            if raws:
                BatchInputRaw.objects.bulk_create([
                    BatchInputRaw(batch=batch, produk_id=int(r["raw"]), qty_kg=r["qty_kg"])
                    for r in raws
                ])
                
            if wips:
                nomor_wip = [w["batch"] for w in wips]
                b_sumber_map = {b.nomor: b for b in Batch.objects.filter(nomor__in=nomor_wip)}
                
                wip_objects = [
                    TransferWip(
                        batch_tujuan=batch, 
                        batch_sumber_id=b_sumber_map[w["batch"]].id,
                        qty_kg=w["qty_kg"],
                        dibuat_oleh=user if getattr(user, "is_authenticated", False) else None
                    ) for w in wips
                ]
                TransferWip.objects.bulk_create(wip_objects)

        return batch

class BatchSerializer(serializers.ModelSerializer):
    tangki_kode = serializers.CharField(source="tangki.kode", read_only=True)
    tangki_tujuan_nama = serializers.CharField(source="tangki.nama", read_only=True)
    batch = serializers.CharField(source="nomor", read_only=True)
    
    class Meta:
        model = Batch
        fields = "__all__"