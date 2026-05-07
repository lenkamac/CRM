from django import forms

from .models import Client, Comment, ClientFile, Purchase
from product.models import Product


class AddClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ('company', 'first_name', 'last_name', 'title', 'phone', 'mobile',
                  'address', 'zipcode', 'city', 'country', 'email', 'description',
                  'status', 'website')

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name', '').strip()
        last_name = cleaned_data.get('last_name', '').strip()

        if first_name or last_name:
            qs = Client.objects.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                name = f'{first_name} {last_name}'.strip()
                raise forms.ValidationError(
                    f'A client named "{name}" already exists in the list.'
                )
        return cleaned_data


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