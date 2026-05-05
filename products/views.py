from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
import json
from .models import Product
from .forms import ProductForm
from stock.models import Stock
from users.mixins import ProjectLoginRequiredMixin
from core.mixins import SessionSortMixin


class ProductListView(ProjectLoginRequiredMixin, SessionSortMixin, ListView):
    model = Product
    context_object_name = 'products'
    paginate_by = 10
    default_sort = 'alpha_asc'
    sort_options = {
        'alpha_asc': 'name',
        'recent': '-created_at',
    }

    def get_template_names(self):
        if self.request.htmx:
            return 'products/list_partial.html'
        return 'products/list.html'

    def get_queryset(self):
        queryset = Product.objects.filter(active=True).order_by(self.get_ordering())
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(name__icontains=q)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context


class ProductCreateView(ProjectLoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/form.html'
    success_url = reverse_lazy('products:list')

    def form_valid(self, form):
        self.object = form.save()
        initial_stock = form.cleaned_data.get('initial_stock', 0)
        Stock.objects.update_or_create(product=self.object, defaults={'quantity': initial_stock})
        if self.request.htmx:
            response = HttpResponse("", status=200)
            response['HX-Reswap'] = 'none'
            response['HX-Trigger'] = json.dumps({
                'itemCreated': '',
                'reloadProducts': '',
                'showSuccess': 'Produto criado com sucesso!',
            })
            return response
        return super().form_valid(form)


class ProductUpdateView(ProjectLoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/form.html'
    success_url = reverse_lazy('products:list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Lock price fields if stock > 0
        stock_qty = getattr(self.object.stock, 'quantity', 0) or 0
        if stock_qty > 0:
            form.fields['purchase_price'].disabled = True
            form.fields['sale_price'].disabled = True
        # Hide initial_stock in edit mode
        form.fields['initial_stock'].required = False
        form.fields['initial_stock'].widget.attrs['disabled'] = True
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        stock_qty = getattr(self.object.stock, 'quantity', 0) or 0
        ctx['is_edit'] = True
        ctx['price_locked'] = stock_qty > 0
        ctx['stock_qty'] = stock_qty
        return ctx

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse('', status=200)
            response['HX-Reswap'] = 'none'
            response['HX-Trigger'] = json.dumps({
                'itemCreated': '',
                'reloadProducts': '',
                'showSuccess': 'Produto atualizado com sucesso!',
            })
            return response
        return super().form_valid(form)


class ProductDeleteView(ProjectLoginRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('products:list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.sale_items.exists():
            if request.htmx:
                response = HttpResponse("", status=200)
                response['HX-Reswap'] = 'none'
                response['HX-Trigger'] = json.dumps({'showError': 'Não é possível excluir este produto pois está vinculado a uma venda.'})
                return response
        self.object.active = False
        self.object.save()
        if request.htmx:
            response = HttpResponse("", status=200)
            response['HX-Trigger'] = json.dumps({'showSuccess': 'Produto excluído com sucesso.'})
            return response
        return super().delete(request, *args, **kwargs)
