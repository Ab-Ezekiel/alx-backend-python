# messaging/signals.py
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import models

from .models import Message, Notification, MessageHistory

User = get_user_model()

@receiver(post_save, sender=Message)
def create_notification_on_message(sender, instance, created, **kwargs):
    if not created:
        return
    Notification.objects.create(user=instance.receiver, message=instance)

@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    if instance._state.adding:
        return
    try:
        old = Message.objects.get(pk=instance.pk)
    except Message.DoesNotExist:
        return
    if old.content != instance.content:
        MessageHistory.objects.create(message=old, old_content=old.content)
        instance.edited = True

@receiver(post_delete, sender=User)
def delete_user_related_data(sender, instance, **kwargs):
    """
    Ensure all user-related messaging data is removed when a User is deleted.
    This is defensive: the DB cascade should remove these already, but having
    explicit cleanup ensures any non-cascaded relations are handled.
    """
    # Delete notifications that reference this user directly
    Notification.objects.filter(user=instance).delete()

    # Delete messages where user was sender or receiver
    Message.objects.filter(models.Q(sender=instance) | models.Q(receiver=instance)).delete()

    # Delete message histories referencing messages of this user (defensive)
    MessageHistory.objects.filter(
        models.Q(message__sender=instance) | models.Q(message__receiver=instance)
    ).delete()
