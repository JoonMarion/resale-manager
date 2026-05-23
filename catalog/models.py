from django.db import models
from django.utils.text import slugify
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nome')
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories', verbose_name='Categoria Pai')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'parent'],
                name='unique_name_per_parent',
            ),
            models.UniqueConstraint(
                fields=['name'],
                condition=models.Q(parent__isnull=True),
                name='unique_name_root',
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_ancestors(self):
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        descendants = []
        for child in self.subcategories.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def get_full_name(self):
        ancestors = self.get_ancestors()
        if ancestors:
            return " > ".join([a.name for a in ancestors]) + f" > {self.name}"
        return self.name

    def __str__(self):
        return self.get_full_name()

class PedidoCatalogo(models.Model):
    STATUS_CHOICES = [
        ('aguardando', 'Aguardando Confirmação'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_pedido = models.CharField(max_length=20, unique=True, verbose_name='Número do Pedido')
    cliente_nome = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nome do Cliente')
    cliente_telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone do Cliente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Total')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aguardando', verbose_name='Status')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    class Meta:
        verbose_name = 'Pedido do Catálogo'
        verbose_name_plural = 'Pedidos do Catálogo'
        ordering = ['-criado_em']

    def __str__(self):
        return f"Pedido {self.numero_pedido}"

    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            # Simple sequential number logic for demonstration
            # In a real app, this might need a more robust approach
            last_order = PedidoCatalogo.objects.all().order_by('criado_em').last()
            if last_order and last_order.numero_pedido.startswith('#'):
                try:
                    last_num = int(last_order.numero_pedido[1:])
                    self.numero_pedido = f"#{str(last_num + 1).zfill(5)}"
                except ValueError:
                    self.numero_pedido = "#00001"
            else:
                self.numero_pedido = "#00001"
        super().save(*args, **kwargs)

class ItemPedidoCatalogo(models.Model):
    pedido = models.ForeignKey(PedidoCatalogo, on_delete=models.CASCADE, related_name='itens', verbose_name='Pedido')
    produto = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, verbose_name='Produto')
    quantidade = models.PositiveIntegerField(default=1, verbose_name='Quantidade')
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço Unitário')

    @property
    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"{self.quantidade}x {self.produto.name if self.produto else 'Produto removido'}"
