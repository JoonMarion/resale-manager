import os
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from core.models import BaseModel
from core.utils import optimize_image


class Product(BaseModel):
    name = models.CharField(max_length=255, verbose_name='Nome')
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name='Categoria')
    sku = models.CharField(max_length=50, unique=True, verbose_name='SKU')
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name='Imagem')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Preço de Compra')
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Preço de Venda')
    min_stock = models.IntegerField(default=5, verbose_name='Estoque Mínimo')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')
    
    # Catalog fields
    show_in_catalog = models.BooleanField(default=False, verbose_name='Exibir no catálogo?')
    catalog_categories = models.ManyToManyField(
        'catalog.Category',
        blank=True,
        related_name='products',
        verbose_name='Categorias do Catálogo'
    )

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'

    @property
    def profit(self):
        return self.sale_price - self.purchase_price

    @property
    def is_low_stock(self):
        return self.stock.quantity <= self.min_stock if hasattr(self, 'stock') else True

    def save(self, *args, **kwargs):
        if not self.sku or self.sku == 'AUTO':
            import uuid
            self.sku = str(uuid.uuid4())[:8].upper()
            
        is_new_image = False
        if self.pk:
            try:
                old = Product.objects.get(pk=self.pk)
                if old.image and old.image != self.image:
                    is_new_image = True
                    if os.path.isfile(old.image.path):
                        os.remove(old.image.path)
                elif not old.image and self.image:
                    is_new_image = True
            except Product.DoesNotExist:
                is_new_image = True
        else:
            is_new_image = True

        if is_new_image and self.image:
            optimize_image(self.image)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

@receiver(post_delete, sender=Product)
def product_post_delete(sender, instance, **kwargs):
    if instance.image and os.path.isfile(instance.image.path):
        os.remove(instance.image.path)
