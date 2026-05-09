import os
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete
from django.dispatch import receiver
from core.utils import optimize_image

User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Usuário')
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True, verbose_name='Foto de Perfil')
    store_name = models.CharField(max_length=100, blank=True, verbose_name='Nome da Loja')
    store_phone = models.CharField(max_length=30, blank=True, verbose_name='Telefone da Loja')

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

    def save(self, *args, **kwargs):
        is_new_image = False
        if self.pk:
            try:
                old = UserProfile.objects.get(pk=self.pk)
                if old.photo and old.photo != self.photo:
                    is_new_image = True
                    if os.path.isfile(old.photo.path):
                        os.remove(old.photo.path)
                elif not old.photo and self.photo:
                    is_new_image = True
            except UserProfile.DoesNotExist:
                is_new_image = True
        else:
            is_new_image = True

        if is_new_image and self.photo:
            optimize_image(self.photo)

        super().save(*args, **kwargs)

    def __str__(self):
        return f'Perfil de {self.user.username}'

@receiver(post_delete, sender=UserProfile)
def userprofile_post_delete(sender, instance, **kwargs):
    if instance.photo and os.path.isfile(instance.photo.path):
        os.remove(instance.photo.path)
