from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView
from django_scalar.views import scalar_viewer

from shortener.urls import redirect_urlpatterns

urlpatterns = [

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    path("api/docs/", scalar_viewer, name="scalar-docs"),

    path("api/auth/", include("users.urls")),
    path("api/", include("shortener.urls")),
    path("", include("frontend.urls")),
    *redirect_urlpatterns,
]