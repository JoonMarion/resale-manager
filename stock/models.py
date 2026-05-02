from django.db import models
from core.models import BaseModel
from products.models import Product


class Stock(BaseModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stock', verbose_name='Produto')
    quantity = models.IntegerField(default=0, verbose_name='Quantidade')

    class Meta:
        verbose_name = 'Estoque'
        verbose_name_plural = 'Estoques'

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"


class StockEntry(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='entries', verbose_name='Produto')
    quantity = models.IntegerField(verbose_name='Quantidade')
    notes = models.TextField(blank=True, null=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Entrada de Estoque'
        verbose_name_plural = 'Entradas de Estoque'

    def __str__(self):
        return f"{self.product.name} +{self.quantity}"


class StockExit(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='exits', verbose_name='Produto')
    quantity = models.IntegerField(verbose_name='Quantidade')
    notes = models.TextField(blank=True, null=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Saída de Estoque'
        verbose_name_plural = 'Saídas de Estoque'

    def __str__(self):
        return f"{self.product.name} -{self.quantity}"
