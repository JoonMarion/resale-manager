from django.db import models
from core.models import BaseModel


class Product(BaseModel):
    name = models.CharField(max_length=255, verbose_name='Nome')
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name='Categoria')
    sku = models.CharField(max_length=50, unique=True, verbose_name='SKU')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Preço de Compra')
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Preço de Venda')
    min_stock = models.IntegerField(default=5, verbose_name='Estoque Mínimo')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')

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
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
