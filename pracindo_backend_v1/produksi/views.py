from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

from .models import Tangki, Batch, TipeProses
from .serializers import TangkiSerializer, BatchSerializer
from .services import (
    buat_batch_mixing,
    posting_mixing,
    simpan_dan_posting_mixing,
    buat_batch_blending,
    posting_blending,
    simpan_dan_posting_blending,
    pratinjau_mixing,
    pratinjau_blending,
    GalatProduksi,
    KonflikBatch
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pratinjau_batch(request):
    jenis = request.query_params.get("jenis", TipeProses.MIXING).upper()
    susut_kg = request.query_params.get("susut_kg")
    
    if jenis == TipeProses.MIXING:
        baris = request.data.get("baris", [])
        res = pratinjau_mixing(baris=baris, susut_kg=susut_kg)
    elif jenis == TipeProses.BLENDING:
        baris_sumber = request.data.get("baris_sumber", [])
        res = pratinjau_blending(baris_sumber=baris_sumber, susut_kg=susut_kg)
    else:
        return Response({"error": f"Jenis proses '{jenis}' tidak dikenal."}, status=status.HTTP_400_BAD_REQUEST)
        
    status_code = status.HTTP_200_OK if res.get("valid") else status.HTTP_422_UNPROCESSABLE_ENTITY
    return Response(res, status=status_code)


class TangkiViewSet(viewsets.ModelViewSet):
    queryset = Tangki.objects.all().order_by("kode")
    serializer_class = TangkiSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    @action(detail=False, methods=["get"])
    def rekap(self, request):
        qs = self.get_queryset()
        data = []
        for t in qs:
            vol = t.batch_aktif.aggregate(v=Coalesce(Sum("qty_kg"), Value(Decimal("0"))))["v"]
            data.append({
                "id": t.id,
                "kode": t.kode,
                "nama": t.nama,
                "kapasitas": str(t.kapasitas_kg),
                "terisi": str(vol),
                "persen": round((vol / t.kapasitas_kg) * 100, 1) if t.kapasitas_kg else 0
            })
        return Response(data)


class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.select_related("tangki", "dibuat_oleh").order_by("-id")
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        jenis = self.request.query_params.get("jenis")
        if jenis:
            qs = qs.filter(jenis=jenis)
        status_batch = self.request.query_params.get("status")
        if status_batch:
            qs = qs.filter(status=status_batch)
        return qs

    def perform_create(self, serializer):
        serializer.save(dibuat_oleh=self.request.user)

    @action(detail=False, methods=["post"], url_path="mixing")
    def mixing(self, request):
        try:
            posting = request.data.get("posting", False)
            params = {
                "nama_hasil": request.data.get("nama_hasil"),
                "tangki_id": request.data.get("tangki_id"),
                "baris": request.data.get("baris", []),
                "susut_kg": request.data.get("susut_kg"),
                "tanggal": request.data.get("tanggal"),
                "user": request.user,
            }
            if posting:
                batch = simpan_dan_posting_mixing(**params)
            else:
                batch = buat_batch_mixing(**params)
            return Response(BatchSerializer(batch).data, status=status.HTTP_201_CREATED)
        except (GalatProduksi, KonflikBatch) as e:
            return Response({"detail": str(e)}, status=getattr(e, "http", status.HTTP_400_BAD_REQUEST))
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="blending")
    def blending(self, request):
        try:
            posting = request.data.get("posting", False)
            params = {
                "nama_hasil": request.data.get("nama_hasil"),
                "tangki_id": request.data.get("tangki_id"),
                "baris_sumber": request.data.get("baris_sumber", []),
                "susut_kg": request.data.get("susut_kg"),
                "tanggal": request.data.get("tanggal"),
                "user": request.user,
            }
            if posting:
                batch = simpan_dan_posting_blending(**params)
            else:
                batch = buat_batch_blending(**params)
            return Response(BatchSerializer(batch).data, status=status.HTTP_201_CREATED)
        except (GalatProduksi, KonflikBatch) as e:
            return Response({"detail": str(e)}, status=getattr(e, "http", status.HTTP_400_BAD_REQUEST))
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="posting")
    def posting(self, request, pk=None):
        try:
            batch = self.get_object()
            if batch.jenis == TipeProses.MIXING:
                hasil = posting_mixing(batch, user=request.user)
            else:
                hasil = posting_blending(batch, user=request.user)
            return Response(BatchSerializer(hasil).data)
        except (GalatProduksi, KonflikBatch) as e:
            return Response({"detail": str(e)}, status=getattr(e, "http", status.HTTP_400_BAD_REQUEST))
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)