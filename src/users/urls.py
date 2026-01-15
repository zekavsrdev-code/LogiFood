from django.urls import path
from .views import register, login, profile, change_password, logout

app_name = 'users'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('profile/', profile, name='profile'),
    path('change-password/', change_password, name='change-password'),
]
