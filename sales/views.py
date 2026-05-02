import json

from django.views.generic import ListView, DetailView, DeleteView
from django.views import View
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.contrib import messages

from .models import Sale
from .forms import SaleForm, SaleItemFormSet
from products.models import Product
from users.mixins import ProjectLoginRequiredMixin
from stock.models import Stock


class SaleListView(ProjectLoginRequiredMixin, ListView):
    model = Sale
    context_object_name = 'sales'
    paginate_by = 10

    def get_template_names(self):
        if self.request.htmx:
            return 'sales/list_partial.html'
        return 'sales/list.html'

    def get_queryset(self):
        queryset = Sale.objects.select_related('customer').prefetch_related('items').order_by('-sale_date')
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(customer__name__icontains=q)
        status = self.request.GET.get('status', 'all')
        if status == 'paid':
            queryset = queryset.filter(is_paid=True)
        elif status == 'pending':
            queryset = queryset.filter(is_paid=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', 'all')
        context['q'] = self.request.GET.get('q', '')
        return context


class SaleDetailView(ProjectLoginRequiredMixin, DetailView):
    model = Sale
    template_name = 'sales/detail.html'
    context_object_name = 'sale'

    def get_queryset(self):
        return Sale.objects.select_related('customer').prefetch_related('items__product')


class SaleMarkPaidView(ProjectLoginRequiredMixin, View):
    def post(self, request, pk):
        sale = get_object_or_404(Sale, pk=pk)
        sale.is_paid = True
        sale.save(update_fields=['is_paid'])
        html = render_to_string('sales/_badge.html', {'sale': sale}, request=request)
        return HttpResponse(html)


class SaleDeleteView(ProjectLoginRequiredMixin, DeleteView):
    model = Sale
    success_url = reverse_lazy('sales:list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Return items to stock
        for item in self.object.items.all():
            stock, created = Stock.objects.get_or_create(product=item.product)
            stock.quantity = (stock.quantity or 0) + (item.quantity or 0)
            stock.save()
        self.object.delete()
        messages.success(request, 'Venda excluída e itens retornaram ao estoque.')
        if request.htmx:
            response = HttpResponse('', status=200)
            response['HX-Reswap'] = 'none'
            response['HX-Redirect'] = str(reverse_lazy('sales:list'))
            return response
        return redirect(self.success_url)


class SaleCreateView(ProjectLoginRequiredMixin, View):
    def _build_context(self, form, formset):
        prices = {
            str(p.pk): str(p.sale_price)
            for p in Product.objects.filter(active=True)
        }
        return {'form': form, 'formset': formset, 'product_prices_json': json.dumps(prices)}

    def get(self, request):
        form = SaleForm()
        formset = SaleItemFormSet()
        return render(request, 'sales/form.html', self._build_context(form, formset))

    def post(self, request):
        form = SaleForm(request.POST)
        formset = SaleItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            sale = form.save()
            formset.instance = sale
            formset.save()
            if request.htmx:
                response = HttpResponse("", status=200)
                response['HX-Reswap'] = 'none'
                response['HX-Trigger'] = json.dumps({
                    'itemCreated': '',
                    'reloadSales': '',
                    'showSuccess': 'Venda registrada!'
                })
                return response
            return redirect('sales:list')
        return render(request, 'sales/form.html', self._build_context(form, formset))
