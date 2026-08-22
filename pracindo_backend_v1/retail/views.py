import uuid
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import (
    StokRetail, CabangToko, SesiKasir, TransaksiPOS, ItemTransaksi,
    AkunBukuBesar, TransaksiJurnal, DetailJurnal,
    PelangganRetail, SalesRetail, BukuPiutangRetail, BonusSales,BukuPiutangRetailSerializer
)

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

        metode_bayar = request.data.get('metode_bayar', 'TUNAI')
        pelanggan_id = request.data.get('pelanggan_id')
        sales_id = request.data.get('sales_id')

        if metode_bayar == 'TEMPO' and not pelanggan_id:
            return Response({'status': 'gagal', 'pesan': 'Transaksi TEMPO wajib memilih Pelanggan.'}, status=status.HTTP_400_BAD_REQUEST)

        sesi = SesiKasir.objects.filter(cabang=cabang, status='AKTIF').first()
        if not sesi:
            sesi = SesiKasir.objects.create(cabang=cabang, kasir=request.user, status='AKTIF')

        keranjang = request.data.get('keranjang', [])
        subtotal = Decimal(str(request.data.get('subtotal', 0)))
        
        transaksi = TransaksiPOS.objects.create(
            nomor_struk=f"TRX-{uuid.uuid4().hex[:8].upper()}",
            sesi=sesi,
            pelanggan_id=pelanggan_id,
            sales_id=sales_id,
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

        if metode_bayar == 'TEMPO':
            pelanggan = PelangganRetail.objects.get(id=pelanggan_id)
            BukuPiutangRetail.objects.create(
                pelanggan=pelanggan,
                transaksi=transaksi,
                tanggal_piutang=timezone.now().date(),
                jatuh_tempo=timezone.now().date() + timedelta(days=pelanggan.default_tempo_hari),
                total_piutang=subtotal
            )

        if sales_id:
            sales = SalesRetail.objects.get(id=sales_id)
            nominal_bonus = subtotal * (sales.persentase_bonus / Decimal('100'))
            if nominal_bonus > 0:
                BonusSales.objects.create(
                    sales=sales,
                    transaksi=transaksi,
                    tanggal=timezone.now().date(),
                    nominal_bonus=nominal_bonus
                )

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

    def get(self, request):
        cabang = CabangToko.objects.filter(aktif=True).first()
        jurnal = TransaksiJurnal.objects.filter(cabang=cabang).prefetch_related('item_jurnal__akun')
        return Response(TransaksiJurnalSerializer(jurnal, many=True).data)

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

class PelangganRetailAPIView(generics.ListAPIView):
    serializer_class = PelangganRetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cabang = CabangToko.objects.filter(aktif=True).first()
        return PelangganRetail.objects.filter(cabang=cabang).select_related('sales')


class SalesRetailAPIView(generics.ListAPIView):
    serializer_class = SalesRetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cabang = CabangToko.objects.filter(aktif=True).first()
        return SalesRetail.objects.filter(cabang=cabang, aktif=True)

class DaftarPiutangAPIView(generics.ListAPIView):
    serializer_class = BukuPiutangRetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cabang = CabangToko.objects.filter(aktif=True).first()
        # Hanya tampilkan piutang dari pelanggan di cabang ini
        return BukuPiutangRetail.objects.filter(pelanggan__cabang=cabang).order_by('jatuh_tempo')


class BayarPiutangAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        try:
            piutang = BukuPiutangRetail.objects.get(id=pk)
        except BukuPiutangRetail.DoesNotExist:
            return Response({'status': 'gagal', 'pesan': 'Data piutang tidak ditemukan.'}, status=status.HTTP_404_NOT_FOUND)

        nominal = Decimal(str(request.data.get('nominal', 0)))
        metode_bayar = request.data.get('metode_bayar', 'TUNAI')

        if nominal <= 0:
            return Response({'status': 'gagal', 'pesan': 'Nominal pembayaran tidak valid.'}, status=status.HTTP_400_BAD_REQUEST)

        if nominal > piutang.sisa_piutang:
            return Response({'status': 'gagal', 'pesan': 'Nominal melebihi sisa piutang.'}, status=status.HTTP_400_BAD_REQUEST)
        RiwayatBayarPiutang.objects.create(
            piutang=piutang,
            tanggal_bayar=timezone.now().date(),
            nominal=nominal,
            metode_bayar=metode_bayar
        )

        cabang = piutang.pelanggan.cabang
        sesi = SesiKasir.objects.filter(cabang=cabang, status='AKTIF').first()
        if sesi and metode_bayar == 'TUNAI':
            sesi.total_penjualan = sesi.total_penjualan + nominal
            sesi.save()

        return Response({'status': 'sukses', 'pesan': 'Pembayaran berhasil dicatat.'}, status=status.HTTP_200_OK)