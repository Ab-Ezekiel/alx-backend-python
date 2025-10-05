# messaging/admin.py
from django.contrib import admin
from .models import Message, Notification, MessageHistory

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'timestamp', 'edited')
    list_filter = ('sender', 'receiver', 'timestamp', 'edited')
    search_fields = ('sender__username', 'receiver__username', 'content')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username',)

@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'edited_at')
    search_fields = ('message__content',)
