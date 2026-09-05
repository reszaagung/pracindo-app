from django.urls import path
from .views import GenerateStikerDocxAPIView


app_name = 'fitur'
urlpatterns = [
    path('generate-stiker-docx/', GenerateStikerDocxAPIView.as_view(), name='generate-stiker-docx'),
]