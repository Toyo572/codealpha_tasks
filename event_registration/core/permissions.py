from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOrganizer(BasePermission):
    """Allows access only to users with the 'organizer' role."""
    message = "You must be an event organizer to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "organizer"
        )


class IsOrganizerOrReadOnly(BasePermission):
    """Read access for all authenticated users; write access only for organizers."""
    message = "You must be an event organizer to modify events."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "organizer"
        )


class IsEventOrganizer(BasePermission):
    """Object-level: only the organizer who owns the event can modify it."""
    message = "You do not have permission to modify this event."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.organizer == request.user


class IsRegistrationOwner(BasePermission):
    """Object-level: only the user who made the registration can view/cancel it."""
    message = "You do not have permission to access this registration."

    def has_object_permission(self, request, view, obj):
        return obj.attendee == request.user
