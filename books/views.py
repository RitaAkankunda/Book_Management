# books/views.py

from rest_framework import generics, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Author, Book
from .serializers import (
    CategorySerializer, 
    AuthorSerializer, 
    BookListSerializer, 
    BookSerializer
)


# Category Views
class CategoryListCreateView(generics.ListCreateAPIView):
    """
    GET: List all categories
    POST: Create a new category
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific category
    PUT/PATCH: Update a category
    DELETE: Delete a category
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# Author Views
class AuthorListCreateView(generics.ListCreateAPIView):
    """
    GET: List all authors
    POST: Create a new author
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['first_name', 'last_name', 'created_at']
    ordering = ['last_name']  # Default ordering


class AuthorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific author
    PUT/PATCH: Update an author
    DELETE: Delete an author
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


# Book Views
class BookListCreateView(generics.ListCreateAPIView):
    """
    GET: List all books (uses simple serializer for performance)
    POST: Create a new book
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Book.objects.select_related('category').prefetch_related('authors')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'authors__first_name', 'authors__last_name']
    filterset_fields = ['category', 'authors']
    ordering_fields = ['title', 'price', 'created_at']
    ordering = ['-created_at']  # Newest first
    
    def get_serializer_class(self):
        """
        Use different serializers for different actions:
        - List: Simple serializer (faster)
        - Create: Detailed serializer (handles relationships)
        """
        if self.request.method == 'POST':
            return BookSerializer
        return BookListSerializer
    
    def perform_create(self, serializer):
        """Set the current user as the creator when creating a book"""
        serializer.save(created_by=self.request.user)


class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific book with full details
    PUT/PATCH: Update a book
    DELETE: Delete a book
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Book.objects.select_related('category', 'created_by').prefetch_related('authors')
    serializer_class = BookSerializer


# Custom API Views (using function-based views for specific functionality)

@api_view(['GET'])
@permission_classes([AllowAny])
def books_by_category(request, category_id):
    """
    Get all books in a specific category
    URL: /api/books/category/{category_id}/
    """
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response(
            {'error': 'Category not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    books = Book.objects.filter(category=category).select_related('category').prefetch_related('authors')
    serializer = BookListSerializer(books, many=True)
    
    return Response({
        'category': CategorySerializer(category).data,
        'books': serializer.data,
        'count': books.count()
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def books_by_author(request, author_id):
    """
    Get all books by a specific author
    URL: /api/books/author/{author_id}/
    """
    try:
        author = Author.objects.get(id=author_id)
    except Author.DoesNotExist:
        return Response(
            {'error': 'Author not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    books = Book.objects.filter(authors=author).select_related('category').prefetch_related('authors')
    serializer = BookListSerializer(books, many=True)
    
    return Response({
        'author': AuthorSerializer(author).data,
        'books': serializer.data,
        'count': books.count()
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def low_stock_books(request):
    """
    Get all books with low stock (5 or fewer copies)
    URL: /api/books/low-stock/
    """
    books = Book.objects.filter(stock_quantity__lte=5).select_related('category').prefetch_related('authors')
    serializer = BookListSerializer(books, many=True)
    return Response({
        'books': serializer.data,
        'count': books.count()
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def books_in_stock(request):
    """
    Get all books currently in stock (stock_quantity > 0)
    URL: /api/books/in-stock/
    """
    books = Book.objects.filter(stock_quantity__gt=0).select_related('category').prefetch_related('authors')
    serializer = BookListSerializer(books, many=True)
    return Response({
        'books': serializer.data,
        'count': books.count()
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticatedOrReadOnly])
def update_book_stock(request, book_id):
    """
    Update the stock quantity of a book
    URL: /api/books/{book_id}/update-stock/
    """
    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        return Response(
            {'error': 'Book not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    new_quantity = request.data.get('stock_quantity')
    if new_quantity is None:
        return Response(
            {'error': 'stock_quantity is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        new_quantity = int(new_quantity)
        if new_quantity < 0:
            raise ValueError()
    except ValueError:
        return Response(
            {'error': 'stock_quantity must be a non-negative integer'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    book.stock_quantity = new_quantity
    book.save()
    
    return Response(BookSerializer(book).data)