# messaging_app/chats/permissions.py
from rest_framework import permissions
from .models import Conversation, Message

class IsParticipantOfConversation(permissions.BasePermission):
    """
    Permission that:
    - allows only authenticated users to access the API (view-level)
    - allows only conversation participants to retrieve/update/delete that conversation
    - allows only participants to create/list messages inside conversations they are part of
    """

    def has_permission(self, request, view):
        # Require authentication for any access to the API endpoints where this permission is applied
        if not request.user or not request.user.is_authenticated:
            return False

        # For create actions we sometimes need to allow the view-level check to pass,
        # but the object-level check (has_object_permission) will enforce membership once the object exists.
        # For example, creating a Conversation is allowed (authenticated users may create),
        # but creating a Message requires further checks in has_object_permission / view.perform_create.
        return True

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission:
        - If the object is a Conversation: user must be a participant
        - If the object is a Message: user must be a participant in the message's conversation
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Conversation object -> check participants
        if isinstance(obj, Conversation):
            return obj.participants.filter(user_id=user.user_id).exists()

        # Message object -> check participants of its conversation
        if isinstance(obj, Message):
            return obj.conversation.participants.filter(user_id=user.user_id).exists()

        # Default deny for unknown object types
        return False

    # Optional convenience: for view-level create of messages under a conversation (nested action),
    # you may want to call this helper from the view to enforce membership before creating.
    @staticmethod
    def user_is_participant_of_conversation(user, conversation):
        if not user or not user.is_authenticated:
            return False
        return conversation.participants.filter(user_id=user.user_id).exists()
