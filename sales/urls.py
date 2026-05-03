from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.SaleListView.as_view(), name='list'),
    path('nova/', views.SaleCreateView.as_view(), name='create'),
    path('<int:pk>/', views.SaleDetailView.as_view(), name='detail'),
    path('<int:pk>/pagar/', views.SaleMarkPaidView.as_view(), name='mark_paid'),
    path('<int:pk>/delete/', views.SaleDeleteView.as_view(), name='delete'),
    path('<int:pk>/comprovante/', views.SaleReceiptView.as_view(), name='receipt'),
]
