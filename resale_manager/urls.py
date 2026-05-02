"""
URL configuration for resale_manager project.
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Apps
    path('', include('users.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('produtos/', include('products.urls')),
    path('clientes/', include('customers.urls')),
    path('vendas/', include('sales.urls')),
    path('estoque/', include('stock.urls')),

    # Root redirect to dashboard
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
]
