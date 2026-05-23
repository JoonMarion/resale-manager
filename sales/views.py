import json

from django.views.generic import ListView, DetailView, DeleteView
from django.views import View
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.contrib import messages

from .models import Sale
from .forms import SaleForm, SaleItemFormSet, SaleItemEditFormSet
from products.models import Product
from users.mixins import ProjectLoginRequiredMixin
from stock.models import Stock
from core.mixins import SessionSortMixin


class SaleListView(ProjectLoginRequiredMixin, SessionSortMixin, ListView):
    model = Sale
    context_object_name = 'sales'
    paginate_by = 10
    default_sort = 'recent'
    sort_options = {
        'recent': '-sale_date',
        'oldest': 'sale_date',
    }

    def get_template_names(self):
        if self.request.htmx:
            return 'sales/list_partial.html'
        return 'sales/list.html'

    def get_queryset(self):
        queryset = Sale.objects.select_related('customer').prefetch_related('items').order_by(self.get_ordering())
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
        q = self.request.GET.get('q', '').strip()
        context['current_status'] = self.request.GET.get('status', 'all')
        context['q'] = q

        # Counts for status filters (respecting search query)
        base_qs = Sale.objects.all()
        if q:
            base_qs = base_qs.filter(customer__name__icontains=q)
        context['counts'] = {
            'all': base_qs.count(),
            'pending': base_qs.filter(is_paid=False).count(),
            'paid': base_qs.filter(is_paid=True).count(),
        }
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
        stocks = {
            str(s.product_id): (s.quantity or 0)
            for s in Stock.objects.select_related('product').all()
        }
        return {
            'form': form,
            'formset': formset,
            'product_prices_json': json.dumps(prices),
            'product_stocks_json': json.dumps(stocks),
        }

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


class SaleEditView(ProjectLoginRequiredMixin, View):
    def _build_context(self, form, formset, sale):
        prices = {
            str(p.pk): str(p.sale_price)
            for p in Product.objects.filter(active=True)
        }
        stocks = {
            str(s.product_id): (s.quantity or 0)
            for s in Stock.objects.select_related('product').all()
        }
        return {
            'form': form,
            'formset': formset,
            'product_prices_json': json.dumps(prices),
            'product_stocks_json': json.dumps(stocks),
            'sale': sale,
        }

    def get(self, request, pk):
        sale = get_object_or_404(Sale.objects.prefetch_related('items'), pk=pk)
        form = SaleForm(instance=sale)
        formset = SaleItemEditFormSet(instance=sale)
        return render(request, 'sales/edit_form.html', self._build_context(form, formset, sale))

    def post(self, request, pk):
        sale = get_object_or_404(Sale.objects.prefetch_related('items'), pk=pk)
        # Snapshot old items before any changes
        old_items = {
            item.pk: {'product': item.product, 'quantity': item.quantity}
            for item in sale.items.all()
        }
        form = SaleForm(request.POST, instance=sale)
        formset = SaleItemEditFormSet(request.POST, instance=sale)
        if form.is_valid() and formset.is_valid():
            form.save()
            instances = formset.save(commit=False)
            # Handle items marked for deletion — return their stock
            for item in formset.deleted_objects:
                old = old_items.get(item.pk)
                if old:
                    stock, _ = Stock.objects.get_or_create(product=old['product'])
                    stock.quantity += old['quantity']
                    stock.save()
                item.delete()
            # Save updated/new items with stock reconciliation
            for item in instances:
                if item.pk and item.pk in old_items:
                    # Existing item updated — return old stock, deduct new stock
                    old = old_items[item.pk]
                    old_stock, _ = Stock.objects.get_or_create(product=old['product'])
                    old_stock.quantity += old['quantity']
                    old_stock.save()
                    new_stock, _ = Stock.objects.get_or_create(product=item.product)
                    new_stock.quantity -= item.quantity
                    new_stock.save()
                    item.save()
                else:
                    # New item — post_save signal handles stock decrement
                    item.save()
            formset.save_m2m()
            # Persist a success message so it's shown after redirect on the detail page
            messages.success(request, 'Venda atualizada com sucesso.')
            if request.htmx:
                from django.urls import reverse
                response = HttpResponse("", status=200)
                response['HX-Reswap'] = 'none'
                # Redirect the browser to the sale detail — the message will be shown on load
                response['HX-Redirect'] = reverse('sales:detail', kwargs={'pk': sale.pk})
                return response
            return redirect('sales:detail', pk=sale.pk)
        return render(request, 'sales/edit_form.html', self._build_context(form, formset, sale))


class SaleReceiptView(View):
    """Public receipt view — no login required so it can be shared with customers."""

    def get(self, request, pk):
        sale = get_object_or_404(
            Sale.objects.select_related('customer').prefetch_related('items__product'),
            pk=pk,
        )
        from users.models import UserProfile
        if request.user.is_authenticated:
            profile = UserProfile.objects.select_related('user').filter(user=request.user).first()
        else:
            profile = UserProfile.objects.select_related('user').first()
        return render(request, 'sales/receipt.html', {'sale': sale, 'profile': profile})
