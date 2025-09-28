# messaging_app/chats/permissions.py
from rest_framework import permissions
from .models import Conversation, Message

class IsParticipant(permissions.BasePermission):
    """
    Object-level permission: allow access only if the requesting user
    is a participant in the Conversation (or the Conversation of the Message).
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # If object is a Conversation, check participants by user_id
        if isinstance(obj, Conversation):
            return obj.participants.filter(user_id=user.user_id).exists()

        # If object is a Message, check the conversation's participants by user_id
        if isinstance(obj, Message):
            return obj.conversation.participants.filter(user_id=user.user_id).exists()

        return False
