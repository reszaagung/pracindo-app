# sales_order/serializers.py
from rest_framework import serializers
from django.db import transaction
from .models import SalesOrder, SalesOrderItem

class SalesOrderItemSerializer(serializers.ModelSerializer):
    produk_nama = serializers.CharField(source='produk.nama', read_only=True)
    satuan_kode = serializers.CharField(source='produk.satuan.kode', read_only=True)

    class Meta:
        model = SalesOrderItem
        fields = ['id', 'produk', 'produk_nama', 'satuan_kode', 'qty', 'harga_jual', 'subtotal']
        read_only_fields = ['subtotal']


class SalesOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True)
    pelanggan_nama = serializers.CharField(source='pelanggan.nama', read_only=True)

    class Meta:
        model = SalesOrder
        fields = [
            'id', 'nomor_so', 'tanggal', 'pelanggan', 'pelanggan_nama',
            'catatan', 'status', 'ppn_persen', 'subtotal',
            'ppn_nominal', 'grand_total', 'items'
        ]
        read_only_fields = ['nomor_so', 'subtotal', 'ppn_nominal', 'grand_total']

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # 1. Buat dokumen header
        so = SalesOrder.objects.create(**validated_data)

        total_subtotal = 0
        # 2. Buat rincian item
        for item_data in items_data:
            item = SalesOrderItem.objects.create(sales_order=so, **item_data)
            total_subtotal += item.subtotal

        # 3. Kalkulasi ulang total dokumen di header
        so.subtotal = total_subtotal
        so.ppn_nominal = (so.ppn_persen / 100) * total_subtotal
        so.grand_total = so.subtotal + so.ppn_nominal
        so.save()

        return so

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        # Update field header
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Jika item dikirim ulang, cara paling aman di ERP adalah menghapus item lama 
        # dan menggantinya dengan daftar item baru (Replace All)
        if items_data is not None:
            instance.items.all().delete()
            
            total_subtotal = 0
            for item_data in items_data:
                item = SalesOrderItem.objects.create(sales_order=instance, **item_data)
                total_subtotal += item.subtotal
            
            instance.subtotal = total_subtotal
            instance.ppn_nominal = (instance.ppn_persen / 100) * total_subtotal
            instance.grand_total = instance.subtotal + instance.ppn_nominal
        
        instance.save()
        return instance