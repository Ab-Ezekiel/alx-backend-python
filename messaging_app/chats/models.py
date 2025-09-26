from django.db import models
import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser

ROLE_GUEST = 'guest'
ROLE_HOST = 'host'
ROLE_ADMIN = 'admin'
ROLE_CHOICES = [
    (ROLE_GUEST, 'Guest'),
    (ROLE_HOST, 'Host'),
    (ROLE_ADMIN, 'Admin'),
]


class User(AbstractUser):
    """
    Custom user model extending AbstractUser.
    Uses a UUID primary key (user_id) and enforces unique email.
    Keeps password hash in 'password' (Django) and mirrors it in password_hash.
    """
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # override email to be unique (and indexed)
    email = models.EmailField(unique=True, db_index=True)

    # make first and last name required (non-null)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    phone_number = models.CharField(max_length=20, null=True, blank=True)

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_GUEST)

    created_at = models.DateTimeField(auto_now_add=True)

    # Keep a separate column named `password_hash` to match DB spec.
    # This will be synchronized with Django's `password` field (which stores the hash).
    password_hash = models.CharField(max_length=128, editable=False, blank=True)

    # Keep default USERNAME_FIELD (username), but ensure email required when creating users
    REQUIRED_FIELDS = ['email']

    def save(self, *args, **kwargs):
        # keep password_hash in sync with Django's password field (hashed value)
        if self.password:
            self.password_hash = self.password
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.email})"


class Conversation(models.Model):
    """
    Conversation that tracks participants (many-to-many to User).
    """
    conversation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # short representation
        return f"Conversation {str(self.conversation_id)[:8]}"


class Message(models.Model):
    """
    Messages belonging to a Conversation.
    """
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    message_body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['sent_at']),
        ]

    def __str__(self):
        return f"Message {str(self.message_id)[:8]} from {self.sender}"

