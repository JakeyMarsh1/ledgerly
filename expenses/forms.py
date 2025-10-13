"""I keep my Ledgerly forms for creating and editing transactions here."""

from decimal import Decimal
from typing import cast

from django import forms

from .currencies import (
    CURRENCY_CHOICES,
    DEFAULT_CURRENCY,
    MAX_CENTS,
    get_currency_symbol,
    parse_display_amount_to_cents,
)
from .models import Category, Transaction, UserSettings


class TransactionForm(forms.ModelForm):
    """I let users edit their existing transactions."""

    currency_code: str

    class Meta:
        model = Transaction
        fields = [
            'name',
            'type',
            'amount_in_cents',
            'category',
            'occurred_on',
            'note',
        ]
        widgets = {
            'occurred_on': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, currency_code: str = DEFAULT_CURRENCY, **kwargs):
        self.currency_code = currency_code
        super().__init__(*args, **kwargs)
        category_field = cast(forms.ModelChoiceField, self.fields['category'])
        category_field.required = False
        category_field.queryset = Category.objects.filter(is_active=True)
        category_field.empty_label = 'N/A'
        self.fields['note'].widget.attrs['placeholder'] = 'Optional notes'
        self.fields['name'].widget.attrs['placeholder'] = (
            'Give this transaction a short title'
        )
        instance_type = None
        if getattr(self.instance, 'pk', None):
            instance_type = self.instance.type
        form_type = (
            self.data.get('type')
            if self.is_bound
            else self.initial.get('type')
        ) or instance_type
        if form_type == Transaction.INCOME:
            category_field.widget.attrs['disabled'] = 'disabled'
            category_field.help_text = (
                'Income does not use categories and will be saved as N/A.'
            )
        else:
            category_field.widget.attrs.pop('disabled', None)
        symbol = get_currency_symbol(currency_code)
        max_amount_units = Decimal(MAX_CENTS) / Decimal(100)
        self.fields['amount_in_cents'] = forms.DecimalField(
            label=f'Amount ({symbol})',
            decimal_places=2,
            max_digits=18,
            min_value=Decimal('0.00'),
            widget=forms.NumberInput(attrs={
                'step': '0.01',
                'max': str(max_amount_units)
            }),
        )
        self.fields['amount_in_cents'].help_text = (
            'Enter the full amount using decimals for cents/pence '
            '(e.g. 19.99).'
        )
        if self.instance and self.instance.pk:
            initial_amount = (
                Decimal(self.instance.amount_in_cents) / Decimal(100)
            )
            self.fields['amount_in_cents'].initial = initial_amount

    def clean_amount_in_cents(self):
        amount = self.cleaned_data.get('amount_in_cents')
        if amount in (None, ''):
            raise forms.ValidationError('Please enter an amount.')
        if amount < 0:
            raise forms.ValidationError('Amount cannot be negative.')
        cents = parse_display_amount_to_cents(str(amount))
        if cents > MAX_CENTS:
            raise forms.ValidationError(
                'Amount is too large to store. Please enter a smaller value.'
            )
        return cents

    def clean(self):
        cleaned_data = super().clean()
        txn_type = cleaned_data.get('type')
        category = cleaned_data.get('category')

        if txn_type == Transaction.OUTGO and category is None:
            self.add_error('category', 'Expenses must have a category.')
        if txn_type == Transaction.INCOME:
            cleaned_data['category'] = None

        name = cleaned_data.get('name')
        if isinstance(name, str):
            cleaned_data['name'] = name.strip().title()

        return cleaned_data


class CurrencySettingsForm(forms.ModelForm):
    """I let users pick their preferred currency."""

    class Meta:
        model = UserSettings
        fields = ['currency_code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['currency_code'].choices = list(CURRENCY_CHOICES)
        self.fields['currency_code'].label = 'Currency'
        self.fields['currency_code'].widget.attrs.update({
            'class': 'form-select'
        })
