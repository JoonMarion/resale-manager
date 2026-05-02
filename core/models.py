from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    active = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        abstract = True
