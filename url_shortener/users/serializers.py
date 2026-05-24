from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "password")
        read_only_fields = ("id",)

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "created_at")
        read_only_fields = ("id", "created_at")


class LoginSerializer(TokenObtainPairSerializer):
    """Extends simplejwt's pair serializer — returns access + refresh tokens."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class TokenRefreshSerializer(serializers.Serializer):
    """Wraps the incoming refresh token for schema visibility."""
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    """Accepts the refresh token to blacklist on logout."""
    refresh = serializers.CharField()