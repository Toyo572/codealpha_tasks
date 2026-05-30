from django.urls import path
from .views import (
    EventListView,
    EventDetailView,
    OrganizerEventListView,
    OrganizerEventDetailView,
    CategoryListView,
)

urlpatterns = [
    # Public
    path("", EventListView.as_view(), name="event-list"),
    path("<uuid:pk>/", EventDetailView.as_view(), name="event-detail"),

    # Categories
    path("categories/", CategoryListView.as_view(), name="category-list"),

    # Organizer management
    path("manage/", OrganizerEventListView.as_view(), name="organizer-event-list"),
    path("manage/<uuid:pk>/", OrganizerEventDetailView.as_view(), name="organizer-event-detail"),
]
