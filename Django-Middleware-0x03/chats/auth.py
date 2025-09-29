# messaging_app/chats/auth.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extend the token payload with useful user info.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        # if your custom user primary key field is user_id (UUID)
        try:
            token['user_id'] = str(user.user_id)
        except Exception:
            token['user_id'] = str(user.pk)
        token['role'] = getattr(user, 'role', None)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # include extra user fields in the response body as well
        data['user'] = {
            "user_id": str(self.user.user_id) if hasattr(self.user, "user_id") else str(self.user.pk),
            "username": self.user.username,
            "email": self.user.email,
            "first_name": getattr(self.user, "first_name", ""),
            "last_name": getattr(self.user, "last_name", ""),
            "role": getattr(self.user, "role", None),
        }
        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
