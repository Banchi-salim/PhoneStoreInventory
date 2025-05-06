from django import forms
from .models import Category, Brand, Phone, Accessory, Inventory, Branch, Supplier, Purchase, PurchaseItem


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description', 'parent')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prevent cycles in category hierarchy
        if self.instance.pk:
            self.fields['parent'].queryset = Category.objects.exclude(pk=self.instance.pk)


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ('name', 'description', 'logo', 'website')


class PhoneForm(forms.ModelForm):
    class Meta:
        model = Phone
        fields = ('name', 'sku', 'barcode', 'description', 'category', 'brand',
                  'cost_price', 'selling_price', 'image', 'is_active',
                  'model_number', 'storage_capacity', 'ram', 'color', 'screen_size',
                  'processor', 'camera_specs', 'battery_capacity', 'operating_system',
                  'release_year', 'warranty_period')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter categories for phones
        self.fields['category'].queryset = Category.objects.filter(parent__isnull=True) | Category.objects.filter(
            parent__name__icontains='phone')
        # Make SKU and barcode optional for auto-generation
        self.fields['sku'].required = False
        self.fields['barcode'].required = False


class AccessoryForm(forms.ModelForm):
    class Meta:
        model = Accessory
        fields = ('name', 'sku', 'barcode', 'description', 'category', 'brand',
                  'cost_price', 'selling_price', 'image', 'is_active',
                  'accessory_type', 'compatible_phones', 'material', 'color',
                  'specifications', 'warranty_period')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter categories for accessories
        self.fields['category'].queryset = Category.objects.filter(parent__isnull=True) | Category.objects.filter(
            parent__name__icontains='accessory')
        # Make SKU and barcode optional for auto-generation
        self.fields['sku'].required = False
        self.fields['barcode'].required = False
        # Filter compatible phones
        self.fields['compatible_phones'].queryset = Phone.objects.filter(is_active=True)


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ('product', 'branch', 'quantity', 'reorder_level')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only active products and branches
        self.fields['product'].queryset = self.fields['product'].queryset.filter(is_active=True)
        self.fields['branch'].queryset = self.fields['branch'].queryset.filter(is_active=True)


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ('name', 'address', 'phone_number', 'email', 'manager', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only admin users for manager role
        from CustomUser.models import CustomUser
        self.fields['manager'].queryset = CustomUser.objects.filter(user_type='admin', is_active=True)


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ('name', 'contact_person', 'email', 'phone_number', 'address', 'website', 'is_active')


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ('supplier', 'branch', 'purchase_date', 'reference_number', 'notes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only active suppliers and branches
        self.fields['supplier'].queryset = self.fields['supplier'].queryset.filter(is_active=True)
        self.fields['branch'].queryset = self.fields['branch'].queryset.filter(is_active=True)
        # Make reference_number optional for auto-generation
        self.fields['reference_number'].required = False


class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ('product', 'quantity', 'unit_price')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only active products
        self.fields['product'].queryset = self.fields['product'].queryset.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')

        if quantity and unit_price:
            # Auto-calculate total price
            cleaned_data['total_price'] = quantity * unit_price

        return cleaned_data
