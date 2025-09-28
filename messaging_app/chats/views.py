# messaging_app/chats/views.py
from django.core.exceptions import FieldError
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .permissions import IsParticipantOfConversation


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    # Enforce authentication + object-level participant checks
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['participants__email']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        try:
            # Explicitly reference the real PK field name `user_id`
            return Conversation.objects.filter(participants__user_id=user.user_id).distinct()
        except FieldError as ex:
            import logging
            logging.exception("FieldError while building Conversation queryset: %s", ex)
            return Conversation.objects.none()

    def perform_create(self, serializer):
        # Creating a conversation is allowed for authenticated users; serializer will set participants
        serializer.save()

    @action(detail=True, methods=['get', 'post'], url_path='messages', url_name='conversation-messages')
    def messages(self, request, pk=None):
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure the requester is a participant (use permission helper)
        if not IsParticipantOfConversation.user_is_participant_of_conversation(request.user, conversation):
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
        data = request.data.copy()
        data['conversation'] = str(conversation.pk)
        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            try:
                message = serializer.save(sender=request.user, conversation=conversation)
            except ValidationError as exc:
                raise exc
            out = MessageSerializer(message)
            return Response(out.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().order_by('-sent_at')
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['message_body', 'sender__email']
    ordering_fields = ['sent_at']
    ordering = ['-sent_at']

    def get_queryset(self):
        try:
            qs = super().get_queryset()
            conversation_id = self.request.query_params.get('conversation')
            if conversation_id:
                qs = qs.filter(conversation__pk=conversation_id)
            # restrict to messages in conversations the requesting user participates in
            qs = qs.filter(conversation__participants__user_id=self.request.user.user_id).distinct()
            return qs
        except FieldError as ex:
            import logging
            logging.exception("FieldError while building Message queryset: %s", ex)
            return Message.objects.none()

    def perform_create(self, serializer):
        # Validate the conversation and membership
        conversation = serializer.validated_data.get('conversation', None)
        if conversation is None:
            conv_pk = self.request.data.get('conversation')
            if not conv_pk:
                raise ValidationError({"conversation": "This field is required."})
            try:
                conversation = Conversation.objects.get(pk=conv_pk)
            except Conversation.DoesNotExist:
                raise ValidationError({"conversation": "Conversation does not exist."})

        if not IsParticipantOfConversation.user_is_participant_of_conversation(self.request.user, conversation):
            raise PermissionDenied("You are not a participant of this conversation.")

        # Force the sender to the request user (ignore client-supplied sender_id)
        serializer.save(sender=self.request.user)
