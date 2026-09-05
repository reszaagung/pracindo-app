import os
from django.conf import settings
from django.http import HttpResponse
from django.contrib import admin
from docxtpl import DocxTemplate
from .models import HelperGenerateStikerDoc

@admin.register(HelperGenerateStikerDoc)
class HelperGenerateStikerDocAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama_item', 'tipe', 'lot', 'qty')
    actions = ['cetak_stiker_docx']

    @admin.action(description="🖨️ Cetak Stiker Gudang (DOCX)")
    def cetak_stiker_docx(self, request, queryset):
        items = []
        
        for obj in queryset:
            jumlah_cetak = obj.total_unit if obj.total_unit else 1 
            for _ in range(jumlah_cetak):
                items.append({
                    'NAMA': obj.nama_item,
                    'TYPE': obj.tipe,
                    'LOT': obj.lot,
                    'TOTAL_UNIT': obj.total_unit, 
                    'NET': obj.qty
                })

        context = {'items': items}
        template_path = os.path.join(settings.BASE_DIR, 'fitur', 'templates', 'stikerbesarpolos.docx')

        if not os.path.exists(template_path):
            self.message_user(request, f"Error: Template tidak ditemukan di {template_path}", level='error')
            return

        try:
            doc = DocxTemplate(template_path)
            doc.render(context)

            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = 'attachment; filename="Stiker_Gudang.docx"'
            
            doc.save(response)
            return response
            
        except Exception as e:
            self.message_user(request, f"Gagal merender dokumen: {str(e)}", level='error')