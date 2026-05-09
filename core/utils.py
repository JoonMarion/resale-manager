import os
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

def optimize_image(image_field, size=(500, 500), quality=80):
    """
    Otimiza a imagem enviada, recortando-a em formato quadrado (centralizado)
    e convertendo para WebP para economizar espaço em disco na VPS.
    """
    if not image_field:
        return

    # Abre a imagem usando Pillow
    try:
        img = Image.open(image_field)
    except Exception:
        return  # Se não for uma imagem válida, não faz nada

    # Converte para RGB se necessário (remover canal alpha ou paleta)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Faz o recorte quadrado central
    img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)

    # Salva a imagem processada em memória
    output = BytesIO()
    img.save(output, format='WEBP', quality=quality)
    output.seek(0)

    # Cria o nome do arquivo com a extensão .webp
    filename = os.path.basename(image_field.name)
    name, ext = os.path.splitext(filename)
    new_filename = f"{name}.webp"

    # Substitui o arquivo no campo do modelo
    image_field.save(new_filename, ContentFile(output.read()), save=False)


def delete_old_file(instance, field_name):
    """
    Deleta o arquivo antigo associado ao campo antes de salvar um novo
    para não acumular lixo no servidor.
    """
    if not instance.pk:
        return False

    try:
        old_instance = instance.__class__.objects.get(pk=instance.pk)
        old_file = getattr(old_instance, field_name)
    except instance.__class__.DoesNotExist:
        return False

    new_file = getattr(instance, field_name)

    # Se a foto antiga existir e não for igual à nova, exclui do disco
    if old_file and old_file != new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
            return True

    return False

