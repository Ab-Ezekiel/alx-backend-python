# messaging/models.py
from django.db import models
from django.contrib.auth import get_user_model
from .managers import UnreadMessagesManager  # add this import


User = get_user_model()


class UnreadMessagesManager(models.Manager):
    """
    Manager that filters unread messages for a given user.
    Usage: Message.unread.for_user(user)
    """
    def get_queryset(self):
        return super().get_queryset().filter(read=False)

    def for_user(self, user):
        """
        Return unread messages where the given user is receiver.
        Use .only() to fetch necessary fields only.
        """
        # Only select commonly needed fields to reduce bandwidth
        return self.get_queryset().filter(receiver=user).only('id', 'sender_id', 'receiver_id', 'content', 'timestamp', 'parent_message_id')


class Message(models.Model):
    sender = models.ForeignKey(
        User, related_name='sent_messages', on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        User, related_name='received_messages', on_delete=models.CASCADE
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # Threading fields
    parent_message = models.ForeignKey(
        'self',
        related_name='replies',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    # root of the thread (self for root messages, or parent's thread_root)
    thread_root = models.ForeignKey(
        'self',
        related_name='thread_messages',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    edited = models.BooleanField(default=False)
    edited_by = models.ForeignKey(
        User,
        related_name='edited_messages',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    # NEW field required by this task: whether message has been read
    read = models.BooleanField(default=False)

    # Managers: default + unread manager
    objects = models.Manager()  # default manager
    unread = UnreadMessagesManager()  # custom manager

    def __str__(self):
        return f"Message {self.pk} from {self.sender} to {self.receiver}"

    def save(self, *args, **kwargs):
        """
        If this message has a parent and thread_root not explicitly set,
        ensure thread_root is set to the parent's thread_root or the parent itself.
        This keeps thread_root consistent without requiring a separate signal.
        """
        if self.parent_message and not self.thread_root:
            parent = self.parent_message
            # parent.thread_root can be None for a root parent; use parent in that case
            self.thread_root = parent.thread_root or parent
        # For root messages, set thread_root to self after saving (can't set before pk)
        super().save(*args, **kwargs)
        if not self.parent_message and not self.thread_root:
            # set thread_root to self for root messages
            self.thread_root = self
            # update without triggering recursion
            Message.objects.filter(pk=self.pk).update(thread_root=self)

    # Helper: return queryset of all messages in this thread
    def get_thread_qs(self):
        """
        Return a queryset of all messages that belong to this thread.
        Uses select_related/prefetch_related for efficient retrieval.
        """
        root = self.thread_root or self
        qs = Message.objects.filter(thread_root=root).select_related(
            'sender', 'receiver', 'edited_by', 'parent_message'
        ).prefetch_related('replies', 'history')
        return qs.order_by('timestamp')

# Keep the rest of your models (Notification, MessageHistory) unchanged
class Notification(models.Model):
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    message = models.ForeignKey(Message, related_name='notifications', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification {self.pk} for {self.user} - read={self.is_read}"

class MessageHistory(models.Model):
    message = models.ForeignKey(Message, related_name='history', on_delete=models.CASCADE)
    old_content = models.TextField()
    edited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-edited_at']

    def __str__(self):
        return f"History for Message {self.message_id} at {self.edited_at.isoformat()}"


