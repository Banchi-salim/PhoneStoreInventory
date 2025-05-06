from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class POSSession(models.Model):
    """Represents a staff member's POS session/shift"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('force_closed', 'Force Closed'),
    )

    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='pos_sessions')
    branch = models.ForeignKey('users.Branch', on_delete=models.CASCADE, related_name='pos_sessions')
    opening_time = models.DateTimeField(auto_now_add=True)
    closing_time = models.DateTimeField(blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cash_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    card_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transaction_count = models.IntegerField(default=0)
    cash_in_drawer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='closed_sessions')

    def __str__(self):
        return f"Session #{self.id} - {self.staff.username} at {self.branch.name}"

    def close_session(self, user, closing_balance, cash_in_drawer, notes=None):
        """Close the POS session"""
        if self.status != 'active':
            raise ValueError(f"Cannot close session with status: {self.status}")

        self.status = 'closed'
        self.closing_time = timezone.now()
        self.closed_by = user
        self.closing_balance = closing_balance
        self.cash_in_drawer = cash_in_drawer

        if notes:
            self.notes = notes

        self.save()

    def update_sales_totals(self, sale):
        """Update session totals with a new sale"""
        from sales.models import Sale

        if sale.status != 'completed':
            return

        # Update total sales
        self.total_sales += sale.total_amount
        self.transaction_count += 1

        # Update payment method totals
        payment_method = sale.payment_method.name.lower() if sale.payment_method else 'other'

        if 'cash' in payment_method:
            self.cash_sales += sale.total_amount
            self.cash_in_drawer += sale.total_amount
        elif 'card' in payment_method or 'credit' in payment_method:
            self.card_sales += sale.total_amount
        else:
            self.other_sales += sale.total_amount

        self.save()


class CashDrawerOperation(models.Model):
    OPERATION_TYPE_CHOICES = [
        ('mobile_in', 'Mobile Money In'),
        ('mobile_out', 'Mobile Money Out'),
        ('wallet_topup', 'Wallet Top-Up'),
        ('wallet_refund', 'Wallet Refund'),
        ('card_refund', 'Card Refund'),
        ('bank_transfer_in', 'Bank Transfer In'),
        ('bank_transfer_out', 'Bank Transfer Out'),
        ('adjustment', 'Manual Adjustment'),
    ]

    session = models.ForeignKey(POSSession, on_delete=models.CASCADE)
    operation_type = models.CharField(max_length=30, choices=OPERATION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.amount}"


class POSSetting(models.Model):
    """POS system settings (can be branch-specific)"""
    branch = models.OneToOneField('users.Branch', on_delete=models.CASCADE, related_name='pos_settings')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)  # percentage
    receipt_header = models.TextField(blank=True, null=True)
    receipt_footer = models.TextField(blank=True, null=True)
    logo_on_receipt = models.BooleanField(default=True)
    enable_discounts = models.BooleanField(default=True)
    require_customer_for_sales = models.BooleanField(default=False)
    allow_price_override = models.BooleanField(default=False)
    min_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    default_payment_method = models.ForeignKey('sales.PaymentMethod',
                                               on_delete=models.SET_NULL, null=True, blank=True)
    cash_rounding = models.BooleanField(default=False)
    allow_partial_payments = models.BooleanField(default=False)

    def __str__(self):
        return f"POS Settings for {self.branch.name}"

    def calculate_tax(self, amount):
        """Calculate tax based on tax rate"""
        return (amount * self.tax_rate) / Decimal('100.0')

    def is_discount_allowed(self, percentage):
        """Check if discount percentage is allowed"""
        return (percentage >= self.min_discount_percentage and
                percentage <= self.max_discount_percentage)


class QuickAction(models.Model):
    """Custom quick actions for the POS interface"""
    ACTION_TYPE_CHOICES = (
        ('product', 'Add Product'),
        ('discount', 'Apply Discount'),
        ('customer', 'Set Customer'),
        ('payment', 'Set Payment'),
        ('custom', 'Custom Action'),
    )

    name = models.CharField(max_length=50)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES)
    value = models.CharField(max_length=100)  # product ID, discount percentage, etc.
    description = models.CharField(max_length=255, blank=True, null=True)
    icon = models.CharField(max_length=50, default='tag')  # Icon name (for UI)
    color = models.CharField(max_length=20, default='primary')  # Button color
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    branch = models.ForeignKey('users.Branch', on_delete=models.CASCADE,
                               related_name='pos_quick_actions', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='pos_quick_actions', null=True, blank=True)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    @property
    def action_data(self):
        """Return action data as JSON-friendly dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'action_type': self.action_type,
            'value': self.value,
            'icon': self.icon,
            'color': self.color,
        }


class CartItem(models.Model):
    """Temporary cart items before finalizing a sale"""
    session = models.ForeignKey(POSSession, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    variant = models.ForeignKey('inventory.ProductVariant', on_delete=models.SET_NULL,
                                null=True, blank=True)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.CharField(max_length=255, blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"

    def save(self, *args, **kwargs):
        """Calculate totals before saving"""
        self.total = (self.unit_price * self.quantity) - self.discount + self.tax_amount
        super().save(*args, **kwargs)

    def apply_tax(self, tax_rate=None):
        """Apply tax rate to item"""
        # If tax_rate is not provided, get from branch settings
        if tax_rate is None:
            try:
                tax_rate = self.session.branch.pos_settings.tax_rate
            except:
                tax_rate = Decimal('10.0')  # Default 10%

        subtotal = (self.unit_price * self.quantity) - self.discount
        self.tax_amount = (subtotal * tax_rate) / Decimal('100.0')
        self.save()


class CustomerDisplay(models.Model):
    """Settings for customer-facing display"""
    branch = models.OneToOneField('users.Branch', on_delete=models.CASCADE,
                                  related_name='customer_display')
    welcome_message = models.CharField(max_length=255, default="Welcome to our store!")
    enable_digital_receipts = models.BooleanField(default=True)
    show_running_total = models.BooleanField(default=True)
    show_item_images = models.BooleanField(default=True)
    screen_timeout = models.IntegerField(default=30)  # seconds before returning to welcome screen
    display_logo = models.BooleanField(default=True)
    thank_you_message = models.CharField(max_length=255, default="Thank you for your purchase!")

    def __str__(self):
        return f"Customer Display for {self.branch.name}"
