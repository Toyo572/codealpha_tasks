from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK, **kwargs):
    payload = {"success": True, "message": message, "data": data}
    payload.update(kwargs)
    return Response(payload, status=status_code)


def created_response(data=None, message="Created successfully"):
    return success_response(data=data, message=message, status_code=status.HTTP_201_CREATED)


def no_content_response(message="Deleted successfully"):
    return Response({"success": True, "message": message}, status=status.HTTP_200_OK)


def error_response(message="An error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    payload = {"success": False, "message": message}
    if errors is not None:
        payload["errors"] = errors
    return Response(payload, status=status_code)
