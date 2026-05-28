from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ReportViewSet

router = SimpleRouter()
router.register("", ReportViewSet, basename="report")

urlpatterns = [
    path("", include(router.urls)),
]