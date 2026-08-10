"""
Serializer Papan Tugas — work_order/serializers.py

DUA BENTUK BERBEDA, DISENGAJA

    WorkOrderRingkasSerializer   untuk list dan mading. TANPA pesan_chat.
    WorkOrderSerializer          untuk detail dan aksi. DENGAN pesan_chat.

Versi sebelumnya menyertakan seluruh pesan di setiap item daftar. Satu WO
dengan 200 pesan mengirim 200 pesan setiap kali papan dimuat, dikalikan
jumlah WO di halaman itu. prefetch_related mencegah N+1 query, tapi tidak
mengecilkan payload.
"""
from rest_framework import serializers

from staff_user.models import Profil

from .models import (
    AturanSelesai, DetailPesananProduksi, Kategori, WorkOrder,
    WorkOrderPenugasan, WorkOrderPesan,
)


def _nama(user):
    if not user:
        return None
    return getattr(user, 'nama_lengkap', None) or user.get_username()


class ProfilStaffRingkasSerializer(serializers.ModelSerializer):
    # jabatan sebelumnya dikirim sebagai ID mentah -- frontend menerima angka
    # dan tidak bisa menampilkannya.
    jabatan_nama = serializers.CharField(source='jabatan.nama',
                                         read_only=True, default=None)

    class Meta:
        model = Profil
        fields = ['id', 'nama_lengkap', 'jabatan', 'jabatan_nama', 'role']


class PenugasanSerializer(serializers.ModelSerializer):
    staff_nama = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrderPenugasan
        fields = ['id', 'staff', 'staff_nama', 'is_pic', 'is_selesai_personal']

    def get_staff_nama(self, obj):
        return _nama(obj.staff)


class PesanChatSerializer(serializers.ModelSerializer):
    # Sebelumnya memakai pengirim.username, sementara penugasan memakai
    # nama_lengkap -- di layar yang sama muncul "Sri Wahyuni" dan "swahyuni".
    pengirim_nama = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrderPesan
        fields = ['id', 'pengirim', 'pengirim_nama', 'teks', 'dibuat_pada']

    def get_pengirim_nama(self, obj):
        return _nama(obj.pengirim)


class DetailProduksiSerializer(serializers.ModelSerializer):
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)
    stiker_display = serializers.CharField(source='get_stiker_display', read_only=True)

    class Meta:
        model = DetailPesananProduksi
        fields = ['nama_item', 'unit', 'unit_display', 'stiker', 'stiker_display']


