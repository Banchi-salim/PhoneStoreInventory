from django import forms
from .models import Customer, Sale, SaleItem


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ('name', 'email', 'phone_number', 'address')


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ('customer', 'payment_method', 'discount_amount', 'notes')

    def __init__(self, *args, **kwargs):
        branch = kwargs.pop('branch', None)
        super().__init__(*args, **kwargs)

        # Make customer optional
        self.fields['customer'].required = False

        # Store branch for later use
        self.branch = branch


class SaleItemForm(forms.ModelForm):
    product_search = forms.CharField(max_length=100, required=False, label="Search Product")

    class Meta:
        model = SaleItem
        fields = ('product', 'quantity', 'discount')

    def __init__(self, *args, **kwargs):
        branch = kwargs.pop('branch', None)
        super().__init__(*args, **kwargs)

        # Product dropdown should only show items in stock
        if branch:
            self.fields['product'].queryset = self.fields['product'].queryset.filter(
                inventory__branch=branch,
                inventory__quantity__gt=0,
                is_active=True
            ).distinct()
        else:
            self.fields['product'].queryset = self.fields['product'].queryset.filter(
                inventory__quantity__gt=0,
                is_active=True
            ).distinct()

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')

        if product and quantity:
            # Check if enough stock is available
            inventory = product.inventory.filter(branch=self.branch).first()
            if inventory and inventory.quantity < quantity:
                raise forms.ValidationError(f"Not enough stock available. Only {inventory.quantity} units in stock.")

        return cleaned_data