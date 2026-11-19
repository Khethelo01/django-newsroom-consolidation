"""Signals for the News application."""

from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate, post_save, m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import User


def sync_role(user):
    """Synchronise role groups and clear inapplicable reader subscriptions."""
    group, _ = Group.objects.get_or_create(name=user.role.title())
    role_groups = Group.objects.filter(
        name__in=["Reader", "Editor", "Journalist"]
    )
    user.groups.remove(*role_groups)
    user.groups.add(group)
    if user.role != "reader":
        user.publisher_subscriptions.clear()
        user.journalist_subscriptions.clear()


@receiver(post_save, sender=User)
def assign_group(sender, instance, **kwargs):
    """Update group membership after a user is saved."""
    sync_role(instance)


@receiver(post_migrate)
def create_role_permissions(sender, **kwargs):
    """Install the model permissions for each role after migrations."""
    if sender.name != "news":
        return
    for role, actions in {
        "Reader": ["view"],
        "Editor": ["view", "change", "delete"],
        "Journalist": ["add", "view", "change", "delete"],
    }.items():
        group, _ = Group.objects.get_or_create(name=role)
        codes = [
            f"{action}_{model}"
            for action in actions
            for model in ["article", "newsletter"]
        ]
        group.permissions.set(
            Permission.objects.filter(
                content_type__app_label="news", codename__in=codes
            )
        )


@receiver(m2m_changed, sender=User.publisher_subscriptions.through)
@receiver(m2m_changed, sender=User.journalist_subscriptions.through)
def restrict_subscriptions(sender, instance, action, reverse, **kwargs):
    """Reject reader subscriptions added by non-reader accounts."""
    if action == "pre_add" and not reverse and instance.role != "reader":
        raise ValidationError("Only readers can subscribe.")
