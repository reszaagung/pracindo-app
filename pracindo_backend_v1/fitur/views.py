import os
from django.conf import settings
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from docxtpl import DocxTemplate
from .serializers import CetakStikerPayloadSerializer

class GenerateStikerDocxAPIView(APIView):
    def post(self, request, format=None):
        serializer = CetakStikerPayloadSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            item_data = {
                'NAMA': data.get('nama_item', ''),
                'TYPE': data.get('type', ''),
                'LOT': data.get('lot', ''),
                'NET': data.get('qty', '')
            }

            jumlah_cetak = data.get('total_unit', 1)
            items = [item_data] * jumlah_cetak  
            
            context = {'items': items}

            template_path = os.path.join(settings.BASE_DIR, 'fitur', 'templates', 'stikerbesarpolos.docx')

            if not os.path.exists(template_path):
                return Response({"error": f"Template tidak ditemukan di path: {template_path}"}, status=404)

            try:
                doc = DocxTemplate(template_path)
                doc.render(context)

                response = HttpResponse(
                    content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
                filename = f"Stiker_{data.get('type', 'Item')}.docx"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                doc.save(response)
                return response
                
            except Exception as e:
                return Response({"error": str(e)}, status=500)
                
        return Response(serializer.errors, status=400)