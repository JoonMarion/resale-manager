from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
import json
from .models import Category
from .forms import CategoryForm
from products.models import Product
from core.mixins import SessionSortMixin

# --- Admin Views for Category ---

class CategoryListView(LoginRequiredMixin, SessionSortMixin, ListView):
    model = Category
    context_object_name = 'categories'
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
            return 'catalog/category_list_partial.html'
        return 'catalog/category_list.html'

    def get_queryset(self):
        q = self.request.GET.get('q')
        queryset = Category.objects.all().order_by(self.get_ordering())
        
        if q:
            queryset = queryset.filter(name__icontains=q)
        else:
            # Em modo visualização normal (sem busca), mostramos apenas as raízes
            # para que o template renderize a árvore recursivamente.
            queryset = queryset.filter(parent__isnull=True)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'catalog/category_form.html'
    success_url = reverse_lazy('catalog:category_list')

    def get_initial(self):
        initial = super().get_initial()
        parent_id = self.request.GET.get('parent')
        if parent_id:
            initial['parent'] = parent_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['root_categories'] = Category.objects.filter(parent__isnull=True)
        
        parent_id = self.request.GET.get('parent')
        if parent_id:
            context['parent_obj'] = Category.objects.filter(pk=parent_id).first()
            
        return context

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse("", status=200)
            response['HX-Reswap'] = 'none'
            response['HX-Trigger'] = json.dumps({
                'itemCreated': '',
                'reloadCategories': '',
                'showSuccess': 'Categoria atualizada com sucesso!',
            })
            return response
        return super().form_valid(form)

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'catalog/category_form.html'
    success_url = reverse_lazy('catalog:category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Exclude self and descendants from potential parents to prevent circular references
        exclude_ids = [self.object.id] + [d.id for d in self.object.get_descendants()] if self.object else []
        context['root_categories'] = Category.objects.filter(parent__isnull=True).exclude(id__in=exclude_ids)
        context['exclude_ids'] = exclude_ids
        return context

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse("", status=200)
            response['HX-Reswap'] = 'none'
            response['HX-Trigger'] = json.dumps({
                'itemCreated': '',
                'reloadCategories': '',
                'showSuccess': 'Categoria atualizada com sucesso!',
            })
            return response
        return super().form_valid(form)

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('catalog:category_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.products.exists():
            if request.htmx:
                response = HttpResponse("", status=200)
                response['HX-Reswap'] = 'none'
                response['HX-Trigger'] = json.dumps({'showError': 'Não é possível excluir esta categoria pois possui produtos vinculados.'})
                return response
        
        # O Django cuidará do CASCADE para subcategorias, mas vamos garantir deleção
        self.object.delete()
        if request.htmx:
            response = HttpResponse("", status=200)
            response['HX-Trigger'] = json.dumps({'showSuccess': 'Categoria excluída com sucesso.', 'reloadCategories': ''})
            return response
        return super().delete(request, *args, **kwargs)

# --- Public Catalog View ---

class PublicCatalogView(ListView):
    model = Product
    template_name = 'catalog/public_list.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        qs = Product.objects.filter(show_in_catalog=True)
        
        # Filtering by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            # Pegar a categoria selecionada
            category = Category.objects.filter(slug=category_slug).first()
            if category:
                # Buscar produtos da categoria e de todas as suas subcategorias (N níveis)
                descendants = category.get_descendants()
                cat_ids = [category.id] + [d.id for d in descendants]
                qs = qs.filter(catalog_category_id__in=cat_ids)
            
        # Searching by name
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
            
        # Ordering
        sort = self.request.GET.get('sort', 'name_asc')
        if sort == 'name_desc':
            qs = qs.order_by('-name')
        elif sort == 'price_asc':
            qs = qs.order_by('sale_price')
        elif sort == 'price_desc':
            qs = qs.order_by('-sale_price')
        else: # name_asc default
            qs = qs.order_by('name')
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Árvore completa de categorias para o Drawer (apenas raízes, o template busca os filhos)
        context['all_categories'] = Category.objects.filter(parent__isnull=True)
        
        current_category = self.request.GET.get('category', '')
        context['current_category_slug'] = current_category
        
        if current_category:
            cat = Category.objects.filter(slug=current_category).first()
            if cat:
                context['current_category_obj'] = cat
                context['breadcrumbs'] = cat.get_ancestors()
                context['subcategories'] = cat.subcategories.all()
        else:
            context['breadcrumbs'] = []
            context['subcategories'] = Category.objects.filter(parent__isnull=True)
            context['current_category_obj'] = None
        
        context['search_query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', 'name_asc')
        return context
