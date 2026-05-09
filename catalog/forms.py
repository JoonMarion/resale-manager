from django import forms
from .models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'parent']
        labels = {
            'name': 'Nome da Categoria',
            'parent': 'Categoria Pai (opcional)',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prevent selecting itself as parent
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = Category.objects.exclude(pk=self.instance.pk)

    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        if self.instance and self.instance.pk and parent and parent.pk == self.instance.pk:
            self.add_error('parent', 'Uma categoria não pode ser pai de si mesma.')
        return cleaned_data
