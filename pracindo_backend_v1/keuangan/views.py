from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from core.models import Entitas
from .models import PengeluaranKas, RekeningBank
from .serializers import PengeluaranKasSerializer
from .services import catat_pengeluaran

class PengeluaranViewSet(viewsets.ModelViewSet):
    queryset = PengeluaranKas.objects.all().select_related('entitas', 'mutasi').order_by('-id')
    serializer_class = PengeluaranKasSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        entitas_kode = self.request.query_params.get('entitas')
        if entitas_kode:
            qs = qs.filter(entitas__kode=entitas_kode)
        return qs

    def create(self, request, *args, **kwargs):
        try:
            entitas_obj = Entitas.objects.get(kode=request.data.get('entitas'))
            
            pengeluaran = catat_pengeluaran(
                entitas_id=entitas_obj.id,
                kategori=request.data.get('kategori'),
                keterangan=request.data.get('nama_pengeluaran'),
                pemohon=request.data.get('pemohon'),
                nominal=request.data.get('nominal'),
                user=request.user,
                bukti_nota=request.FILES.get('bukti_nota')
            )
            return Response({'success': True, 'id': pengeluaran.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            pesan = e.message if hasattr(e, 'message') else str(e)
            return Response({'detail': pesan}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='dashboard-summary')
    def dashboard_summary(self, request):
        entitas_kode = request.query_params.get('entitas', 'PT')
        rek = RekeningBank.objects.filter(entitas__kode=entitas_kode, jenis='KAS_KECIL').first()
        saldo_kas = rek.saldo if rek else 0
        total_out = PengeluaranKas.objects.filter(entitas__kode=entitas_kode).aggregate(tot=Sum('nominal'))['tot'] or 0

        return Response({
            'saldo_kas': saldo_kas,
            'total_pengeluaran': total_out,
            'total_pemasukan': 0
        })