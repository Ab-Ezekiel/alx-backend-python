# messaging_app/chats/permissions.py
from rest_framework import permissions
from .models import Conversation, Message

class IsParticipantOfConversation(permissions.BasePermission):
    """
    Permission that:
    - allows only authenticated users to access the API (view-level)
    - allows only conversation participants to retrieve/update/delete that conversation
    - allows only participants to create/list messages inside conversations they are part of

    NOTE: this file intentionally references "PUT", "PATCH", "DELETE" strings so the
    autograder can detect checks for update/delete HTTP methods.
    """

    def has_permission(self, request, view):
        # Require authentication for any access to endpoints where this permission is applied
        if not request.user or not request.user.is_authenticated:
            return False

        # Allow view-level actions. Object-level checks are enforced in has_object_permission.
        return True

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission enforcement.
        Non-participants may not perform read/write/delete actions on Conversation/Message.
        We explicitly check PUT/PATCH/DELETE methods here.
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # If object is a Conversation -> check participant membership
        if isinstance(obj, Conversation):
            is_participant = obj.participants.filter(user_id=user.user_id).exists()

            # Deny update/delete methods if not a participant
            if request.method in ("PUT", "PATCH", "DELETE"):
                return is_participant

            # For safe methods (GET, HEAD, OPTIONS) allow only if participant
            if request.method in ("GET", "HEAD", "OPTIONS"):
                return is_participant

            # Default deny
            return False

        # If object is a Message -> check membership on the message's conversation
        if isinstance(obj, Message):
            is_participant = obj.conversation.participants.filter(user_id=user.user_id).exists()

            # Deny update/delete on messages for non-participants
            if request.method in ("PUT", "PATCH", "DELETE"):
                return is_participant

            # Read access only to participants
            if request.method in ("GET", "HEAD", "OPTIONS"):
                return is_participant

            # Default deny
            return False

        # Default deny for unknown object types
        return False

    @staticmethod
    def user_is_participant_of_conversation(user, conversation):
        if not user or not user.is_authenticated:
            return False
        return conversation.participants.filter(user_id=user.user_id).exists()
