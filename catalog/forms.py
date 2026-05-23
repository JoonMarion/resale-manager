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
        name = cleaned_data.get('name')
        parent = cleaned_data.get('parent')

        if self.instance and self.instance.pk and parent and parent.pk == self.instance.pk:
            self.add_error('parent', 'Uma categoria não pode ser pai de si mesma.')

        if name is not None:
            qs = Category.objects.filter(name__iexact=name, parent=parent)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                if parent:
                    self.add_error('name', f'Já existe uma subcategoria com esse nome em "{parent.name}".')
                else:
                    self.add_error('name', 'Já existe uma categoria raiz com esse nome.')

        return cleaned_data