class WorkOrderRingkasSerializer(serializers.ModelSerializer):
    """Bentuk daftar. Tanpa pesan, hanya jumlahnya."""

    penugasan = PenugasanSerializer(many=True, read_only=True)
    detail_produksi = DetailProduksiSerializer(read_only=True)

    kategori_label = serializers.CharField(source='get_kategori_display', read_only=True)
    aturan_label = serializers.CharField(
        source='get_aturan_penyelesaian_display', read_only=True)

    dibuat_oleh_nama = serializers.SerializerMethodField()
    diselesaikan_oleh_nama = serializers.SerializerMethodField()
    terlambat = serializers.BooleanField(read_only=True)
    jumlah_pesan = serializers.IntegerField(read_only=True)
    progres = serializers.SerializerMethodField()
    saya_ditandai = serializers.SerializerMethodField()
    saya_sudah_menandai = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrder
        fields = [
            'id', 'nomor', 'kategori', 'kategori_label', 'judul', 'deskripsi',
            'aturan_penyelesaian', 'aturan_label', 'tanggal', 'deadline',
            'selesai', 'catatan_selesai', 'waktu_selesai', 'terlambat',
            'dibuat_oleh_nama', 'diselesaikan_oleh_nama', 'dibuat_pada',
            'penugasan', 'detail_produksi', 'jumlah_pesan', 'progres',
            'saya_ditandai', 'saya_sudah_menandai',
        ]

    def get_dibuat_oleh_nama(self, obj):
        return _nama(obj.dibuat_oleh)

    def get_diselesaikan_oleh_nama(self, obj):
        return _nama(obj.diselesaikan_oleh)

    def get_progres(self, obj):
        """Hanya bermakna untuk aturan SEMUA, tapi selalu dikirim supaya
        bentuk responsnya tidak berubah-ubah."""
        sudah, total = obj.progres_penyelesaian
        return {'sudah': sudah, 'total': total}

    def _penugasan_saya(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if not user or not user.is_authenticated:
            return None
        return next((p for p in obj.penugasan.all() if p.staff_id == user.id), None)

    def get_saya_ditandai(self, obj):
        """Dipakai frontend untuk memutuskan menampilkan tombol atau tidak.
        Backend tetap memvalidasi ulang -- ini kejelasan, bukan pengamanan."""
        return self._penugasan_saya(obj) is not None

    def get_saya_sudah_menandai(self, obj):
        p = self._penugasan_saya(obj)
        return bool(p and p.is_selesai_personal)


class WorkOrderSerializer(WorkOrderRingkasSerializer):
    """Bentuk detail. Dengan pesan."""

    pesan_chat = PesanChatSerializer(many=True, read_only=True)

    class Meta(WorkOrderRingkasSerializer.Meta):
        fields = WorkOrderRingkasSerializer.Meta.fields + ['pesan_chat']


# =========================================================
# TULIS
# =========================================================

class DetailProduksiInputSerializer(serializers.Serializer):
    nama_item = serializers.CharField(max_length=255)
    unit = serializers.ChoiceField(
        choices=[c[0] for c in DetailPesananProduksi.UNIT_CHOICES])
    stiker = serializers.ChoiceField(
        choices=[c[0] for c in DetailPesananProduksi.STIKER_CHOICES])


class BuatWorkOrderSerializer(serializers.Serializer):
    judul = serializers.CharField(max_length=255)
    kategori = serializers.ChoiceField(choices=Kategori.choices,
                                       default=Kategori.UMUM)
    aturan_penyelesaian = serializers.ChoiceField(
        choices=AturanSelesai.choices, default=AturanSelesai.SALAH_SATU)
    deskripsi = serializers.CharField(required=False, allow_blank=True, default='')
    tanggal = serializers.DateField(required=False, allow_null=True)
    deadline = serializers.DateField(required=False, allow_null=True)

    staff_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False)
    pic_id = serializers.IntegerField(required=False, allow_null=True)
    detail_produksi = DetailProduksiInputSerializer(required=False, allow_null=True)


class UbahWorkOrderSerializer(serializers.Serializer):
    """
    Semua opsional. Yang tidak dikirim tidak diubah.

    Versi sebelumnya tidak punya update(), sehingga PATCH dengan
    detail_produksi melempar AssertionError dari raise_errors_on_nested_writes
    -- 500 yang pesannya tidak menyebut field mana. staff_ids dan pic_id juga
    diabaikan tanpa suara, jadi penugasan tidak bisa diubah setelah dibuat.
    """
    judul = serializers.CharField(max_length=255, required=False)
    kategori = serializers.ChoiceField(choices=Kategori.choices, required=False)
    aturan_penyelesaian = serializers.ChoiceField(
        choices=AturanSelesai.choices, required=False)
    deskripsi = serializers.CharField(required=False, allow_blank=True)
    deadline = serializers.DateField(required=False, allow_null=True)

    staff_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=False)
    pic_id = serializers.IntegerField(required=False, allow_null=True)
    detail_produksi = DetailProduksiInputSerializer(required=False, allow_null=True)


class SetujuiSerializer(serializers.Serializer):
    catatan = serializers.CharField(required=False, allow_blank=True, default='')


class BukaKembaliSerializer(serializers.Serializer):
    alasan = serializers.CharField(allow_blank=False, max_length=500)


class KirimPesanSerializer(serializers.Serializer):
    teks = serializers.CharField(allow_blank=False)
