# books/views.py

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Category, Author, Book
from .serializers import (
    CategorySerializer, 
    AuthorSerializer, 
    BookSerializer,
    BookListSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing categories
    Provides CRUD operations for categories
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def books(self, request, pk=None):
        """Get all books in this category"""
        category = self.get_object()
        books = Book.objects.filter(category=category)
        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)


class AuthorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing authors
    Provides CRUD operations for authors
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['first_name', 'last_name', 'created_at']
    ordering = ['last_name', 'first_name']

    @action(detail=True, methods=['get'])
    def books(self, request, pk=None):
        """Get all books by this author"""
        author = self.get_object()
        books = author.books.all()
        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing books
    Provides CRUD operations with advanced filtering
    """
    queryset = Book.objects.select_related('category', 'created_by').prefetch_related('authors')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'isbn', 'description']
    filterset_fields = ['category', 'authors']
    ordering_fields = ['title', 'price', 'publication_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializers for list vs detail views"""
        if self.action == 'list':
            return BookListSerializer
        return BookSerializer

    def get_permissions(self):
        """Require authentication for create/update/delete"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return []

    def perform_create(self, serializer):
        """Set the current user as the creator"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search across multiple fields"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'detail': 'No search query provided'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Search across multiple fields
        books = Book.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(isbn__icontains=query) |
            Q(authors__first_name__icontains=query) |
            Q(authors__last_name__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
        
        serializer = BookListSerializer(books, many=True)
        return Response({
            'count': books.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def in_stock(self, request):
        """Get only books that are in stock"""
        books = Book.objects.filter(stock_quantity__gt=0)
        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get books with low stock (less than 5)"""
        books = Book.objects.filter(stock_quantity__lt=5, stock_quantity__gt=0)
        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_stock(self, request, pk=None):
        """Add stock to a book"""
        book = self.get_object()
        quantity = request.data.get('quantity', 0)
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response({'detail': 'Quantity must be positive'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'detail': 'Invalid quantity'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        book.stock_quantity += quantity
        book.save()
        
        return Response({
            'detail': f'Added {quantity} units to stock',
            'new_stock': book.stock_quantity
        })

    @action(detail=True, methods=['post'])
    def remove_stock(self, request, pk=None):
        """Remove stock from a book"""
        book = self.get_object()
        quantity = request.data.get('quantity', 0)
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response({'detail': 'Quantity must be positive'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'detail': 'Invalid quantity'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if book.stock_quantity < quantity:
            return Response({'detail': 'Not enough stock available'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        book.stock_quantity -= quantity
        book.save()
        
        return Response({
            'detail': f'Removed {quantity} units from stock',
            'new_stock': book.stock_quantity
        })