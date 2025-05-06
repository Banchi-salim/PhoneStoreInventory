from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .utils import setup_default_permissions

@receiver(post_migrate)
def create_default_groups_and_permissions(sender, **kwargs):
    """
    Signal handler to create default groups and permissions
    after migrations are complete.
    """
    setup_default_permissions()