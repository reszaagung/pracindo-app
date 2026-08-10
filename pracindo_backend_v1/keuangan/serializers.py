from rest_framework import serializers
from .models import PengeluaranKas

class PengeluaranKasSerializer(serializers.ModelSerializer):
    # Mapping otomatis agar cocok dengan kebutuhan tabel di Frontend Vue
    id_transaksi = serializers.CharField(source='mutasi.referensi', read_only=True, default='PROSES')
    tanggal = serializers.DateTimeField(source='dibuat_pada', read_only=True)
    entitas = serializers.CharField(source='entitas.kode', read_only=True)
    nama_pengeluaran = serializers.CharField(source='keterangan', read_only=True)

    class Meta:
        model = PengeluaranKas
        fields = [
            'id', 'id_transaksi', 'tanggal', 'entitas', 
            'kategori', 'nama_pengeluaran', 'pemohon', 
            'nominal', 'bukti_nota'
        ]