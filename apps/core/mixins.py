"""
Shared mixins for API views.
"""
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError

from .utils import success_response, error_response
from .exceptions import BusinessLogicError


class ActionValidationMixin:
    """
    Mixin for ViewSet actions: get_serializer + is_valid(raise_exception=True),
    then run fn(validated_data). Catches ValidationError -> error_response,
    BusinessLogicError -> error_response.
    """
    def _run_action_validated(self, request, run_fn, validation_message='Validation failed'):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except DRFValidationError:
            return error_response(
                message=validation_message,
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            return run_fn(serializer.validated_data)
        except BusinessLogicError as e:
            return error_response(message=str(e.detail), status_code=e.status_code)


class SuccessResponseListRetrieveMixin:
    """
    Mixin for List/Retrieve views that wrap response in success_response.

    Set on the view:
      list_success_message = "Items listed successfully"
      retrieve_success_message = "Item detail"

    If not set, defaults are "Listed successfully" / "Retrieved successfully".
    """
    list_success_message = "Listed successfully"
    retrieve_success_message = "Retrieved successfully"

    def list(self, request, *args, **kwargs) -> Response:
        response = super().list(request, *args, **kwargs)
        return success_response(
            data=response.data,
            message=getattr(self, "list_success_message", self.list_success_message),
        )

    def retrieve(self, request, *args, **kwargs) -> Response:
        response = super().retrieve(request, *args, **kwargs)
        return success_response(
            data=response.data,
            message=getattr(
                self, "retrieve_success_message", self.retrieve_success_message
            ),
        )
