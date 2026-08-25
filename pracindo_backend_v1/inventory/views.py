from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from core.models import CounterDokumen, Entitas
from master.models import Produk
from . import serializers as ser
from . import services
from .models import Kemasan, MutasiKlaim, Packing, Pembelian, RawMutasiEntity, StatusDokumen, rp
from .permissions import AksesInventory, SupervisorInventory

MODUL = "inventory"

def _galat(e):
    kode = e.__class__.__name__
    pesan = getattr(e, "message", None) or (e.messages[0] if getattr(e, "messages", None) else str(e))
    return Response({"detail": pesan, "kode": kode, "pesan": pesan}, status=getattr(e, "http", 400))

GALAT_TERTANGANI = (services.GalatInventory, DjangoValidationError)

@api_view(["GET"])
@permission_classes([AksesInventory])
def entitas_list(request):
    qs = Entitas.objects.select_related("grup_bahan").order_by("kode")
    if request.query_params.get("aktif") in ("true", "1", "True"):
        qs = qs.filter(aktif=True)
    if request.query_params.get("grup"):
        qs = qs.filter(grup_bahan_id=request.query_params["grup"])
    return Response(ser.EntitasRingkasSerializer(qs, many=True).data)

@api_view(["GET"])
@permission_classes([AksesInventory])
def produk_list(request):
    qs = Produk.objects.order_by("kode")
    q = request.query_params.get("q")
    if q:
        qs = qs.filter(nama__icontains=q)
    return Response(ser.ProdukRingkasSerializer(qs[:200], many=True).data)

class KemasanViewSet(viewsets.ModelViewSet):
    modul = MODUL
    queryset = Kemasan.objects.all().order_by("nama")
    serializer_class = ser.KemasanSerializer
    permission_classes = [AksesInventory]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("aktif") in ("true", "1", "True"):
            qs = qs.filter(aktif=True)
        return qs

