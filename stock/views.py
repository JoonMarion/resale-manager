from django.db import models
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Stock, StockEntry, StockExit
from .forms import StockEntryForm, StockExitForm
from products.models import Product
from users.mixins import ProjectLoginRequiredMixin
from core.mixins import SessionSortMixin
from django.db.models import Q


class StockListView(ProjectLoginRequiredMixin, SessionSortMixin, ListView):
    model = Stock
    context_object_name = 'stocks'
    paginate_by = 10
    template_name = 'stock/list.html'
    default_sort = 'alpha_asc'
    sort_options = {
        'alpha_asc': 'product__name',
        'recent': '-created_at',
        'oldest': 'created_at',
    }

    def get_template_names(self):
        if self.request.htmx:
            return 'stock/list_partial.html'
        return self.template_name

    def get_queryset(self):
        queryset = Stock.objects.filter(product__active=True).select_related('product').order_by(self.get_ordering())
        
        # Search by product name
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(product__name__icontains=q)
        
        # Filter by low stock
        low = self.request.GET.get('low')
        if low == '1':
            queryset = queryset.filter(quantity__lte=models.F('product__min_stock'))
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if there are any low stock items globally to show banner
        low_stock_qs = Stock.objects.filter(
            product__active=True,
            quantity__lte=models.F('product__min_stock')
        )
        low_stock_count = low_stock_qs.count()
        context['low_stock_count'] = low_stock_count
        context['has_low_stock'] = low_stock_count > 0
        context['q'] = self.request.GET.get('q', '')
        return context


class StockEntryCreateView(ProjectLoginRequiredMixin, CreateView):
    model = StockEntry
    form_class = StockEntryForm
    template_name = 'stock/entry_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, pk=self.kwargs.get('product_pk'))
        return context

    def form_valid(self, form):
        product = get_object_or_404(Product, pk=self.kwargs.get('product_pk'))
        entry = form.save(commit=False)
        entry.product = product
        entry.save()

        # Update Stock quantity
        stock, created = Stock.objects.get_or_create(product=product)
        stock.quantity += entry.quantity
        stock.save()

        if self.request.htmx:
            # Return the updated partial for this specific stock item? 
            # Or just success message and reload list. 
            # User requested "retorna fragment atualizado do card"
            return HttpResponse(
                '<script>'
                'closeModal();'
                'htmx.trigger("#stock-list", "reload");'
                '</script>'
            )
        return HttpResponse("Sucesso!")


class StockExitCreateView(ProjectLoginRequiredMixin, CreateView):
    model = StockExit
    form_class = StockExitForm
    template_name = 'stock/exit_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, pk=self.kwargs.get('product_pk'))
        return context

    def form_valid(self, form):
        product = get_object_or_404(Product, pk=self.kwargs.get('product_pk'))
        exit_obj = form.save(commit=False)
        exit_obj.product = product
        exit_obj.save()

        # Update Stock quantity
        stock, created = Stock.objects.get_or_create(product=product)
        stock.quantity -= exit_obj.quantity
        stock.save()

        if self.request.htmx:
            return HttpResponse(
                '<script>'
                'closeModal();'
                'htmx.trigger("#stock-list", "reload");'
                '</script>'
            )
        return HttpResponse("Sucesso!")
