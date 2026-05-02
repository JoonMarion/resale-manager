from django.db import models
from core.models import BaseModel
from customers.models import Customer
from products.models import Product


class Sale(BaseModel):
    PAYMENT_METHODS = [
        ('pix', 'Pix'),
        ('cash', 'Dinheiro'),
        ('card', 'Cartão'),
        ('other', 'Outro'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='sales', verbose_name='Cliente')
    sale_date = models.DateTimeField(auto_now_add=True, verbose_name='Data da Venda')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='pix', verbose_name='Método de Pagamento')
    is_paid = models.BooleanField(default=False, verbose_name='Pago')

    class Meta:
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    def __str__(self):
        return f"Venda {self.id} - {self.customer.name if self.customer else 'Consumidor'}"


class SaleItem(BaseModel):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items', verbose_name='Venda')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_items', verbose_name='Produto')
    quantity = models.IntegerField(verbose_name='Quantidade')
    unit_sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço Unitário')

    class Meta:
        verbose_name = 'Item da Venda'
        verbose_name_plural = 'Itens da Venda'

    @property
    def total_price(self):
        return self.unit_sale_price * self.quantity

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"
