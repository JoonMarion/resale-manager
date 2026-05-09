from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    initial_stock = forms.IntegerField(label='Estoque', initial=0, required=False)

    class Meta:
        model = Product
        fields = ['name', 'category', 'sku', 'purchase_price', 'sale_price', 'min_stock', 'description', 'image', 'show_in_catalog', 'catalog_category']
        labels = {
            'name': 'Nome',
            'category': 'Categoria',
            'sku': 'SKU',
            'purchase_price': 'Preço de compra',
            'sale_price': 'Preço de venda',
            'min_stock': 'Estoque mínimo',
            'description': 'Descrição',
            'image': 'Imagem',
        }
        widgets = {
            'image': forms.FileInput(),
            'catalog_category': forms.Select(attrs={'class': 'select2'}), # Assuming they want something like select2
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.conf import settings
        if not getattr(settings, 'USE_CATALOG', False):
            # Remove catalog fields if feature flag is off
            if 'show_in_catalog' in self.fields:
                del self.fields['show_in_catalog']
            if 'catalog_category' in self.fields:
                del self.fields['catalog_category']

    def clean(self):
        cleaned_data = super().clean()
        from django.conf import settings
        
        if getattr(settings, 'USE_CATALOG', False):
            show_in_catalog = cleaned_data.get('show_in_catalog')
            catalog_category = cleaned_data.get('catalog_category')
            
            if show_in_catalog and not catalog_category:
                self.add_error('catalog_category', 'A categoria do catálogo é obrigatória quando o produto é exibido no catálogo.')
                
        return cleaned_data
