from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.conf import settings
from django.views import View
from django.urls import reverse
import json
import urllib.parse
from .models import Category, PedidoCatalogo, ItemPedidoCatalogo
from .forms import CategoryForm
from products.models import Product
from core.mixins import SessionSortMixin
from .decorators import require_catalog
from .cart import Cart

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
        context['exclude_ids'] = []

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

@method_decorator(require_catalog, name='dispatch')
class PublicCatalogView(ListView):
    model = Product
    template_name = 'catalog/public_list.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        qs = Product.objects.filter(show_in_catalog=True).prefetch_related('catalog_categories', 'stock')
        
        # Filtering by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            # Pegar a categoria selecionada
            category = Category.objects.filter(slug=category_slug).first()
            if category:
                # Buscar produtos da categoria e de todas as suas subcategorias (N níveis)
                descendants = category.get_descendants()
                cat_ids = [category.id] + [d.id for d in descendants]
                qs = qs.filter(catalog_categories__in=cat_ids).distinct()
            
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

@method_decorator(require_catalog, name='dispatch')
class OrderSummaryView(DetailView):
    model = PedidoCatalogo
    template_name = 'catalog/order_summary.html'
    context_object_name = 'pedido'
    pk_url_kwarg = 'order_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pedido = self.object
        
        # WhatsApp logic
        whatsapp_number = getattr(settings, 'WHATSAPP_NUMBER', '')
        order_url = self.request.build_absolute_uri()
        
        message = f"Olá! Gostaria de confirmar meu pedido número *{pedido.numero_pedido}*. Segue o link do pedido: {order_url}"
        encoded_message = urllib.parse.quote(message)
        
        context['whatsapp_link'] = f"https://wa.me/{whatsapp_number}?text={encoded_message}"
        context['whatsapp_number_display'] = whatsapp_number
        
        return context

# --- Cart Views ---

@method_decorator(require_catalog, name='dispatch')
class AddToCartView(View):
    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        cart.add(product=product)
        
        if request.htmx:
            response = render(request, 'catalog/_cart_badge.html', {'cart': cart})
            response['HX-Trigger'] = json.dumps({
                'showSuccess': f'{product.name} adicionado ao carrinho!'
            })
            return response

@method_decorator(require_catalog, name='dispatch')
class RemoveFromCartView(View):
    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        cart.remove(product)
        
        if request.htmx:
            return render(request, 'catalog/_cart_drawer.html', {'cart': cart})
        return HttpResponse(status=204)

@method_decorator(require_catalog, name='dispatch')
class UpdateCartView(View):
    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        action = request.POST.get('action')
        
        # Get current quantity
        current_qty = cart.cart.get(str(product.id), {}).get('quantity', 0)
        
        if action == 'increment':
            cart.add(product, 1)
        elif action == 'decrement':
            if current_qty > 1:
                cart.add(product, -1)
            else:
                cart.remove(product)
                
        if request.htmx:
            return render(request, 'catalog/_cart_drawer.html', {'cart': cart})
        return HttpResponse(status=204)

@method_decorator(require_catalog, name='dispatch')
class CartDetailView(View):
    def get(self, request):
        cart = Cart(request)
        return render(request, 'catalog/_cart_drawer.html', {'cart': cart})

@method_decorator(require_catalog, name='dispatch')
class CheckoutView(View):
    def get(self, request):
        cart = Cart(request)
        if len(cart) == 0:
            from django.shortcuts import redirect
            return redirect('catalog:public_list')
        return render(request, 'catalog/checkout.html', {'cart': cart})

    def post(self, request):
        cart = Cart(request)
        if len(cart) == 0:
            from django.shortcuts import redirect
            return redirect('catalog:public_list')
            
        nome = request.POST.get('nome')
        telefone = request.POST.get('telefone')
        
        # Create Order
        pedido = PedidoCatalogo.objects.create(
            cliente_nome=nome,
            cliente_telefone=telefone,
            total=cart.get_total_price()
        )
        
        # Create Items
        for item in cart:
            ItemPedidoCatalogo.objects.create(
                pedido=pedido,
                produto=item['product'],
                quantidade=item['quantity'],
                preco_unitario=item['price']
            )
            
        # Clear Cart
        cart.clear()
        
        from django.shortcuts import redirect
        return redirect('catalog:order_summary', order_id=pedido.id)
