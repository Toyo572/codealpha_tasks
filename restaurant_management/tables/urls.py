from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TableViewSet, ReservationViewSet

router = DefaultRouter()
router.register("tables", TableViewSet, basename="table")
router.register("reservations", ReservationViewSet, basename="reservation")

urlpatterns = [
    path("", include(router.urls)),
]