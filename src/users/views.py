from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    ChangePasswordSerializer,
)
from apps.core.utils import success_response, error_response


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """User Registration"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return success_response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, message='User registered successfully', status_code=status.HTTP_201_CREATED)
    return error_response(message='Registration failed', errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """User Login"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return error_response(message='Email and password are required', status_code=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(request, username=email, password=password)
    
    if user is None:
        return error_response(message='Invalid credentials', status_code=status.HTTP_401_UNAUTHORIZED)
    
    refresh = RefreshToken.for_user(user)
    return success_response({
        'user': UserSerializer(user).data,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, message='Login successful')


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Get or Update User Profile"""
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return success_response(data=serializer.data, message='Profile retrieved successfully')
    
    elif request.method == 'PUT':
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message='Profile updated successfully')
        return error_response(message='Update failed', errors=serializer.errors)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change User Password"""
    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return error_response(message='Old password is incorrect', status_code=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return success_response(message='Password changed successfully')
    return error_response(message='Password change failed', errors=serializer.errors)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """User Logout (Blacklist refresh token)"""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return success_response(message='Logged out successfully')
    except Exception as e:
        return error_response(message='Logout failed', status_code=status.HTTP_400_BAD_REQUEST)
