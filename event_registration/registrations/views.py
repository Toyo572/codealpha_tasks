from django.shortcuts import render

# Create your views here.
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from events.models import Event
from core.views import BaseAPIView
from core.permissions import IsOrganizer, IsRegistrationOwner
from core.responses import success_response, created_response, error_response
from .models import Registration
from .serializers import (
    RegistrationSerializer,
    RegistrationCancelSerializer,
    OrganizerRegistrationSerializer,
)


@extend_schema(tags=["Registrations"])
class RegisterForEventView(BaseAPIView):
    """
    POST /api/v1/registrations/   — register the authenticated user for an event.
    Validates: event is published, user not already registered, spots available.
    """
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        registration = serializer.save()
        return created_response(
            data=RegistrationSerializer(registration, context={"request": request}).data,
            message="Successfully registered for the event.",
        )


@extend_schema(tags=["Registrations"])
class MyRegistrationsView(BaseAPIView):
    """
    GET /api/v1/registrations/me/   — list all registrations for the current user.
    """
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Registration.objects.filter(attendee=self.request.user)
            .select_related("event", "event__category", "event__organizer")
        )

    def get(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)


@extend_schema(tags=["Registrations"])
class CancelRegistrationView(BaseAPIView):
    """
    POST /api/v1/registrations/<id>/cancel/  — cancel a specific registration.
    Only the attendee who owns the registration can cancel it.
    """
    serializer_class = RegistrationCancelSerializer
    permission_classes = [IsAuthenticated, IsRegistrationOwner]

    def get_object(self, pk):
        try:
            return Registration.objects.select_related("attendee", "event").get(
                pk=pk, attendee=self.request.user
            )
        except Registration.DoesNotExist:
            return None

    def post(self, request, pk):
        registration = self.get_object(pk)
        if not registration:
            return error_response(message="Registration not found.", status_code=404)

        serializer = self.get_serializer(
            data=request.data,
            context={"request": request, "registration": registration},
        )
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return success_response(
            data=RegistrationSerializer(updated, context={"request": request}).data,
            message="Registration cancelled successfully.",
        )


@extend_schema(tags=["Organizer — Registrations"])
class EventRegistrationsView(BaseAPIView):
    """
    GET /api/v1/registrations/event/<event_id>/
    Organizer-only: view all registrations for one of their events.
    """
    serializer_class = OrganizerRegistrationSerializer
    permission_classes = [IsAuthenticated, IsOrganizer]

    def get_queryset(self, event_id):
        return (
            Registration.objects.filter(
                event__id=event_id,
                event__organizer=self.request.user,
            )
            .select_related("attendee", "event")
        )

    def get(self, request, event_id):
        queryset = self.get_queryset(event_id)
        if not queryset.exists():
            
            if not Event.objects.filter(id=event_id, organizer=request.user).exists():
                return error_response(message="Event not found.", status_code=404)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)
