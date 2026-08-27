from decimal import Decimal
from rest_framework import serializers
from .models import (
    Kemasan, MutasiKlaim, Packing, Pembelian, SaldoEntitas,
    StatusDokumen, PoolResource, PoolKemasan
)

class EntitasRingkasSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    kode = serializers.CharField(read_only=True)
    nama = serializers.CharField(read_only=True)
    grup_bahan = serializers.IntegerField(source="grup_bahan_id", read_only=True)
    grup_kode = serializers.CharField(source="grup_bahan.kode", read_only=True)
    aktif = serializers.BooleanField(read_only=True)

class ProdukRingkasSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    kode = serializers.CharField(read_only=True)
    nama = serializers.CharField(read_only=True)

class KemasanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kemasan
        fields = ["id", "nama", "bobot_kg", "aktif"]

class PoolResourceSerializer(serializers.ModelSerializer):
    produk_kode = serializers.CharField(source="produk.kode", read_only=True)
    produk_nama = serializers.CharField(source="produk.nama", read_only=True)
    harga_rata = serializers.DecimalField(max_digits=20, decimal_places=6, read_only=True)

    class Meta:
        model = PoolResource
        fields = ["id", "produk", "produk_kode", "produk_nama", "qty_kg", "nilai", "harga_rata", "diubah_pada"]
        read_only_fields = fields

class SaldoEntitasSerializer(serializers.ModelSerializer):
    entitas_kode = serializers.CharField(source="entitas.kode", read_only=True)
    entitas_nama = serializers.CharField(source="entitas.nama", read_only=True)
    grup_kode = serializers.CharField(source="entitas.grup_bahan.kode", read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = SaldoEntitas
        fields = ["entitas", "entitas_kode", "entitas_nama", "grup_kode",
                  "qty_setor", "qty_tarik", "total_setor", "total_tarik",
                  "total_rugi", "saldo", "status", "diubah_pada"]
        read_only_fields = fields

    def get_status(self, obj):
        if obj.saldo == Decimal("0"):
            return "IMPAS"
        return "KLAIM" if obj.saldo > 0 else "HUTANG"

class PembelianSerializer(serializers.ModelSerializer):
    entitas_kode = serializers.CharField(source="entitas.kode", read_only=True)
    grup_kode = serializers.CharField(source="grup_bahan.kode", read_only=True)
    produk_kode = serializers.CharField(source="produk.kode", read_only=True)
    produk_nama = serializers.CharField(source="produk.nama", read_only=True)

    class Meta:
        model = Pembelian
        fields = [
            "id", "nomor", "no_po", "entitas", "entitas_kode",
            "grup_bahan", "grup_kode", "produk", "produk_kode", "produk_nama",
            "qty_kg", "harga_per_kg", "nilai",
            "tanggal", "waktu", "status", "sumber", "penerimaan_item",
            "catatan", "dibuat_oleh", "dibuat_pada", "posted_at",
        ]
        read_only_fields = ["nomor", "nilai", "status", "sumber",
                            "penerimaan_item", "grup_bahan", "dibuat_oleh",
                            "dibuat_pada", "posted_at"]

    def validate(self, data):
        inst = self.instance
        if inst and inst.status != StatusDokumen.DRAFT:
            raise serializers.ValidationError({
                "kode": "DOKUMEN_TERKUNCI",
                "pesan": f"Pembelian {inst.nomor} sudah {inst.status} dan tidak bisa diubah.",
            })
        qty = data.get("qty_kg", getattr(inst, "qty_kg", None))
        hrg = data.get("harga_per_kg", getattr(inst, "harga_per_kg", None))
        if qty is not None and qty <= 0:
            raise serializers.ValidationError({"qty_kg": "Qty harus lebih dari 0."})
        if hrg is not None and hrg < 0:
            raise serializers.ValidationError({"harga_per_kg": "Harga tidak boleh negatif."})
        ent = data.get("entitas") or getattr(inst, "entitas", None)
        if ent is not None and not ent.aktif:
            raise serializers.ValidationError({
                "entitas": f"Entitas {ent.kode} nonaktif dan tidak bisa menyetor.",
            })
        return data

class PackingSerializer(serializers.ModelSerializer):
    entitas_kode = serializers.CharField(source="entitas.kode", read_only=True)
    batch_nomor = serializers.CharField(source="batch.nomor", read_only=True)
    batch_hasil = serializers.CharField(source="batch.nama_hasil", read_only=True)
    kemasan_nama = serializers.CharField(source="kemasan.nama", read_only=True)

    class Meta:
        model = Packing
        fields = [
            "id", "nomor", "entitas", "entitas_kode",
            "batch", "batch_nomor", "batch_hasil",
            "kemasan", "kemasan_nama",
            "total_unit", "qty_kg", "harga_per_kg", "nilai_hpp",
            "menghabiskan", "tanggal", "waktu", "status",
            "dibuat_oleh", "dibuat_pada", "posted_at",
        ]
        read_only_fields = ["nomor", "harga_per_kg", "nilai_hpp",
                            "menghabiskan", "status", "dibuat_oleh",
                            "dibuat_pada", "posted_at"]

    def validate(self, data):
        inst = self.instance
        if inst and inst.status != StatusDokumen.DRAFT:
            raise serializers.ValidationError({
                "kode": "DOKUMEN_TERKUNCI",
                "pesan": f"Packing {inst.nomor} sudah {inst.status}.",
            })
        for f in ("qty_kg", "total_unit"):
            v = data.get(f, getattr(inst, f, None))
            if v is not None and v <= 0:
                raise serializers.ValidationError({f: f"{f} harus lebih dari 0."})
        ent = data.get("entitas") or getattr(inst, "entitas", None)
        batch = data.get("batch") or getattr(inst, "batch", None)
        if ent is not None and not ent.aktif:
            raise serializers.ValidationError({"entitas": f"Entitas {ent.kode} nonaktif."})
        
        # Validasi bahwa batch dan entitas memiliki grup yang sama dihapus 
        # karena batch sekarang mengambil dari PoolResource (lintas grup).

        return data

class MutasiKlaimSerializer(serializers.ModelSerializer):
    entitas_kode = serializers.CharField(source="entitas.kode", read_only=True)
    grup_kode = serializers.CharField(source="grup_bahan.kode", read_only=True)

    class Meta:
        model = MutasiKlaim
        fields = ["id", "entitas", "entitas_kode", "grup_bahan", "grup_kode",
                  "tipe", "arah", "qty_kg", "nilai", "ref_type", "ref_id",
                  "keterangan", "waktu", "dibuat_pada", "dibuat_oleh"]
        read_only_fields = fields
        
class PoolKemasanSerializer(serializers.ModelSerializer):
    produk_kode = serializers.CharField(source="produk.kode", read_only=True)
    produk_nama = serializers.CharField(source="produk.nama", read_only=True)
    harga_satuan = serializers.DecimalField(max_digits=20, decimal_places=6, read_only=True)

    class Meta:
        model = PoolKemasan
        fields = ["id", "produk", "produk_kode", "produk_nama", "qty_unit", "nilai", "harga_satuan", "diubah_pada"]
        read_only_fields = fields

