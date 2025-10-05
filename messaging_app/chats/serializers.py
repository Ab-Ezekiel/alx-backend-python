# messaging_app/chats/serializers.py
from rest_framework import serializers
from . import models
from .models import Conversation, Message, User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the custom User model.
    - password is write_only and set via set_password().
    - password_hash is read-only (keeps in sync with Django password hash).
    """
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = models.User
        fields = (
            "user_id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "role",
            "created_at",
            "password",
        )
        read_only_fields = ("user_id", "created_at")
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = models.User(**validated_data)
        if password:
            user.set_password(password)
        else:
            # If no password provided, create unusable password
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message.
    - sender is read-only nested user info for GET responses.
    - sender_id is write-only field used to create messages.
    """
    sender = UserSerializer(read_only=True)
    sender_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=models.User.objects.all(), source="sender"
    )

    class Meta:
        model = models.Message
        fields = ("message_id", "sender", "sender_id", "conversation", "message_body", "sent_at")
        read_only_fields = ("message_id", "sent_at")

    def validate(self, attrs):
            """
            Ensure that if a conversation is provided, the sender is a participant
            of that conversation.
            """
            sender = attrs.get("sender")  # set by sender_id field
            conversation = attrs.get("conversation") or self.initial_data.get("conversation")
            # If conversation is an int/uuid in initial_data, let DB/field-level handle FK resolution later.
            if conversation and sender:
                # conversation may be a Conversation instance (write path), or a PK; handle both.
                conv_obj = conversation if isinstance(conversation, Conversation) else None
                if conv_obj is None:
                    # attempt to fetch conversation by given pk
                    try:
                        conv_obj = Conversation.objects.get(pk=conversation)
                    except Exception:
                        # Let DRF's FK validation handle invalid PK; only raise if conversation exists but sender not participant
                        conv_obj = None
                if conv_obj and not conv_obj.participants.filter(pk=sender.pk).exists():
                    raise serializers.ValidationError("Sender must be a participant in the conversation.")
            return attrs

    def create(self, validated_data):
        # The PrimaryKeyRelatedField above sets 'sender' in validated_data
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    """
    Conversation serializer which:
    - shows participants as nested UserSerializer (read).
    - accepts participants_ids (list of user primary keys / UUIDs) on write.
    - includes nested messages (read-only).
    """
    participants = UserSerializer(many=True, read_only=True)
    participants_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=models.User.objects.all(), source="participants"
    )

    # include nested messages as read-only list
    messages = serializers.SerializerMethodField()

    class Meta:
        model = models.Conversation
        fields = ("conversation_id", "participants", "participants_ids", "created_at", "messages")
        read_only_fields = ("conversation_id", "created_at", "messages")

    def get_messages(self, obj):
        # Return nested messages using MessageSerializer
        qs = obj.messages.all().order_by("-sent_at")
        return MessageSerializer(qs, many=True).data

    def validate(self, attrs):
        """
        Ensure there is at least one participant (or more, depending on your rules).
        """
        participants = attrs.get("participants")
        # If participants is None then this is likely an update without participants.
        if participants is not None and len(participants) == 0:
            raise serializers.ValidationError("A conversation must have at least one participant.")
        return attrs

    def create(self, validated_data):
        # 'participants' will be provided from participants_ids via source="participants"
        participants = validated_data.pop("participants", [])
        conversation = models.Conversation.objects.create(**validated_data)
        if participants:
            conversation.participants.set(participants)
        return conversation

    def update(self, instance, validated_data):
        participants = validated_data.pop("participants", None)
        # update other fields (none expected except participants)
        instance = super().update(instance, validated_data)
        if participants is not None:
            instance.participants.set(participants)
        return instance
