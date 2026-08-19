"""
Endpoint Produksi — produksi/views.py

PEMETAAN GALAT KE HTTP

    GalatValidasi      422  payload tidak masuk akal
    KonflikSaldo       409  payload masuk akal, kenyataan menolak
    InvariantMelenceng 500  rupiah tercipta/menguap, transaksi di-rollback

    Menangkap semuanya sebagai 409 -- seperti versi sebelumnya --
    membuat frontend tidak bisa membedakan "perbaiki isian" dari
    "hubungi admin".
"""
from dataclasses import asdict
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from . import serializers as ser
from . import services
from .models import Batch, StatusBatch, Tangki, nomor_baru
from .permissions import ModulProduksi, OperatorSesi


def _galat_response(e):
    return Response({"detail": e.pesan, **e.as_dict()}, status=e.http)


class TangkiViewSet(viewsets.ModelViewSet):
    queryset = Tangki.objects.all().order_by("kode")
    serializer_class = ser.TangkiSerializer
    permission_classes = [ModulProduksi]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("aktif") in ("true", "1", "True"):
            qs = qs.filter(aktif=True)
        return qs

    @action(detail=True, methods=["get"])
    def saldo(self, request, pk=None):
        return Response(services.saldo_tangki(self.get_object()))


class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.select_related("tangki").order_by("-waktu", "-id")
    permission_classes = [ModulProduksi]

    def get_serializer_class(self):
        return ser.BatchCreateSerializer if self.action == "create" \
            else ser.BatchSerializer

    def get_permissions(self):
        if self.action in ("posting", "void"):
            return [ModulProduksi(), OperatorSesi()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        for param, field in (("tangki", "tangki_id"), ("jenis", "jenis"),
                             ("status", "status")):
            if p.get(param):
                qs = qs.filter(**{field: p[param]})
        if p.get("dari"):
            qs = qs.filter(waktu__date__gte=p["dari"])
        if p.get("sampai"):
            qs = qs.filter(waktu__date__lte=p["sampai"])
        return qs

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        batch = s.save()
        return Response(ser.BatchSerializer(batch).data,
                        status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        from rest_framework.exceptions import ValidationError
        if instance.status != StatusBatch.DRAFT:
            raise ValidationError({"kode": "BATCH_TERKUNCI",
                                   "pesan": "Hanya batch DRAFT yang bisa "
                                            "dihapus."})
        instance.delete()

    @action(detail=True, methods=["post"], url_path="post")
    def posting(self, request, pk=None):
        try:
            batch = services.posting_batch(self.get_object(),
                                           user=request.user)
        except services.GalatProduksi as e:
            return _galat_response(e)
        return Response(ser.BatchSerializer(batch).data)

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        try:
            batch = services.void_batch(
                self.get_object(),
                request.data.get("alasan", ""), user=request.user)
        except services.GalatProduksi as e:
            return _galat_response(e)
        return Response(ser.BatchSerializer(batch).data)

    @action(detail=True, methods=["get"])
    def saldo(self, request, pk=None):
        return Response(services.saldo_batch(self.get_object()).as_dict())

    @action(detail=True, methods=["get"])
    def komposisi(self, request, pk=None):
        return Response(services.komposisi_json(self.get_object()))

    @action(detail=False, methods=["get"])
    def tersedia(self, request):
        return Response(services.get_batch_tersedia(
            request.query_params.get("tangki")))

    @action(detail=False, methods=["get"], url_path="nomor-baru")
    def nomor_baru_(self, request):
        from django.utils import timezone
        awalan = "BD" if request.query_params.get("jenis") == "BLENDING" else "MX"
        return Response({"nomor": nomor_baru(
            awalan, timezone.now().strftime("%Y%m"))})


@api_view(["POST"])
@permission_classes([ModulProduksi])
def pratinjau_batch(request):
    """
    POST /api/produksi/pratinjau/

    SELALU 200. Pratinjau adalah kalkulator, bukan gerbang -- 4xx akan
    memicu penanganan error global yang salah tempat sementara operator
    masih mengetik.
    """
    s = ser.PratinjauRequestSerializer(data=request.data)
    if not s.is_valid():
        return Response({"valid": False, "galat": [s.errors]})

    d = s.validated_data
    pakai_raw = {r["raw"]: r["qty_kg"] for r in d.get("input_raw", [])}
    pakai_wip = {w["batch_sumber"]: w["qty_kg"] for w in d.get("input_wip", [])}

    v, galat = services.pratinjau(pakai_raw, pakai_wip, d["tekor_kg"])
    if galat is not None:
        return Response({"valid": False, "galat": [galat.as_dict()]})

    return Response({
        "valid": True,
        **asdict(v)
    })