from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from drf_spectacular.utils import extend_schema

from core.views import BaseAPIView
from core.responses import success_response, created_response, error_response
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    LogoutSerializer,
    UserSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer,
)


@extend_schema(tags=["Auth"])
class RegisterView(BaseAPIView):
    """Create a new attendee or organizer account."""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return created_response(
            data=UserSerializer(user, context={"request": request}).data,
            message="Account created successfully.",
        )


@extend_schema(tags=["Auth"])
class LoginView(BaseAPIView):
    """Authenticate and receive JWT access + refresh tokens."""
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return success_response(
            data=serializer.validated_data,
            message="Login successful.",
        )


@extend_schema(tags=["Auth"])
class LogoutView(BaseAPIView):
    """Blacklist the refresh token to invalidate the session."""
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError as e:
            return error_response(message=str(e))
        return success_response(message="Logged out successfully.")


@extend_schema(tags=["Auth"])
class TokenRefreshView(BaseAPIView):
    """Exchange a valid refresh token for a new access token."""
    permission_classes = [AllowAny]
    serializer_class = TokenRefreshSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return success_response(
            data=serializer.validated_data,
            message="Token refreshed successfully.",
        )


@extend_schema(tags=["Profile"])
class MeView(BaseAPIView):
    """Retrieve or update the currently authenticated user's profile."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = self.get_serializer(request.user)
        return success_response(data=serializer.data)

    def patch(self, request):
        serializer = UpdateProfileSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=UserSerializer(request.user, context={"request": request}).data,
            message="Profile updated successfully.",
        )


@extend_schema(tags=["Profile"])
class ChangePasswordView(BaseAPIView):
    """Change the password for the authenticated user."""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return success_response(message="Password changed successfully.")