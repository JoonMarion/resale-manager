from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    # Public catalog
    path('', views.PublicCatalogView.as_view(), name='public_list'),
    
    # Category Management (Internal)
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/new/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
]
