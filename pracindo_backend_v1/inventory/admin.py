
from django.contrib import admin

from .models import (
    Kemasan, MutasiKlaim, Packing, Pembelian, SaldoEntitas, SaldoPool,
    StatusDokumen, SumberPembelian,
)


class TanpaTulis:
    """
    Model append-only atau turunan: tidak bisa ditambah, diubah, atau
    dihapus lewat admin.

    Menutup hanya `add` tidak cukup. Kalau `change` tetap terbuka,
    menekan Simpan memanggil save() yang melempar ValueError -- muncul
    sebagai 500, bukan sebagai penolakan yang bisa dibaca.
    """
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class KunciSetelahPosting:
    """
    DRAFT bisa disunting, POSTED dan VOID tidak.

    Angka pada dokumen POSTED adalah dasar tagihan yang sudah terbit.
    Mengubahnya lewat admin berarti mengubah tagihan tanpa jejak, dan
    pemeriksaan invariant baru menemukannya belakangan -- setelah tidak
    ada lagi yang ingat apa yang diubah.
    """
    readonly_dasar = ()

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != StatusDokumen.DRAFT:
            return [f.name for f in obj._meta.fields]
        return list(self.readonly_dasar)

    def has_delete_permission(self, request, obj=None):
        return obj is None or obj.status == StatusDokumen.DRAFT



@admin.register(Kemasan)
class KemasanAdmin(admin.ModelAdmin):
    list_display = ("nama", "bobot_kg", "aktif")
    list_filter = ("aktif",)
    search_fields = ("nama",)


@admin.register(SaldoPool)
class SaldoPoolAdmin(TanpaTulis, admin.ModelAdmin):
    list_display = ("grup_bahan", "produk", "qty_kg", "nilai", "harga_rata",
                    "kosong_bernilai", "diubah_pada")
    list_filter = ("grup_bahan",)
    search_fields = ("produk__kode", "produk__nama")
    list_select_related = ("grup_bahan", "produk")

    @admin.display(description="Harga / Kg")
    def harga_rata(self, obj):
        return f"Rp {obj.harga_rata:,.2f}"

    @admin.display(boolean=True, description="Kosong tapi bernilai")
    def kosong_bernilai(self, obj):
        # Isinya akan keluar gratis pada pengambilan berikutnya.
        return obj.qty_kg == 0 and obj.nilai != 0


@admin.register(SaldoEntitas)
class SaldoEntitasAdmin(TanpaTulis, admin.ModelAdmin):
    """
    CACHE, bukan sumber kebenaran. Sumbernya MutasiKlaim.

    Mengetik angka di sini membuat cache berbeda dari buku besar, dan
    `rekalkulasi_saldo` akan menimpanya kembali -- setelah laporan
    terlanjur terbit dengan angka yang salah.
    """
    list_display = ("entitas", "grup", "qty_setor", "qty_tarik",
                    "total_setor", "total_tarik", "total_rugi", "saldo",
                    "status")
    list_filter = ("entitas__grup_bahan",)
    search_fields = ("entitas__kode", "entitas__nama")
    list_select_related = ("entitas", "entitas__grup_bahan")

    @admin.display(description="Grup")
    def grup(self, obj):
        return obj.entitas.grup_bahan.kode

    @admin.display(description="Status")
    def status(self, obj):
        if obj.saldo == 0:
            return "IMPAS"
        return "KLAIM" if obj.saldo > 0 else "HUTANG"


@admin.register(Pembelian)
class PembelianAdmin(KunciSetelahPosting, admin.ModelAdmin):
    list_display = ("nomor", "tanggal", "no_po", "entitas", "grup_bahan",
                    "produk", "qty_kg", "harga_per_kg", "nilai", "sumber",
                    "status")
    list_filter = ("status", "sumber", "tanggal", "grup_bahan", "entitas")
    search_fields = ("nomor", "no_po", "produk__kode", "entitas__kode")
    date_hierarchy = "tanggal"
    list_select_related = ("entitas", "grup_bahan", "produk")
    readonly_dasar = ("nomor", "nilai", "status", "sumber", "penerimaan_item",
                      "dibuat_oleh", "dibuat_pada", "posted_at")


    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Packing)
class PackingAdmin(KunciSetelahPosting, admin.ModelAdmin):
    list_display = ("nomor", "tanggal", "entitas", "batch", "kemasan",
                    "total_unit", "qty_kg", "harga_per_kg", "nilai_hpp",
                    "menghabiskan", "status")
    list_filter = ("status", "tanggal", "kemasan", "entitas")
    search_fields = ("nomor", "entitas__kode", "batch__nomor")
    date_hierarchy = "tanggal"
    list_select_related = ("entitas", "batch", "kemasan")
    readonly_dasar = ("nomor", "harga_per_kg", "nilai_hpp", "menghabiskan",
                      "status", "dibuat_oleh", "dibuat_pada", "posted_at")


@admin.register(MutasiKlaim)
class MutasiKlaimAdmin(TanpaTulis, admin.ModelAdmin):
    """
    Append-only. Koreksi dilakukan dengan entri lawan (PENYESUAIAN),
    bukan dengan mengubah atau menghapus. Buku yang bisa dihapus bukan
    buku besar.
    """
    list_display = ("waktu", "entitas", "grup_bahan", "tipe", "arah_label",
                    "qty_kg", "nilai", "ref", "keterangan")
    list_filter = ("tipe", "grup_bahan", "entitas", "waktu")
    search_fields = ("ref_type", "keterangan", "entitas__kode")
    date_hierarchy = "waktu"
    list_select_related = ("entitas", "grup_bahan")

    @admin.display(description="Arah")
    def arah_label(self, obj):
        return "MASUK (+)" if obj.arah > 0 else "KELUAR (−)"

    @admin.display(description="Referensi")
    def ref(self, obj):
        return f"{obj.ref_type}#{obj.ref_id}"