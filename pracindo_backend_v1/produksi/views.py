from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import Tangki, Batch, TipeProses
from .serializers import TangkiSerializer, BatchSerializer
from .services import (
    simpan_dan_posting_mixing,
    simpan_dan_posting_blending,
    posting_mixing,
    posting_blending,
    pratinjau_mixing,
    pratinjau_blending,
    GalatProduksi,
    KonflikBatch
)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pratinjau_batch(request):
    jenis = request.data.get("jenis", request.query_params.get("jenis", TipeProses.MIXING)).upper()
    susut_kg = request.data.get("susut_kg", request.query_params.get("susut_kg"))
    
    if jenis == TipeProses.MIXING:
        baris = request.data.get("baris", request.data.get("materials", []))
        res = pratinjau_mixing(baris=baris, susut_kg=susut_kg)
    elif jenis == TipeProses.BLENDING:
        baris_sumber = request.data.get("baris_sumber", request.data.get("wip_sources", []))
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
        from .services import saldo_batch 
        
        qs = self.get_queryset()
        data = []
        for t in qs:
            vol = sum((saldo_batch(b).sisa_qty for b in t.batch_set.filter(status="POSTED")), Decimal("0"))
            
            data.append({
                "id": t.id,
                "kode": t.kode,
                "nama": t.nama,
                "kapasitas": str(t.kapasitas_kg) if t.kapasitas_kg else "0",
                "terisi": str(vol),
                "persen": round((float(vol) / float(t.kapasitas_kg)) * 100, 1) if t.kapasitas_kg and t.kapasitas_kg > 0 else 0
            })
        return Response(data)

    @action(detail=True, methods=["get"])
    def saldo(self, request, pk=None):
        from .services import saldo_batch
        from decimal import Decimal
        
        tangki = self.get_object()
        batches_in_tank = tangki.batch_set.filter(status="POSTED").order_by("-waktu")
        
        total_qty = Decimal("0")
        total_nilai = Decimal("0")
        batches_data = []
        
        for b in batches_in_tank:
            s = saldo_batch(b)
            if s.sisa_qty > 0:
                total_qty += s.sisa_qty
                total_nilai += s.sisa_nilai
                batches_data.append({
                    "id": b.id,
                    "nomor": b.nomor,
                    "nama_hasil": b.nama_hasil,
                    "sisa_qty": str(s.sisa_qty),
                    "harga_per_kg": str(s.harga_per_kg)
                })
        
        harga_rata = (total_nilai / total_qty) if total_qty > 0 else Decimal("0")
        harga_unik = set(b["harga_per_kg"] for b in batches_data)
        harga_beragam = len(harga_unik) > 1

        return Response({
            "sisa_qty": str(total_qty),
            "sisa_nilai": str(total_nilai),
            "harga_per_kg": str(harga_rata),
            "harga_beragam": harga_beragam,
            "batches": batches_data
        })


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
            params = {
                "nama_hasil": request.data.get("nama_hasil"),
                "tangki_id": request.data.get("tangki_id"),
                "baris": request.data.get("baris", request.data.get("materials", [])),
                "susut_kg": request.data.get("susut_kg"),
                "tanggal": request.data.get("tanggal"),
                "user": request.user,
            }
            batch = simpan_dan_posting_mixing(**params)
            return Response(BatchSerializer(batch).data, status=status.HTTP_201_CREATED)
        except (GalatProduksi, KonflikBatch) as e:
            return Response({"detail": str(e)}, status=getattr(e, "http", status.HTTP_400_BAD_REQUEST))
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="blending")
    def blending(self, request):
        try:
            params = {
                "nama_hasil": request.data.get("nama_hasil"),
                "tangki_id": request.data.get("tangki_id"),
                "baris_sumber": request.data.get("baris_sumber", request.data.get("wip_sources", [])),
                "susut_kg": request.data.get("susut_kg"),
                "tanggal": request.data.get("tanggal"),
                "user": request.user,
            }
            batch = simpan_dan_posting_blending(**params)
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