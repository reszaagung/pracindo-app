from django.contrib import admin

from .models import JejakAktivitas


@admin.register(JejakAktivitas)
class JejakAktivitasAdmin(admin.ModelAdmin):
    list_display = ('waktu', 'oleh', 'aksi', 'label_objek',
                    'perpindahan', 'entitas')
    list_filter = ('aksi', 'entitas', 'waktu', 'content_type')
    search_fields = ('label_objek', 'alasan')
    list_select_related = ('oleh', 'entitas', 'content_type')
    readonly_fields = [f.name for f in JejakAktivitas._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
