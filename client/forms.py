from django import forms

from .models import Client, Comment, ClientFile, Purchase
from product.models import Product


class AddClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'


class AddCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)


class AddFileForm(forms.ModelForm):
    class Meta:
        model = ClientFile
        fields = ('file',)


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['created_at', 'product', 'quantity', 'purchase_price', 'currency', 'notes']
        widgets = {
            'created_at': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_created_at',
            }),
            'product': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_product',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'id': 'id_quantity',
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Leave empty to use product price',
                'id': 'id_purchase_price',
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_currency',
            }),
            'notes': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Add notes about this purchase...',
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show all products
        self.fields['product'].queryset = Product.objects.all()
        # Display product name with price
        self.fields['product'].label_from_instance = lambda obj: f"{obj.name}"
        # Make purchase_price optional
        self.fields['purchase_price'].required = False