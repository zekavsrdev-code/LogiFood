"""
Tests for core utilities
"""
import pytest
from rest_framework import status
from apps.core.utils import success_response, error_response


class TestResponseUtils:
    """Test response utility functions"""
    
    def test_success_response(self):
        """Test success response"""
        response = success_response(data={'key': 'value'}, message='Success')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['message'] == 'Success'
        assert response.data['data'] == {'key': 'value'}
    
    def test_error_response(self):
        """Test error response"""
        response = error_response(message='Error', errors={'field': ['Error message']})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert response.data['message'] == 'Error'
        assert 'errors' in response.data
