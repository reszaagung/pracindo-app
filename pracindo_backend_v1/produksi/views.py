from decimal import Decimal
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from . import serializers as ser
from . import services
from .models import Batch, StatusBatch, Tangki, TipeProses
from .permissions import ModulProduksi, OperatorSesi

def _galat_response(e):
    pesan = getattr(e, "message", None) or (e.messages[0] if getattr(e, "messages", None) else str(e))
    return Response({"detail": pesan, "kode": e.__class__.__name__, "pesan": pesan}, status=getattr(e, "http", 400))

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
        tangki = self.get_object()
        try:
            from decimal import Decimal
            
            # Ambil semua batch posted di tangki ini
            batches = Batch.objects.filter(tangki=tangki, status=StatusBatch.POSTED)
            
            total_qty = Decimal('0')
            total_nilai = Decimal('0')
            
            for b in batches:
                # Ambil langsung dari field database model Batch Anda
                qty = getattr(b, 'qty_hasil', Decimal('0'))
                
                # Cek berbagai kemungkinan nama field harga di model Anda
                harga = getattr(b, 'harga_per_kg', None)
                if harga is None:
                    harga = getattr(b, 'harga_rata', Decimal('0'))
                
                total_qty += Decimal(str(qty))
                total_nilai += (Decimal(str(qty)) * Decimal(str(harga)))
                
            harga_rata = (total_nilai / total_qty) if total_qty > 0 else Decimal('0')

            return Response({
                "sisa_qty": str(total_qty),
                "sisa_nilai": str(total_nilai),
                "harga_per_kg": str(harga_rata) if harga_rata is not None else "0"
            })
        except Exception as e:
            return Response({"detail": str(e)}, status=400)
            
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
        s = self.get_serializer(data=request.data, context={'request': request})
        s.is_valid(raise_exception=True)
        batch = s.save()
        return Response(ser.BatchSerializer(batch).data,
                        status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        from rest_framework.exceptions import ValidationError
        if instance.status != StatusBatch.DRAFT:
            raise ValidationError({"kode": "BATCH_TERKUNCI",
                                   "pesan": "Hanya batch DRAFT yang bisa dihapus."})
        instance.delete()

    @action(detail=True, methods=["post"], url_path="post")
    def posting(self, request, pk=None):
        batch = self.get_object()
        try:
            if batch.jenis == TipeProses.MIXING:
                batch = services.posting_mixing(batch, user=request.user)
            else:
                batch = services.posting_blending(batch, user=request.user)
        except services.GalatProduksi as e:
            return _galat_response(e)
        return Response(ser.BatchSerializer(batch).data)

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        return Response(
            {"detail": "Fitur VOID Batch belum diimplementasikan di layanan baru."}, 
            status=status.HTTP_501_NOT_IMPLEMENTED
        )

    @action(detail=True, methods=["get"])
    def saldo(self, request, pk=None):
        res = services.saldo_batch(self.get_object())
        return Response({
            "sisa_qty": str(res.sisa_qty),
            "sisa_nilai": str(res.sisa_nilai),
            "harga_per_kg": str(res.harga_per_kg)
        })

    @action(detail=False, methods=["get"], url_path="nomor-baru")
    def nomor_baru_(self, request):
        from django.utils import timezone
        jenis = request.query_params.get("jenis")
        tipe = TipeProses.BLENDING if jenis == "BLENDING" else TipeProses.MIXING
        nomor = services._nomor_batch(tipe, timezone.localdate())
        return Response({"nomor": nomor})


@api_view(["POST"])
@permission_classes([ModulProduksi])
def pratinjau_batch(request):
    s = ser.PratinjauRequestSerializer(data=request.data)
    if not s.is_valid():
        errs = []
        for field, messages in s.errors.items():
            if isinstance(messages, list):
                for m in messages:
                    if isinstance(m, dict) and "pesan" in m:
                        errs.append(m)
                    else:
                        errs.append({"field": field if field != "non_field_errors" else "", "pesan": str(m)})
            elif isinstance(messages, dict) and "pesan" in messages:
                errs.append(messages)
            else:
                errs.append({"field": field if field != "non_field_errors" else "", "pesan": str(messages)})
        return Response({"valid": False, "galat": errs})
        
    d = s.validated_data
    
    pakai_raw = [{"produk_id": int(r["raw"]), "qty_kg": r["qty_kg"]} for r in d.get("materials", []) if r.get("raw") and r.get("qty_kg", 0) > 0]
    
    pakai_wip = []
    for w in d.get("wip_sources", []):
        if w.get("batch") and w.get("qty_kg", 0) > 0:
            try:
                b_sumber = Batch.objects.get(nomor=w["batch"])
                pakai_wip.append({"batch_sumber_id": b_sumber.id, "qty_kg": w["qty_kg"]})
            except Batch.DoesNotExist:
                return Response({"valid": False, "galat": [{"pesan": f"Batch WIP {w['batch']} tidak ditemukan."}]})
                
    if not pakai_raw and not pakai_wip:
        return Response({"valid": False, "galat": [{"pesan": "Pilih minimal satu sumber dengan qty > 0."}]})

    susut = d.get("susut_kg", Decimal("0"))

    try:
        if pakai_wip:
            res = services.pratinjau_blending(pakai_wip, susut_kg=susut)
        else:
            res = services.pratinjau_mixing(pakai_raw, susut_kg=susut)
            
        return Response(res)
    except Exception as e:
        return Response({"valid": False, "galat": [{"pesan": str(e)}]})