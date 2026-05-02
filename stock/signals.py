from django.db.models.signals import post_save
from django.dispatch import receiver
from sales.models import SaleItem
from .models import Stock


@receiver(post_save, sender=SaleItem)
def decrement_stock_on_sale(sender, instance, created, **kwargs):
    if created:
        stock, _ = Stock.objects.get_or_create(product=instance.product)
        stock.quantity -= instance.quantity
        stock.save()
