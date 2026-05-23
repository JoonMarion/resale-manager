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
    
    # Orders
    path('pedido/<uuid:order_id>/resumo/', views.OrderSummaryView.as_view(), name='order_summary'),
    
    # Cart
    path('carrinho/', views.CartDetailView.as_view(), name='cart_detail'),
    path('carrinho/adicionar/<int:product_id>/', views.AddToCartView.as_view(), name='cart_add'),
    path('carrinho/remover/<int:product_id>/', views.RemoveFromCartView.as_view(), name='cart_remove'),
    path('carrinho/atualizar/<int:product_id>/', views.UpdateCartView.as_view(), name='cart_update'),
    path('finalizar/', views.CheckoutView.as_view(), name='checkout'),
]
