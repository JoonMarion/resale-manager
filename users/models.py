from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Usuário')
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True, verbose_name='Foto de Perfil')
    store_name = models.CharField(max_length=100, blank=True, verbose_name='Nome da Loja')
    store_phone = models.CharField(max_length=30, blank=True, verbose_name='Telefone da Loja')

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

    def __str__(self):
        return f'Perfil de {self.user.username}'
