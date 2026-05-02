from django.db import models
from core.models import BaseModel


class Customer(BaseModel):
    name = models.CharField(max_length=255, verbose_name='Nome Completo')
    email = models.EmailField(unique=True, blank=True, null=True, verbose_name='E-mail')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    document = models.CharField(max_length=20, blank=True, null=True, verbose_name='CPF/CNPJ')
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name='Endereço')
    notes = models.TextField(blank=True, null=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.name
