"""
Custom exceptions for the application
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class CustomAPIException(APIException):
    """Custom API Exception"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'A server error occurred.'
    default_code = 'error'
    
    def __init__(self, detail=None, code=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail, code)


class APIValidationError(CustomAPIException):
    """
    API-level validation error. Use when returning 400 from views/serializers.
    For serializer field validation use rest_framework.serializers.ValidationError.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Validation error occurred.'


class NotFoundError(CustomAPIException):
    """Not Found Error"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found.'


class PermissionDeniedError(CustomAPIException):
    """Permission Denied Error"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Permission denied.'


class BusinessLogicError(CustomAPIException):
    """Business logic error for service layer"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Business logic error occurred.'