class PembelianViewSet(viewsets.ModelViewSet):
    modul = MODUL
    queryset = Pembelian.objects.select_related("entitas", "grup_bahan", "produk").order_by("-waktu", "-id")
    serializer_class = ser.PembelianSerializer
    permission_classes = [AksesInventory]

    def get_permissions(self):
        if self.action == "void":
            return [AksesInventory(), SupervisorInventory()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        for param, field in (("entitas", "entitas_id"),
                             ("produk", "produk_id"),
                             ("grup", "grup_bahan_id"),
                             ("status", "status"),
                             ("sumber", "sumber")):
            if p.get(param):
                qs = qs.filter(**{field: p[param]})
        if p.get("no_po"):
            qs = qs.filter(no_po__icontains=p["no_po"])
        if p.get("dari"):
            qs = qs.filter(tanggal__gte=p["dari"])
        if p.get("sampai"):
            qs = qs.filter(tanggal__lte=p["sampai"])
        return qs

    def perform_create(self, serializer):
        d = serializer.validated_data
        ent = d["entitas"]
        try:
            nomor = CounterDokumen.berikutnya(ent, "PB", d["tanggal"])
        except DjangoValidationError as e:
            raise DRFValidationError({"kode": "PENOMORAN_GAGAL", "pesan": str(e)})
        serializer.save(
            nomor=nomor,
            grup_bahan=ent.grup_bahan,
            nilai=rp(d["qty_kg"] * d["harga_per_kg"]),
            dibuat_oleh=self.request.user,
        )

    def perform_update(self, serializer):
        inst = serializer.instance
        d = serializer.validated_data
        qty_kg = d.get("qty_kg", inst.qty_kg)
        hrg = d.get("harga_per_kg", inst.harga_per_kg)
        ent = d.get("entitas", inst.entitas)
        serializer.save(nilai=rp(qty_kg * hrg), grup_bahan=ent.grup_bahan)

    def perform_destroy(self, instance):
        if instance.status != StatusDokumen.DRAFT:
            raise DRFValidationError({
                "kode": "DOKUMEN_TERKUNCI",
                "pesan": "Hanya pembelian DRAFT yang bisa dihapus. Dokumen POSTED dibatalkan lewat /void/.",
            })
        Pembelian.objects.filter(pk=instance.pk).delete()

    @action(detail=True, methods=["post"], url_path="post")
    def posting(self, request, pk=None):
        try:
            hasil = services.posting_pembelian(self.get_object(), user=request.user)
        except GALAT_TERTANGANI as e:
            return _galat(e)
        return Response(ser.PembelianSerializer(hasil).data)

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        try:
            hasil = services.void_pembelian(self.get_object(), request.data.get("alasan", ""), user=request.user)
        except GALAT_TERTANGANI as e:
            return _galat(e)
        return Response(ser.PembelianSerializer(hasil).data)

class PackingViewSet(viewsets.ModelViewSet):
    modul = MODUL
    queryset = Packing.objects.select_related("entitas", "batch", "kemasan").order_by("-waktu", "-id")
    serializer_class = ser.PackingSerializer
    permission_classes = [AksesInventory]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        for param, field in (("entitas", "entitas_id"), ("batch", "batch_id"), ("status", "status")):
            if p.get(param):
                qs = qs.filter(**{field: p[param]})
        if p.get("dari"):
            qs = qs.filter(tanggal__gte=p["dari"])
        if p.get("sampai"):
            qs = qs.filter(tanggal__lte=p["sampai"])
        return qs

    def perform_create(self, serializer):
        from django.utils import timezone
        d = serializer.validated_data
        ent = d["entitas"]
        tgl = d.get("tanggal") or timezone.localdate()
        try:
            nomor = CounterDokumen.berikutnya(ent, "PKG", tgl)
        except DjangoValidationError as e:
            raise DRFValidationError({"kode": "PENOMORAN_GAGAL", "pesan": str(e)})
        serializer.save(nomor=nomor, tanggal=tgl, dibuat_oleh=self.request.user)

    def perform_destroy(self, instance):
        if instance.status != StatusDokumen.DRAFT:
            raise DRFValidationError({
                "kode": "DOKUMEN_TERKUNCI",
                "pesan": "Hanya packing DRAFT yang bisa dihapus.",
            })
        instance.delete()

    @action(detail=True, methods=["post"], url_path="post")
    def posting(self, request, pk=None):
        try:
            hasil = services.posting_packing(self.get_object(), user=request.user)
        except GALAT_TERTANGANI as e:
            return _galat(e)
        return Response(ser.PackingSerializer(hasil).data)

    @action(detail=False, methods=["get"])
    def pratinjau(self, request):
        return Response(services.pratinjau_packing(request.query_params.get("batch"), request.query_params.get("qty") or 0))

def _int_atau_none(nilai):
    try:
        return int(nilai) if nilai not in (None, "") else None
    except (TypeError, ValueError):
        return None

@api_view(["GET"])
@permission_classes([AksesInventory])
def raw_mutasi_list(request):
    return Response(services.get_raw_mutasi_entity_all(_int_atau_none(request.query_params.get("grup"))))

@api_view(["GET"])
@permission_classes([AksesInventory])
def pool_kartu_stok(request, produk_id):
    grup = _int_atau_none(request.query_params.get("grup"))
    if grup is None:
        return Response({"kode": "GRUP_WAJIB", "detail": "Parameter `grup` wajib dan harus berupa angka."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        return Response(services.get_kartu_stok(int(produk_id), grup))
    except RawMutasiEntity.DoesNotExist:
        return Response({"kode": "POOL_BELUM_ADA", "detail": f"Produk {produk_id} belum punya baris di grup {grup}."}, status=status.HTTP_404_NOT_FOUND)

@api_view(["GET"])
@permission_classes([AksesInventory])
def mutasi_list(request):
    qs = MutasiKlaim.objects.select_related("entitas", "grup_bahan").order_by("-waktu", "-id")
    p = request.query_params
    if p.get("entitas"):
        qs = qs.filter(entitas_id=p["entitas"])
    if p.get("grup"):
        qs = qs.filter(grup_bahan_id=p["grup"])
    if p.get("tipe"):
        qs = qs.filter(tipe=p["tipe"].upper())
    if p.get("dari"):
        qs = qs.filter(waktu__date__gte=p["dari"])
    if p.get("sampai"):
        qs = qs.filter(waktu__date__lte=p["sampai"])
    try:
        batas = min(int(p.get("limit", 200)), 1000)
    except (TypeError, ValueError):
        batas = 200
    return Response(ser.MutasiKlaimSerializer(qs[:batas], many=True).data)

@api_view(["GET"])
@permission_classes([AksesInventory])
def mutasi_rekap(request):
    return Response(services.get_rekap_klaim(_int_atau_none(request.query_params.get("grup"))))

@api_view(["GET"])
@permission_classes([AksesInventory])
def pemeriksaan_invarian(request):
    return Response(services.jalankan_pemeriksaan_invarian())

@api_view(["GET"])
@permission_classes([AksesInventory])
def barang_jadi(request):
    return Response(services.get_barang_jadi(_int_atau_none(request.query_params.get("grup"))))

@api_view(["GET"])
@permission_classes([AksesInventory])
def stok_list(request):
    lapis = (request.query_params.get("lapis") or "POOL").upper()
    grup = _int_atau_none(request.query_params.get("grup"))
    if lapis == "POOL":
        d = services.get_raw_mutasi_entity_all(grup)
        return Response({"lapis": "POOL", "rincian": d["rincian"], "total_nilai": d["total_nilai_pool"]})
    if lapis == "JADI":
        d = services.get_barang_jadi(grup)
        return Response({"lapis": "JADI", "rincian": d["rincian"], "total_nilai": d["total_nilai"]})
    return Response({"kode": "LAPIS_TIDAK_DIKENAL", "detail": f"Lapis '{lapis}' tidak ada."}, status=status.HTTP_400_BAD_REQUEST)