from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.base_serializers import TimestampedModelSerializer
from .models import StaffInvitation

User = get_user_model()



class UserSerializer(TimestampedModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "role", "phone", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(help_text="Refresh token to blacklist on logout.")

    def validate_refresh(self, value):
        try:
            token = RefreshToken(value)
            token.blacklist()
        except Exception:
            raise serializers.ValidationError("Invalid or already blacklisted refresh token.")
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user

class CustomerRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "phone", "password", "password_confirm"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        # Customers always get customer role regardless of input
        validated_data["role"] = User.Role.CUSTOMER
        return User.objects.create_user(**validated_data)


class CustomerLoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if self.user.role != User.Role.CUSTOMER:
            raise serializers.ValidationError(
                {"detail": "This login is for customers only. Please use the correct login endpoint."}
            )
        data["user"] = UserSerializer(self.user).data
        return data



class StaffRegisterSerializer(serializers.ModelSerializer):
    """
    Staff can only register via a valid invitation token sent to their email.
    """
    token = serializers.UUIDField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["token", "first_name", "last_name", "phone", "password", "password_confirm"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        token = attrs.get("token")
        try:
            invitation = StaffInvitation.objects.get(token=token)
        except StaffInvitation.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid invitation token."})

        if not invitation.is_valid:
            raise serializers.ValidationError(
                {"token": "This invitation has expired or has already been used."}
            )

        attrs["_invitation"] = invitation
        return attrs

    def create(self, validated_data):
        invitation = validated_data.pop("_invitation")
        validated_data.pop("token", None)  # remove token — not a User field
        validated_data["email"] = invitation.email
        validated_data["role"] = User.Role.STAFF
        user = User.objects.create_user(**validated_data)

        # Mark invitation as used — expires immediately
        invitation.status = StaffInvitation.Status.ACCEPTED
        invitation.save(update_fields=["status"])
        return user


class StaffLoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if self.user.role != User.Role.STAFF:
            raise serializers.ValidationError(
                {"detail": "This login is for staff only. Please use the correct login endpoint."}
            )
        data["user"] = UserSerializer(self.user).data
        return data



class AdminRegisterSerializer(serializers.ModelSerializer):
    """
    Admin registration — secured by ADMIN_REGISTRATION_SECRET in settings.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    registration_secret = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "email", "first_name", "last_name", "phone",
            "password", "password_confirm", "registration_secret",
        ]

    def validate(self, attrs):
        from django.conf import settings
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        secret = attrs.pop("registration_secret", "")
        expected = getattr(settings, "ADMIN_REGISTRATION_SECRET", None)
        if not expected or secret != expected:
            raise serializers.ValidationError(
                {"registration_secret": "Invalid admin registration secret."}
            )
        return attrs

    def create(self, validated_data):
        validated_data["role"] = User.Role.ADMIN
        validated_data["is_staff"] = True
        return User.objects.create_user(**validated_data)


class AdminLoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if self.user.role != User.Role.ADMIN:
            raise serializers.ValidationError(
                {"detail": "This login is for admins only. Please use the correct login endpoint."}
            )
        data["user"] = UserSerializer(self.user).data
        return data


# ── Staff Invitation ──────────────────────────────────────────────────────────

class StaffInvitationSerializer(serializers.ModelSerializer):
    invited_by_email = serializers.CharField(source="invited_by.email", read_only=True)

    class Meta:
        model = StaffInvitation
        fields = [
            "id", "token", "email", "invited_by", "invited_by_email",
            "status", "expires_at", "created_at",
        ]
        read_only_fields = ["id", "token", "invited_by", "invited_by_email", "status", "expires_at", "created_at"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")

        # Cancel any existing pending invitation for this email before creating a new one
        StaffInvitation.objects.filter(
            email=value, status=StaffInvitation.Status.PENDING
        ).update(status=StaffInvitation.Status.EXPIRED)
        return value

    def create(self, validated_data):
        from django.utils import timezone
        from datetime import timedelta
        validated_data["invited_by"] = self.context["request"].user
        validated_data["expires_at"] = timezone.now() + timedelta(hours=24)
        invitation = super().create(validated_data)
        self._send_invitation_email(invitation)
        return invitation

    def _send_invitation_email(self, invitation):
        from django.core.mail import EmailMessage
        from django.conf import settings

        register_url = (
            f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:8000')}"
            f"/api/v1/auth/staff/register/"
        )
        # Pass token as a separate line so MIME wrapping never touches the UUID
        body = (
            f"Hello,\n\n"
            f"You have been invited by {invitation.invited_by.full_name} "
            f"to register as a staff member.\n\n"
            f"Use the link below to complete your registration "
            f"(expires in 24 hours):\n\n"
            f"{register_url}\n\n"
            f"Your registration token (copy exactly):\n"
            f"{invitation.token}\n\n"
            f"If you did not expect this email, please ignore it."
        )
        email = EmailMessage(
            subject="You've been invited to join the restaurant team",
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invitation.email],
        )
        # Force UTF-8, no quoted-printable wrapping that corrupts UUIDs
        email.encoding = "utf-8"
        email.send(fail_silently=False)