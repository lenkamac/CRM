from django import forms
from .models import Opportunity, Comment


class AddOpportunityForm(forms.ModelForm):
    expected_close_date = forms.DateField(
        required=False,
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        widget=forms.DateInput(
            format='%d.%m.%Y',
            attrs={
                'type': 'text',
                'class': 'form-control flatpickr-date',
                'placeholder': 'dd.mm.yyyy',
                'autocomplete': 'off',
            }
        )
    )
    class Meta:
        model = Opportunity
        fields = (
            'name', 'account', 'currency', 'amount', 'stage', 'probability',
            'next_step', 'expected_close_date', 'type', 'lead_source',
            'campaign', 'description', 'assigned_to', 'forecast_category',
        )
        widgets = {
            'expected_close_date': forms.DateInput(attrs={'type': 'text', 'class': 'form-control flatpickr-date'}),
        }


class AddCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
