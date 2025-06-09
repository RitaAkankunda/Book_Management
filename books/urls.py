from django.urls import path, include
from .views import (
    CategoryListCreateView, CategoryDetailView,
    AuthorListCreateView, AuthorDetailView,
    BookListCreateView, BookDetailView,
    books_by_category, books_by_author,
    low_stock_books, books_in_stock,
    update_book_stock
)

urlpatterns = [
    # Categories
    path('api/categories/', CategoryListCreateView.as_view()),
    path('api/categories/<int:pk>/', CategoryDetailView.as_view()),
    
    # Authors
    path('api/authors/', AuthorListCreateView.as_view()),
    path('api/authors/<int:pk>/', AuthorDetailView.as_view()),
    
    # Books
    path('api/books/', BookListCreateView.as_view()),
    path('api/books/<int:pk>/', BookDetailView.as_view()),
    
    # Custom endpoints
    path('api/books/category/<int:category_id>/', books_by_category),
    path('api/books/author/<int:author_id>/', books_by_author),
    path('api/books/low-stock/', low_stock_books),
    path('api/books/in-stock/', books_in_stock),
    path('api/books/<int:book_id>/update-stock/', update_book_stock),
]