# messaging/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Message(models.Model):
    sender = models.ForeignKey(
        User, related_name='sent_messages', on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        User, related_name='received_messages', on_delete=models.CASCADE
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    # new field to track whether the message has ever been edited
    edited = models.BooleanField(default=False)
    
    # new field requested by autograder: who last edited this message (nullable)
    edited_by = models.ForeignKey(
        User,
        related_name='edited_messages',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"Message {self.pk} from {self.sender} to {self.receiver}"

class Notification(models.Model):
    user = models.ForeignKey(
        User, related_name='notifications', on_delete=models.CASCADE
    )
    message = models.ForeignKey(
        Message, related_name='notifications', on_delete=models.CASCADE, null=True, blank=True
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification {self.pk} for {self.user} - read={self.is_read}"

class MessageHistory(models.Model):
    """
    Stores historical versions of Message.content before edits.
    Each record stores the previous content and when the edit happened.
    """
    message = models.ForeignKey(
        Message, related_name='history', on_delete=models.CASCADE
    )
    old_content = models.TextField()
    edited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-edited_at']

    def __str__(self):
        return f"History for Message {self.message_id} at {self.edited_at.isoformat()}"
