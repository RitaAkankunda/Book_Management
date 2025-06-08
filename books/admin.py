# books/admin.py

from django.contrib import admin
from .models import Category, Author, Book


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Enhanced admin for Category - makes it easier to manage categories"""
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Enhanced admin for Author - better display and search"""
    list_display = ['get_full_name', 'email', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']
    list_filter = ['created_at']
    ordering = ['last_name', 'first_name']
    
    def get_full_name(self, obj):
        """Show full name in the list instead of separate first/last"""
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Name'


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Enhanced admin for Book - the most important one"""
    list_display = ['title', 'category', 'price', 'stock_quantity', 'get_stock_status']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'isbn']
    filter_horizontal = ['authors']  # Better widget for selecting multiple authors
    ordering = ['-created_at']
    
    def get_stock_status(self, obj):
        """Show if book is in stock with green/red indicator"""
        return obj.stock_quantity > 0
    get_stock_status.boolean = True  # Shows as ✓ or ✗
    get_stock_status.short_description = 'In Stock'
    
    def save_model(self, request, obj, form, change):
        """Automatically set created_by to current user when adding new book"""
        if not change:  # Only when creating new book
            obj.created_by = request.user
        super().save_model(request, obj, form, change)