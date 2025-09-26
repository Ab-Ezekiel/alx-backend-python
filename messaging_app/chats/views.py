# messaging_app/chats/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Conversation:
    - list: returns conversations the requesting user participates in
    - create: create a new conversation (provide participants_ids)
    - retrieve/update/destroy: standard ModelViewSet behavior (protected by permission)
    - messages (custom action): GET list messages in this conversation, POST send message to this conversation
    """
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return conversations the request.user is a participant of
        user = self.request.user
        return Conversation.objects.filter(participants=user).distinct()

    def perform_create(self, serializer):
        # ConversationSerializer handles participants via participants_ids.
        serializer.save()

    @action(detail=True, methods=['get', 'post'], url_path='messages', url_name='conversation-messages')
    def messages(self, request, pk=None):
        """
        GET: return messages for this conversation (paginated by default DRF settings).
        POST: create/send a new message in this conversation. Request body should include `message_body`.
              Sender is set to request.user (server-side) to avoid spoofing.
        """
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure the requester is a participant
        if not conversation.participants.filter(pk=request.user.pk).exists():
            raise PermissionDenied("You are not a participant of this conversation.")

        if request.method == 'GET':
            msgs = conversation.messages.all().order_by('-sent_at')
            page = self.paginate_queryset(msgs)
            if page is not None:
                serializer = MessageSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = MessageSerializer(msgs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # POST - create a message in this conversation; sender forced to request.user
        serializer = MessageSerializer(data=request.data)
        # ensure conversation field (if present) matches pk or we inject conversation instance
        # Prefer to pass the conversation instance into serializer.validated_data by supplying it as context in save()
        if serializer.is_valid():
            # Enforce sender and conversation server-side
            # If serializer expects 'sender' field via sender_id, we bypass by calling save with sender and conversation.
            try:
                message = serializer.save(sender=request.user, conversation=conversation)
            except ValidationError as exc:
                raise exc
            out = MessageSerializer(message)
            return Response(out.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Message:
    - list: can filter by `?conversation=<conversation_id>` query param
    - create: create message; sender will be set to request.user (server-side)
    """
    queryset = Message.objects.all().order_by('-sent_at')
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            qs = qs.filter(conversation__pk=conversation_id)
        # Optionally restrict to conversations user participates in:
        # only return messages for conversations the requesting user participates in
        qs = qs.filter(conversation__participants=self.request.user).distinct()
        return qs

    def perform_create(self, serializer):
        # Ensure the user is a participant of the conversation being posted to
        conversation = serializer.validated_data.get('conversation', None)
        if conversation is None:
            # If conversation key was not resolved to instance yet, attempt to extract from initial data
            conv_pk = self.request.data.get('conversation')
            if not conv_pk:
                raise ValidationError({"conversation": "This field is required."})
            try:
                conversation = Conversation.objects.get(pk=conv_pk)
            except Conversation.DoesNotExist:
                raise ValidationError({"conversation": "Conversation does not exist."})

        if not conversation.participants.filter(pk=self.request.user.pk).exists():
            raise PermissionDenied("You are not a participant of this conversation.")

        # force the sender to be request.user (ignore any sender_id submitted by client)
        serializer.save(sender=self.request.user)
