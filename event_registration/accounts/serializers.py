from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from core.serializers import BaseSerializer
from .models import User


class UserSerializer(BaseSerializer):
    full_name = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField())
    def get_full_name(self, obj):
        return obj.full_name

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name",
            "full_name", "role", "bio", "profile_picture",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RegisterSerializer(BaseSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "email", "username", "first_name", "last_name",
            "password", "password_confirm", "role",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(BaseSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "access", "refresh", "user"]

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            email=attrs["email"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError({"email": "Invalid email or password."})
        if not user.is_active:
            raise serializers.ValidationError({"email": "This account has been deactivated."})

        tokens = RefreshToken.for_user(user)
        return {
            "email": user.email,
            "access": str(tokens.access_token),
            "refresh": str(tokens),
            "user": UserSerializer(user).data,
        }


class LogoutSerializer(BaseSerializer):
    refresh = serializers.CharField()

    class Meta:
        model = User
        fields = ["refresh"]

    def validate_refresh(self, value):
        try:
            RefreshToken(value)
        except Exception:
            raise serializers.ValidationError("Invalid or expired refresh token.")
        return value


class UpdateProfileSerializer(BaseSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "bio", "profile_picture", "username"]


class ChangePasswordSerializer(BaseSerializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["old_password", "new_password", "new_password_confirm"]

    def validate(self, attrs):
        if attrs["new_password"] != attrs.pop("new_password_confirm"):
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value