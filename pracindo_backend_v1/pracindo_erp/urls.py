from django.contrib import admin
from django.urls import include, path

# TAMBAHAN BARU: Impor modul drf-spectacular
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Halaman Admin Rahasia
    path('8243e09f83b0e1e21827c2824180297939b4747cff46d22b27b2721111e87bfe/', admin.site.urls),
    

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/auth/',        include('staff_user.urls')),
    path('api/v1/master/',      include('master.urls')),
    path('api/v1/dokumen/',     include('dokumen.urls')),
    path('api/v1/inventory/',   include('inventory.urls')),
    path('api/v1/akunting/',    include('akunting.urls')),
    path('api/v1/keuangan/',    include('keuangan.urls')),
    path('api/v1/pajak/',       include('pajak.urls')),
    path('api/v1/warehouse/',   include('warehouse.urls')),
    path('api/v1/produksi/',    include('produksi.urls')),
    path('api/v1/sales-order/', include('sales_order.urls')),
    path('api/v1/logistik/',    include('logistik.urls')),
    path('api/v1/work-order/',  include('work_order.urls')),
    path('api/v1/core/',        include('core.urls')),
]