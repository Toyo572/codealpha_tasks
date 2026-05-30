from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated


class BaseAPIView(GenericAPIView):
    """
    Base view for the entire project.

    Rules enforced here:
    - Every subclass MUST declare `serializer_class`.
    - Default permission: IsAuthenticated (override per view as needed).
    - Pagination, filtering, and exception handling are wired via DRF settings
      so all views share the same behaviour automatically.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer(self, *args, **kwargs):
        if self.serializer_class is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define `serializer_class`."
            )
        return super().get_serializer(*args, **kwargs)
