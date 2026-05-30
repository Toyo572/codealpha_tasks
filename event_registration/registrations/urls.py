from django.urls import path
from .views import (
    RegisterForEventView,
    MyRegistrationsView,
    CancelRegistrationView,
    EventRegistrationsView,
)

urlpatterns = [
    # Attendee
    path("", RegisterForEventView.as_view(), name="register-for-event"),
    path("me/", MyRegistrationsView.as_view(), name="my-registrations"),
    path("<uuid:pk>/cancel/", CancelRegistrationView.as_view(), name="cancel-registration"),

    # Organizer
    path("event/<uuid:event_id>/", EventRegistrationsView.as_view(), name="event-registrations"),
]
