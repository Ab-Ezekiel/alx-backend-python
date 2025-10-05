# messaging/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Message, Notification, MessageHistory

@receiver(post_save, sender=Message)
def create_notification_on_message(sender, instance, created, **kwargs):
    """
    Create a Notification for the receiver when a new Message is created.
    """
    if not created:
        return
    Notification.objects.create(user=instance.receiver, message=instance)

@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    """
    Before updating a Message, if the content changed, save the old content
    to MessageHistory and mark the Message.edited flag True.

    This uses pre_save so we capture the content *before* it's overwritten.
    """
    # If this is a new instance (being created), don't log history
    if instance._state.adding:
        return

    try:
        # fetch the current state from the DB
        old = Message.objects.get(pk=instance.pk)
    except Message.DoesNotExist:
        # nothing to do if the DB record doesn't exist
        return

    # if content changed, save history and mark edited
    if old.content != instance.content:
        # store the old content; use old instance so we store the DB content
        MessageHistory.objects.create(message=old, old_content=old.content)
        # mark the message as edited; it will be saved in the same transaction
        instance.edited = True
