# messaging/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, Notification

@receiver(post_save, sender=Message)
def create_notification_on_message(sender, instance, created, **kwargs):
    """
    When a new Message is created, create a Notification for the receiver.
    """
    if not created:
        return

    Notification.objects.create(user=instance.receiver, message=instance)
