from django.urls import path
from .views import StockListView, StockEntryCreateView, StockExitCreateView

app_name = 'stock'

urlpatterns = [
    path('', StockListView.as_view(), name='list'),
    path('entry/<int:product_pk>/', StockEntryCreateView.as_view(), name='entry_create'),
    path('exit/<int:product_pk>/', StockExitCreateView.as_view(), name='exit_create'),
]
