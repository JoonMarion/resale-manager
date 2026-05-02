from django.urls import path
from .views import CustomerListView, CustomerCreateView, CustomerDeleteView, CustomerUpdateView

app_name = 'customers'

urlpatterns = [
    path('', CustomerListView.as_view(), name='list'),
    path('create/', CustomerCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', CustomerUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', CustomerDeleteView.as_view(), name='delete'),
]
