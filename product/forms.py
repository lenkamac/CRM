from django import forms

from .models import ProductFile


class ProductFileForm(forms.ModelForm):
    class Meta:
        model = ProductFile
        fields = ('file',)
