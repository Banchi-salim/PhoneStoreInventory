from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import uuid

from inventory.models import Inventory, Purchase


# notifications/models.py
class Notification(models.Model):
    """Model for system notifications (SMS/Email)"""
    NOTIFICATION_TYPE_CHOICES = (
        ('low_stock', 'Low Stock Alert'),
        ('stock_out', 'Stock Out Alert'),
        ('new_sale', 'New Sale'),
        ('new_purchase', 'New Purchase'),
        ('system', 'System Notification'),
    )

    DELIVERY_METHOD_CHOICES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Both Email and SMS'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )

    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    delivery_method = models.CharField(max_length=10, choices=DELIVERY_METHOD_CHOICES, default='email')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)  # ContentType reference
    related_object_id = models.PositiveIntegerField(blank=True, null=True)  # Object ID

    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name()} ({self.status})"


# reports/models.py
class Report(models.Model):
    """Model for generated reports"""
    REPORT_TYPE_CHOICES = (
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('purchase', 'Purchase Report'),
        ('profit', 'Profit Report'),
        ('custom', 'Custom Report'),
    )

    FORMAT_CHOICES = (
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
    )

    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    file = models.FileField(upload_to='reports/')
    parameters = models.JSONField(blank=True, null=True)  # Store report parameters as JSON
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='reports')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%Y-%m-%d')})"


# Signal handlers
@receiver(post_save, sender=Inventory)
def check_low_stock(sender, instance, **kwargs):
    """Send notification when inventory is low"""
    if instance.is_low_stock():
        # Find branch manager and admin users
        recipients = []
        if instance.branch.manager:
            recipients.append(instance.branch.manager)

        # Create notification for each recipient
        for recipient in recipients:
            Notification.objects.create(
                notification_type='low_stock',
                title=f'Low Stock Alert: {instance.product.name}',
                message=f'The inventory for {instance.product.name} at {instance.branch.name} is low. '
                        f'Current quantity: {instance.quantity}, Reorder level: {instance.reorder_level}',
                recipient=recipient,
                delivery_method='both',
                related_object_type='inventory',
                related_object_id=instance.id
            )


@receiver(post_save, sender=Purchase)
def update_inventory_on_purchase_received(sender, instance, created, **kwargs):
    """Update inventory when a purchase is marked as received"""
    if instance.status == 'received':
        # Update inventory quantities for each item in the purchase
        for item in instance.items.all():
            inventory, created = Inventory.objects.get_or_create(
                product=item.product,
                branch=instance.branch,
                defaults={'quantity': 0}
            )
            inventory.quantity += item.quantity
            inventory.last_restock_date = timezone.now()
            inventory.save()