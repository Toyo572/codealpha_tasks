from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from django.conf import settings

# Scalar UI served via a simple HTML page — no admin URLs
def scalar_ui(request):
    from django.http import HttpResponse
    html = """<!DOCTYPE html>
<html>
<head>
  <title>Event Registration API — Scalar</title>
  <meta charset="utf-8"/>
</head>
<body>
  <script
    id="api-reference"
    data-url="/api/schema/"
    data-proxy-url="https://proxy.scalar.com">
  </script>
  <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
</body>
</html>"""
    return HttpResponse(html)


urlpatterns = [
    # OpenAPI schema (machine-readable)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Scalar browser UI
    path("api/docs/", scalar_ui, name="scalar-ui"),
    # Redoc (bonus alternative)
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # App routes
    path("api/v1/accounts/", include("accounts.urls")),
    path("api/v1/events/", include("events.urls")),
    path("api/v1/registrations/", include("registrations.urls")),
]
