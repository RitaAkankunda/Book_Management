from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'authors', views.AuthorViewSet)
router.register(r'books', views.BookViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('api/', include(router.urls)),
]
