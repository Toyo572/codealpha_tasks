from django.urls import path

from .views import RedirectView, URLDetailView, URLListCreateView

urlpatterns = [
    # API endpoints
    path("urls/", URLListCreateView.as_view(), name="url-list-create"),
    path("urls/<int:pk>/", URLDetailView.as_view(), name="url-detail"),
]

# The redirect route is mounted at root level from config/urls.py
redirect_urlpatterns = [
    path("<str:short_code>/", RedirectView.as_view(), name="url-redirect"),
]