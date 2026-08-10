# sales_order/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalesOrderViewSet

app_name = 'sales_order'

router = DefaultRouter()
router.register('', SalesOrderViewSet, basename='salesorder')

urlpatterns = [
    path('', include(router.urls)),
]