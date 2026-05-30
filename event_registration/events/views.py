from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema

from core.views import BaseAPIView
from core.permissions import IsOrganizer, IsEventOrganizer
from core.responses import success_response, created_response, no_content_response, error_response
from .models import Event, EventCategory
from .serializers import (
    EventListSerializer,
    EventDetailSerializer,
    EventWriteSerializer,
    EventCategorySerializer,
)
from .filters import EventFilter


# ── Public event endpoints ────────────────────────────────────────────────────

class EventListView(BaseAPIView):
    """Paginated list of all published events."""
    serializer_class = EventListSerializer
    permission_classes = [AllowAny]
    filterset_class = EventFilter
    search_fields = ["title", "description", "location", "tags"]
    ordering_fields = ["start_datetime", "price", "created_at"]
    ordering = ["-start_datetime"]

    def get_queryset(self):
        return (
            Event.objects.filter(status=Event.Status.PUBLISHED)
            .select_related("organizer", "category")
        )

    @extend_schema(tags=["Events"], operation_id="public_events_list",
                   summary="List published events")
    def get(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)


class EventDetailView(BaseAPIView):
    """Full detail of a single published event."""
    serializer_class = EventDetailSerializer
    permission_classes = [AllowAny]

    def get_event(self, pk):
        try:
            return Event.objects.select_related("organizer", "category").get(
                pk=pk, status=Event.Status.PUBLISHED
            )
        except Event.DoesNotExist:
            return None

    @extend_schema(tags=["Events"], operation_id="public_events_detail",
                   summary="Retrieve a published event")
    def get(self, request, pk):
        event = self.get_event(pk)
        if event is None:
            return error_response(message="Event not found.", status_code=404)
        serializer = self.get_serializer(event)
        return success_response(data=serializer.data)


# ── Organizer event management ────────────────────────────────────────────────

class OrganizerEventListView(BaseAPIView):
    """List all events owned by the organizer / create a new event."""
    serializer_class = EventWriteSerializer
    permission_classes = [IsAuthenticated, IsOrganizer]

    def get_queryset(self):
        return Event.objects.filter(organizer=self.request.user).select_related("category")

    @extend_schema(tags=["Organizer — Events"], operation_id="organizer_events_list",
                   summary="List organizer's events")
    def get(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = EventListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = EventListSerializer(queryset, many=True, context={"request": request})
        return success_response(data=serializer.data)

    @extend_schema(tags=["Organizer — Events"], operation_id="organizer_events_create",
                   summary="Create a new event")
    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return created_response(data=serializer.data, message="Event created successfully.")


class OrganizerEventDetailView(BaseAPIView):
    """Retrieve / update / delete a single event owned by the organizer."""
    serializer_class = EventWriteSerializer
    permission_classes = [IsAuthenticated, IsOrganizer, IsEventOrganizer]

    def get_object(self, pk):
        try:
            return Event.objects.get(pk=pk, organizer=self.request.user)
        except Event.DoesNotExist:
            return None

    @extend_schema(tags=["Organizer — Events"], operation_id="organizer_events_detail",
                   summary="Retrieve own event")
    def get(self, request, pk):
        event = self.get_object(pk)
        if not event:
            return error_response(message="Event not found.", status_code=404)
        serializer = EventDetailSerializer(event, context={"request": request})
        return success_response(data=serializer.data)

    @extend_schema(tags=["Organizer — Events"], operation_id="organizer_events_update",
                   summary="Update own event")
    def patch(self, request, pk):
        event = self.get_object(pk)
        if not event:
            return error_response(message="Event not found.", status_code=404)
        serializer = self.get_serializer(
            event, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="Event updated successfully.")

    @extend_schema(tags=["Organizer — Events"], operation_id="organizer_events_delete",
                   summary="Delete own event")
    def delete(self, request, pk):
        event = self.get_object(pk)
        if not event:
            return error_response(message="Event not found.", status_code=404)
        event.delete()
        return no_content_response("Event deleted successfully.")


# ── Categories ────────────────────────────────────────────────────────────────

class CategoryListView(BaseAPIView):
    """List all categories / create one (organizer only)."""
    serializer_class = EventCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EventCategory.objects.all()

    @extend_schema(tags=["Categories"], operation_id="categories_list",
                   summary="List all categories")
    def get(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    @extend_schema(tags=["Categories"], operation_id="categories_create",
                   summary="Create a category (organizer only)")
    def post(self, request):
        if request.user.role != "organizer":
            return error_response(
                message="Only organizers can create categories.", status_code=403
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return created_response(data=serializer.data, message="Category created.")