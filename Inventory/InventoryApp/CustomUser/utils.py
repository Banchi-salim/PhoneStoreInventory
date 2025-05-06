from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


def setup_default_permissions():
    """
    Set up default groups and permissions for the application.
    This function should be called after migrations via a post-migrate signal.
    """
    # Create Admin group if it doesn't exist
    admin_group, _ = Group.objects.get_or_create(name='Admin')

    # Create Staff group if it doesn't exist
    staff_group, _ = Group.objects.get_or_create(name='Staff')

    # Clear existing permissions to avoid duplicates
    admin_group.permissions.clear()
    staff_group.permissions.clear()

    # Add all permissions to Admin group
    all_permissions = Permission.objects.all()
    admin_group.permissions.add(*all_permissions)

    # Set up Staff permissions
    # First, get content types for models that staff can interact with
    from inventory.models import Product, Inventory
    from sales.models import Sale, SaleItem, Customer

    staff_models = [Product, Inventory, Sale, SaleItem, Customer]
    staff_content_types = ContentType.objects.get_for_models(*staff_models).values()

    # Get view and add permissions for these models
    staff_permissions = Permission.objects.filter(
        Q(codename__startswith='view_') | Q(codename__startswith='add_'),
        content_type__in=staff_content_types
    )

    # Add custom permissions
    custom_permissions = Permission.objects.filter(
        codename__in=['can_access_staff_portal']
    )

    # Combine and add to staff group
    staff_group.permissions.add(*staff_permissions, *custom_permissions)
