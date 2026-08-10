# sales_order/views.py
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from django.db.models import Prefetch

# Sesuaikan import permission ini dengan yang Anda miliki di core/staff_user
# from staff_user.permissions import SudahLogin, AdminAtauAkunting

from .models import SalesOrder, StatusSO
from .serializers import SalesOrderSerializer

class SalesOrderViewSet(viewsets.ModelViewSet):
    # Optimasi query relasi menggunakan select_related dan prefetch_related
    queryset = SalesOrder.objects.select_related('pelanggan').prefetch_related(
        'items__produk__satuan'
    ).order_by('-tanggal', '-nomor_so')
    
    serializer_class = SalesOrderSerializer
    filterset_fields = ['status', 'pelanggan']
    search_fields = ['nomor_so', 'pelanggan__nama']

    # def get_permissions(self):
    #     if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
    #         return [SudahLogin()]
    #     return [AdminAtauAkunting()]

    def perform_destroy(self, instance):
        if instance.status != StatusSO.DRAFT:
            raise ValidationError("Hanya Sales Order berstatus DRAFT yang bisa dihapus.")
        instance.delete()