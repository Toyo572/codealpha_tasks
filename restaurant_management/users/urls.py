from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema

from .views import CustomerAuthViewSet, StaffAuthViewSet, AdminAuthViewSet, UserManagementViewSet


class DecoratedTokenRefreshView(TokenRefreshView):
    @extend_schema(tags=["Auth - Token"], summary="Refresh access token")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# Use SimpleRouter — prevents phantom list/create/update/delete routes
# on action-only viewsets
router = SimpleRouter()
router.register("customer", CustomerAuthViewSet, basename="customer-auth")
router.register("staff", StaffAuthViewSet, basename="staff-auth")
router.register("admin", AdminAuthViewSet, basename="admin-auth")
router.register("users", UserManagementViewSet, basename="user-management")

urlpatterns = [
    path("", include(router.urls)),
    path("token/refresh/", DecoratedTokenRefreshView.as_view(), name="token-refresh"),
]