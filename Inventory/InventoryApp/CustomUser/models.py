from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Adds additional fields for staff vs admin roles.
    """
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='staff')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    branch = models.ForeignKey('inventory.Branch', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        permissions = [
            ('can_access_admin_portal', 'Can access admin portal'),
            ('can_access_staff_portal', 'Can access staff portal'),
            ('can_manage_inventory', 'Can manage inventory'),
            ('can_view_reports', 'Can view reports'),
            ('can_export_data', 'Can export data'),
            ('can_manage_users', 'Can manage users'),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.user_type})"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)

        if creating:
            # Auto-assign groups based on user_type
            if self.user_type == 'admin':
                admin_group, _ = Group.objects.get_or_create(name='Admin')
                self.groups.add(admin_group)
            elif self.user_type == 'staff':
                staff_group, _ = Group.objects.get_or_create(name='Staff')
                self.groups.add(staff_group)
