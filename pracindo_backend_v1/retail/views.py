import uuid
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

# Import seluruh model
from .models import (
    StokRetail, CabangToko, SesiKasir, TransaksiPOS, ItemTransaksi,
    AkunBukuBesar, TransaksiJurnal, DetailJurnal
)

# Import seluruh serializer
from .serializers import (
    KatalogPOSSerializer, RiwayatTransaksiSerializer, SesiKasirSerializer,
    AkunBukuBesarSerializer, TransaksiJurnalSerializer
)


class KatalogPOSAPIView(generics.ListAPIView):
    serializer_class = KatalogPOSSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cabang_aktif = CabangToko.objects.filter(aktif=True).first()
        if cabang_aktif:
            return StokRetail.objects.filter(cabang=cabang_aktif, qty__gt=0).select_related('produk')
        return StokRetail.objects.none()


class CheckoutPOSAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic 
    def post(self, request):
        cabang = CabangToko.objects.filter(aktif=True).first()
        if not cabang:
            return Response({'status': 'gagal', 'pesan': 'Cabang tidak ditemukan'}, status=status.HTTP_400_BAD_REQUEST)

        sesi = SesiKasir.objects.filter(cabang=cabang, status='AKTIF').first()
        if not sesi:
            sesi = SesiKasir.objects.create(cabang=cabang, kasir=request.user, status='AKTIF')

        keranjang = request.data.get('keranjang', [])
        subtotal = Decimal(str(request.data.get('subtotal', 0)))
        metode_bayar = request.data.get('metode_bayar', 'TUNAI')
        
        transaksi = TransaksiPOS.objects.create(
            nomor_struk=f"TRX-{uuid.uuid4().hex[:8].upper()}",
            sesi=sesi,
            subtotal=subtotal,
            pajak=Decimal('0'),
            grand_total=subtotal,
            metode_bayar=metode_bayar
        )

        for item in keranjang:
            qty_beli = int(item['qty'])
            harga_satuan = Decimal(str(item['harga']))
            stok = StokRetail.objects.select_for_update().get(cabang=cabang, produk_id=item['id'])
            
            if stok.qty < qty_beli:
                return Response({'status': 'gagal', 'pesan': f"Stok {stok.produk.nama} tidak mencukupi."}, status=status.HTTP_400_BAD_REQUEST)

            ItemTransaksi.objects.create(
                transaksi=transaksi,
                produk_id=item['id'],
                qty=qty_beli,
                harga_satuan=harga_satuan,
                subtotal=harga_satuan * Decimal(qty_beli)
            )
            
            stok.qty -= qty_beli
            stok.save()

        sesi.total_penjualan = sesi.total_penjualan + subtotal
        sesi.save()

        return Response({'status': 'sukses', 'nomor_struk': transaksi.nomor_struk}, status=status.HTTP_201_CREATED)


class RiwayatTransaksiAPIView(generics.ListAPIView):
    serializer_class = RiwayatTransaksiSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        cabang = CabangToko.objects.filter(aktif=True).first()
        return TransaksiPOS.objects.filter(sesi__cabang=cabang).order_by('-waktu_transaksi')[:50]


class SesiKasirAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cabang = CabangToko.objects.filter(aktif=True).first()
        sesi = SesiKasir.objects.filter(cabang=cabang, status='AKTIF').first()
        if sesi:
            return Response(SesiKasirSerializer(sesi).data)
        return Response({'status': 'TIDAK_ADA_SHIFT'}, status=status.HTTP_200_OK)
        
    def post(self, request):
        cabang = CabangToko.objects.filter(aktif=True).first()
        sesi = SesiKasir.objects.filter(cabang=cabang, status='AKTIF').first()
        if sesi:
            sesi.status = 'DITUTUP'
            sesi.waktu_tutup = timezone.now()
            sesi.save()
            return Response({'status': 'sukses'})
        return Response({'status': 'gagal'}, status=status.HTTP_400_BAD_REQUEST)


class AkunBukuBesarAPIView(generics.ListCreateAPIView):
    serializer_class = AkunBukuBesarSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cabang = CabangToko.objects.filter(aktif=True).first()
        return AkunBukuBesar.objects.filter(cabang=cabang)


class JurnalUmumAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        cabang = CabangToko.objects.filter(aktif=True).first()
        if not cabang:
            return Response({'status': 'gagal'}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        items = data.get('items', [])
        
        total_debit = sum(Decimal(str(i.get('debit', 0))) for i in items)
        total_kredit = sum(Decimal(str(i.get('kredit', 0))) for i in items)

        if total_debit != total_kredit:
            return Response({'status': 'gagal', 'pesan': 'Debit dan Kredit tidak balance'}, status=status.HTTP_400_BAD_REQUEST)

        jurnal = TransaksiJurnal.objects.create(
            nomor_jurnal=f"JV-{uuid.uuid4().hex[:6].upper()}",
            referensi=data.get('referensi', ''),
            keterangan=data.get('keterangan', ''),
            cabang=cabang
        )

        for item in items:
            DetailJurnal.objects.create(
                jurnal=jurnal,
                akun_id=item['akun_id'],
                debit=Decimal(str(item.get('debit', 0))),
                kredit=Decimal(str(item.get('kredit', 0)))
            )

        return Response({'status': 'sukses', 'nomor_jurnal': jurnal.nomor_jurnal}, status=status.HTTP_201_CREATED)