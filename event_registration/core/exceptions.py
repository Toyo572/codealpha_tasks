from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    Wraps ALL DRF exceptions into the uniform shape:
        { "success": false, "message": "...", "errors": {...} }
    """
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled server error
        return Response(
            {"success": False, "message": "An unexpected error occurred. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    error_data = response.data

    # DRF validation errors come back as a dict of field → list-of-messages
    # or sometimes as a plain list or a {"detail": "..."} string.
    if isinstance(error_data, dict) and "detail" in error_data:
        message = str(error_data["detail"])
        errors = None
    elif isinstance(error_data, dict):
        message = "Validation failed. Please check the errors below."
        errors = _flatten_errors(error_data)
    elif isinstance(error_data, list):
        message = str(error_data[0]) if error_data else "Request error."
        errors = None
    else:
        message = str(error_data)
        errors = None

    payload = {"success": False, "message": message}
    if errors:
        payload["errors"] = errors

    response.data = payload
    return response


def _flatten_errors(error_dict):
    """Convert DRF's nested error lists into clean { field: "first message" } dict."""
    flat = {}
    for field, messages in error_dict.items():
        if isinstance(messages, list) and messages:
            flat[field] = str(messages[0])
        elif isinstance(messages, dict):
            flat[field] = _flatten_errors(messages)
        else:
            flat[field] = str(messages)
    return flat
