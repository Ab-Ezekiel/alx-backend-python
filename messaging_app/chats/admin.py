from django.contrib import admin
from .models import User, Conversation, Message
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class CustomUserAdmin(BaseUserAdmin):
    model = User
    readonly_fields = ('user_id', 'created_at', 'password_hash')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Extra', {'fields': ('phone_number', 'role', 'user_id', 'password_hash', 'created_at')}),
    )
    
admin.site.register(User, CustomUserAdmin)
admin.site.register(Conversation)
admin.site.register(Message)

