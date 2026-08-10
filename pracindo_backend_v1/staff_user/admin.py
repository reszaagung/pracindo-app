from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import DataKepegawaian, Jabatan, Profil, RiwayatAkses


@admin.register(Jabatan)
class JabatanAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'departemen', 'level', 'aktif')
    list_filter = ('departemen', 'aktif')
    search_fields = ('kode', 'nama')


class DataKepegawaianInline(admin.StackedInline):
    model = DataKepegawaian
    extra = 0
    can_delete = False


@admin.register(Profil)
class ProfilAdmin(UserAdmin):
    list_display = ('username', 'nama_lengkap', 'nip', 'role', 'jabatan',
                    'status_kerja', 'is_active')
    list_filter = ('role', 'status_kerja', 'is_active', 'jabatan__departemen')
    search_fields = ('username', 'first_name', 'last_name', 'nip')
    list_select_related = ('jabatan',)
    filter_horizontal = ('entitas_diizinkan', 'groups', 'user_permissions')
    readonly_fields = ('disetujui_oleh', 'disetujui_pada', 'ditolak_pada',
                       'last_login', 'date_joined')
    inlines = [DataKepegawaianInline]

    fieldsets = UserAdmin.fieldsets + (
        ('Kepegawaian', {
            'fields': ('nip', 'role', 'jabatan', 'atasan', 'foto', 'nomor_hp',
                       'status_kerja', 'tanggal_masuk', 'tanggal_keluar'),
        }),
        ('Akses entitas', {
            'fields': ('entitas_default', 'entitas_diizinkan'),
            'description': 'Entitas diizinkan kosong berarti boleh semua.',
        }),
        ('Persetujuan', {
            'fields': ('disetujui_oleh', 'disetujui_pada',
                       'ditolak_pada', 'alasan_tolak'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Kepegawaian', {'fields': ('role', 'jabatan', 'nomor_hp')}),
    )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RiwayatAkses)
class RiwayatAksesAdmin(admin.ModelAdmin):
    list_display = ('waktu', 'username_dicoba', 'profil', 'berhasil',
                    'alasan_gagal', 'ip')
    list_filter = ('berhasil', 'waktu')
    search_fields = ('username_dicoba', 'ip')
    readonly_fields = [f.name for f in RiwayatAkses._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
