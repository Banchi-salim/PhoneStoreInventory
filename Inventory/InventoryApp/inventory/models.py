from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import uuid


class Category(models.Model):
    """Model for product categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Brand(models.Model):
    """Model for product brands"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='brand_logos/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Branch(models.Model):
    """Model for store branches"""
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='managed_branches')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Branches'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Base model for all products (abstract)"""
    PRODUCT_TYPE_CHOICES = (
        ('phone', 'Phone'),
        ('accessory', 'Accessory'),
    )

    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=50, blank=True, null=True, unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.sku}"

    def save(self, *args, **kwargs):
        # Auto-generate SKU if not provided
        if not self.sku:
            # Create a unique SKU based on product type, brand, and a random string
            prefix = 'PH' if self.product_type == 'phone' else 'AC'
            brand_prefix = ''.join([x[0] for x in self.brand.name.split()]).upper()
            unique_id = str(uuid.uuid4())[:8]
            self.sku = f"{prefix}-{brand_prefix}-{unique_id}"

        super().save(*args, **kwargs)


class Phone(Product):
    """Model for phone products"""
    model_number = models.CharField(max_length=100)
    storage_capacity = models.CharField(max_length=50)
    ram = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    screen_size = models.CharField(max_length=50)
    processor = models.CharField(max_length=100)
    camera_specs = models.TextField(blank=True, null=True)
    battery_capacity = models.CharField(max_length=50, blank=True, null=True)
    operating_system = models.CharField(max_length=50)
    release_year = models.PositiveIntegerField(blank=True, null=True)
    warranty_period = models.CharField(max_length=50, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.product_type = 'phone'
        super().save(*args, **kwargs)


class Accessory(Product):
    """Model for accessory products"""
    ACCESSORY_TYPE_CHOICES = (
        ('case', 'Case'),
        ('screen_protector', 'Screen Protector'),
        ('charger', 'Charger'),
        ('headphone', 'Headphone'),
        ('cable', 'Cable'),
        ('power_bank', 'Power Bank'),
        ('memory_card', 'Memory Card'),
        ('other', 'Other'),
    )

    accessory_type = models.CharField(max_length=20, choices=ACCESSORY_TYPE_CHOICES)
    compatible_phones = models.ManyToManyField(Phone, blank=True, related_name='compatible_accessories')
    material = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    specifications = models.TextField(blank=True, null=True)
    warranty_period = models.CharField(max_length=50, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.product_type = 'accessory'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Accessories'


class Inventory(models.Model):
    """Model for tracking inventory across branches"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=5)
    last_restock_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Inventories'
        unique_together = ('product', 'branch')

    def __str__(self):
        return f"{self.product.name} at {self.branch.name} - {self.quantity} units"

    def is_low_stock(self):
        """Check if inventory is below reorder level"""
        return self.quantity <= self.reorder_level


class Supplier(models.Model):
    """Model for product suppliers"""
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Purchase(models.Model):
    """Model for tracking purchases from suppliers"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('canceled', 'Canceled'),
    )

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchases')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='purchases')
    purchase_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reference_number = models.CharField(max_length=50, unique=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='created_purchases')
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='received_purchases')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PO-{self.reference_number} ({self.supplier.name})"

    def save(self, *args, **kwargs):
        # Auto-generate reference number if not provided
        if not self.reference_number:
            last_purchase = Purchase.objects.order_by('-id').first()
            last_id = last_purchase.id if last_purchase else 0
            self.reference_number = f"PO-{str(last_id + 1).zfill(6)}"

        super().save(*args, **kwargs)


class PurchaseItem(models.Model):
    """Model for individual items in a purchase"""
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='purchase_items')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} ({self.quantity}) - {self.purchase.reference_number}"

    def save(self, *args, **kwargs):
        # Auto-calculate the total price
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

        # Update the purchase total
        self.purchase.total_amount = sum(item.total_price for item in self.purchase.items.all())
        self.purchase.save()
