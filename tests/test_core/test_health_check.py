"""
Tests for health check endpoint
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self, api_client):
        """Test health check endpoint"""
        response = api_client.get('/api/health/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'ok'
        assert 'message' in response.data
