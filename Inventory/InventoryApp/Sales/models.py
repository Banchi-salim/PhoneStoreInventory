from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import uuid


class Customer(models.Model):
    """Model for customer information"""
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Sale(models.Model):
    """Model for sales transactions"""
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('mobile_payment', 'Mobile Payment'),
        ('other', 'Other'),
    )

    sale_date = models.DateTimeField(default=timezone.now)
    invoice_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    branch = models.ForeignKey('inventory.Branch', on_delete=models.CASCADE, related_name='sales')
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sales')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.sale_date.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        # Auto-generate invoice number if not provided
        if not self.invoice_number:
            today = timezone.now().strftime('%Y%m%d')
            last_sale = Sale.objects.filter(invoice_number__startswith=f"INV-{today}").order_by('-id').first()
            if last_sale:
                last_number = int(last_sale.invoice_number.split('-')[-1])
                self.invoice_number = f"INV-{today}-{str(last_number + 1).zfill(4)}"
            else:
                self.invoice_number = f"INV-{today}-0001"

        super().save(*args, **kwargs)


class SaleItem(models.Model):
    """Model for individual items in a sale"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='sale_items')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} ({self.quantity}) - {self.sale.invoice_number}"

    def save(self, *args, **kwargs):
        # Auto-calculate the total price
        self.total_price = (self.quantity * self.unit_price) - self.discount
        super().save(*args, **kwargs)

        # Update the sale total
        self.sale.subtotal = sum(item.total_price for item in self.sale.items.all())
        self.sale.total_amount = self.sale.subtotal + self.sale.tax_amount - self.sale.discount_amount
        self.sale.save()

        # Update inventory
        inventory = self.product.inventory.filter(branch=self.sale.branch).first()
        if inventory:
            inventory.quantity = max(0, inventory.quantity - self.quantity)
            inventory.save()
