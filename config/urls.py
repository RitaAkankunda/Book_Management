from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('books.urls')),  # Books API endpoints
    path('api/users/', include('users.urls')),  # User management endpoints
]