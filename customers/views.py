from django.views.generic import ListView, CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import render
from django.http import HttpResponse
import json
from .models import Customer
from .forms import CustomerForm
from users.mixins import ProjectLoginRequiredMixin
from core.mixins import SessionSortMixin


class CustomerListView(ProjectLoginRequiredMixin, SessionSortMixin, ListView):
    model = Customer
    context_object_name = 'customers'
    paginate_by = 10
    default_sort = 'alpha_asc'
    sort_options = {
        'alpha_asc': 'name',
        'alpha_desc': '-name',
        'recent': '-created_at',
        'oldest': 'created_at',
    }

    def get_template_names(self):
        if self.request.htmx:
            return 'customers/list_partial.html'
        return 'customers/list.html'

    def get_queryset(self):
        queryset = Customer.objects.filter(active=True).order_by(self.get_ordering())
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(name__icontains=q)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context


class CustomerCreateView(ProjectLoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/form.html'
    success_url = reverse_lazy('customers:list')

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse("", status=200)
            response['HX-Reswap'] = 'none'
            response['HX-Trigger'] = json.dumps({
                'itemCreated': '',
                'reloadCustomers': '',
                'showSuccess': 'Cliente criado com sucesso!',
            })
            return response
        return super().form_valid(form)


class CustomerUpdateView(ProjectLoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/form.html'
    success_url = reverse_lazy('customers:list')

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse("", status=200)
            response['HX-Reswap'] = 'none'
            response['HX-Trigger'] = json.dumps({
                'itemCreated': '',
                'reloadCustomers': '',
                'showSuccess': 'Cliente atualizado com sucesso!',
            })
            return response
        return super().form_valid(form)


class CustomerDeleteView(ProjectLoginRequiredMixin, DeleteView):
    model = Customer
    success_url = reverse_lazy('customers:list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.sales.exists():
            if request.htmx:
                response = HttpResponse("", status=200)
                response['HX-Reswap'] = 'none'
                response['HX-Trigger'] = json.dumps({'showError': 'Não é possível excluir este cliente pois está vinculado a uma venda.'})
                return response
        self.object.active = False
        self.object.save()
        if request.htmx:
            response = HttpResponse("", status=200)
            response['HX-Trigger'] = json.dumps({'showSuccess': 'Cliente excluído com sucesso.'})
            return response
        return super().delete(request, *args, **kwargs)
