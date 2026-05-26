from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view

from core.mixins import SuccessResponseMixin
from core.permissions import IsAdminUser
from .serializers import (
    UserSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    LogoutSerializer,
    CustomerRegisterSerializer,
    CustomerLoginSerializer,
    StaffRegisterSerializer,
    StaffLoginSerializer,
    AdminRegisterSerializer,
    AdminLoginSerializer,
    StaffInvitationSerializer,
)

User = get_user_model()


# ── Customer Auth ViewSet ─────────────────────────────────────────────────────

@extend_schema_view(
    register=extend_schema(tags=["Customer Auth"], summary="Customer registration"),
    login=extend_schema(tags=["Customer Auth"], summary="Customer login"),
    logout=extend_schema(tags=["Customer Auth"], summary="Logout (blacklist refresh token)"),
    me=extend_schema(tags=["Customer Auth"], summary="View or update own profile"),
    change_password=extend_schema(tags=["Customer Auth"], summary="Change password"),
)
class CustomerAuthViewSet(SuccessResponseMixin, viewsets.GenericViewSet):
    queryset = User.objects.none()

    def get_permissions(self):
        if self.action in ("register", "login"):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        return {
            "register": CustomerRegisterSerializer,
            "login": CustomerLoginSerializer,
            "logout": LogoutSerializer,
            "me": UserUpdateSerializer,
            "change_password": ChangePasswordSerializer,
        }.get(self.action, UserSerializer)

    @action(methods=["post"], detail=False, url_path="register")
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return self.get_success_response(UserSerializer(user).data, status.HTTP_201_CREATED)

    @action(methods=["post"], detail=False, url_path="login")
    def login(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return self.get_success_response(serializer.validated_data)

    @action(methods=["post"], detail=False, url_path="logout")
    def logout(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.get_success_response({"detail": "Successfully logged out."})

    @action(methods=["get", "patch"], detail=False, url_path="me")
    def me(self, request):
        if request.method == "GET":
            return self.get_success_response(UserSerializer(request.user).data)
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get_success_response(UserSerializer(request.user).data)

    @action(methods=["post"], detail=False, url_path="change-password")
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get_success_response({"detail": "Password changed successfully."})


# ── Staff Auth ViewSet ────────────────────────────────────────────────────────

@extend_schema_view(
    register=extend_schema(
        tags=["Staff Auth"],
        summary="Staff registration via invitation token",
    ),
    login=extend_schema(tags=["Staff Auth"], summary="Staff login"),
    logout=extend_schema(tags=["Staff Auth"], summary="Staff logout"),
    me=extend_schema(tags=["Staff Auth"], summary="View or update own profile"),
    change_password=extend_schema(tags=["Staff Auth"], summary="Change password"),
)
class StaffAuthViewSet(SuccessResponseMixin, viewsets.GenericViewSet):
    queryset = User.objects.none()

    def get_permissions(self):
        if self.action in ("register", "login"):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        return {
            "register": StaffRegisterSerializer,
            "login": StaffLoginSerializer,
            "logout": LogoutSerializer,
            "me": UserUpdateSerializer,
            "change_password": ChangePasswordSerializer,
        }.get(self.action, UserSerializer)

    @action(methods=["post"], detail=False, url_path="register")
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return self.get_success_response(UserSerializer(user).data, status.HTTP_201_CREATED)

    @action(methods=["post"], detail=False, url_path="login")
    def login(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return self.get_success_response(serializer.validated_data)

    @action(methods=["post"], detail=False, url_path="logout")
    def logout(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.get_success_response({"detail": "Successfully logged out."})

    @action(methods=["get", "patch"], detail=False, url_path="me")
    def me(self, request):
        if request.method == "GET":
            return self.get_success_response(UserSerializer(request.user).data)
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get_success_response(UserSerializer(request.user).data)

    @action(methods=["post"], detail=False, url_path="change-password")
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get_success_response({"detail": "Password changed successfully."})


# ── Admin Auth ViewSet ────────────────────────────────────────────────────────

@extend_schema_view(
    register=extend_schema(
        tags=["Admin Auth"],
        summary="Admin registration (requires ADMIN_REGISTRATION_SECRET)",
    ),
    login=extend_schema(tags=["Admin Auth"], summary="Admin login"),
    logout=extend_schema(tags=["Admin Auth"], summary="Admin logout"),
    me=extend_schema(tags=["Admin Auth"], summary="View or update own profile"),
    change_password=extend_schema(tags=["Admin Auth"], summary="Change password"),
    invite_staff=extend_schema(
        tags=["Admin Auth"],
        summary="Send staff invitation email (admin only)",
    ),
    list_invitations=extend_schema(
        tags=["Admin Auth"],
        summary="List all staff invitations (admin only)",
    ),
)
class AdminAuthViewSet(SuccessResponseMixin, viewsets.GenericViewSet):
    queryset = User.objects.none()

    def get_permissions(self):
        if self.action in ("register", "login"):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        return {
            "register": AdminRegisterSerializer,
            "login": AdminLoginSerializer,
            "logout": LogoutSerializer,
            "me": UserUpdateSerializer,
            "change_password": ChangePasswordSerializer,
            "invite_staff": StaffInvitationSerializer,
            "list_invitations": StaffInvitationSerializer,
        }.get(self.action, UserSerializer)

    @action(methods=["post"], detail=False, url_path="register")
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return self.get_success_response(UserSerializer(user).data, status.HTTP_201_CREATED)

    @action(methods=["post"], detail=False, url_path="login")
    def login(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return self.get_success_response(serializer.validated_data)

    @action(methods=["post"], detail=False, url_path="logout")
    def logout(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.get_success_response({"detail": "Successfully logged out."})

    @action(methods=["get", "patch"], detail=False, url_path="me")
    def me(self, request):
        if request.method == "GET":
            return self.get_success_response(UserSerializer(request.user).data)
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get_success_response(UserSerializer(request.user).data)

    @action(methods=["post"], detail=False, url_path="change-password")
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get_success_response({"detail": "Password changed successfully."})

    @action(methods=["post"], detail=False, url_path="invite-staff",
            permission_classes=[IsAdminUser])
    def invite_staff(self, request):
        serializer = StaffInvitationSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()
        return self.get_success_response(
            StaffInvitationSerializer(invitation).data, status.HTTP_201_CREATED
        )

    @action(methods=["get"], detail=False, url_path="invitations",
            permission_classes=[IsAdminUser])
    def list_invitations(self, request):
        from .models import StaffInvitation
        invitations = StaffInvitation.objects.select_related("invited_by").order_by("-created_at")
        serializer = StaffInvitationSerializer(invitations, many=True)
        return self.get_success_response(serializer.data)


# ── User Management ViewSet (Admin only) ──────────────────────────────────────

@extend_schema_view(
    list=extend_schema(tags=["User Management"], summary="List all users (admin only)"),
    retrieve=extend_schema(tags=["User Management"], summary="Get user by ID"),
    partial_update=extend_schema(tags=["User Management"], summary="Update user"),
    destroy=extend_schema(tags=["User Management"], summary="Delete user"),
)
class UserManagementViewSet(SuccessResponseMixin, viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    permission_classes = [IsAdminUser]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action == "partial_update":
            return UserUpdateSerializer
        return UserSerializer