from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),


    path("api/v1/auth/", include("users.urls")),
    path("api/v1/menu/", include("menu.urls")),
    path("api/v1/", include("tables.urls")),
    path("api/v1/orders/", include("orders.urls")),
    path("api/v1/inventory/", include("inventory.urls")),
    path("api/v1/reports/", include("reports.urls")),
]