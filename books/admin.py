# books/admin.py

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.db import transaction
from .models import Category, Author, Book


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Enhanced admin for Category - makes it easier to manage categories"""
    list_display = ['name', 'description', 'created_at', 'book_count']
    search_fields = ['name']
    ordering = ['name']
    actions = ['delete_selected']

    def book_count(self, obj):
        """Show number of books in this category"""
        return obj.books.count()
    book_count.short_description = 'Books'

    def has_delete_permission(self, request, obj=None):
        """Check if category can be deleted"""
        if obj is not None:
            return obj.books.count() == 0
        return True
    
    def delete_model(self, request, obj):
        """Handle deletion of a single category"""
        if obj.books.exists():
            self.message_user(request, 
                f"Cannot delete category '{obj.name}' because it has {obj.books.count()} books associated with it.", 
                level='ERROR')
            return
        obj.delete()

    def delete_selected(self, request, queryset):
        """Custom action to handle bulk deletion"""
        deletable = []
        undeletable = []
        
        for obj in queryset:
            if obj.books.exists():
                undeletable.append(obj)
            else:
                deletable.append(obj)
        
        # Delete categories that can be deleted
        Category.objects.filter(id__in=[obj.id for obj in deletable]).delete()
        
        # Show message about categories that couldn't be deleted
        if undeletable:
            categories = ", ".join([f"'{obj.name}'" for obj in undeletable])
            self.message_user(request, 
                f"Could not delete the following categories because they have books: {categories}", 
                level='ERROR')
        
        if deletable:
            self.message_user(request, 
                f"Successfully deleted {len(deletable)} categories.", 
                level='SUCCESS')
    delete_selected.short_description = "Delete selected categories"


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
    actions = ['delete_selected']  # Override default delete_selected
    
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

    def delete_model(self, request, obj):
        """Handle deletion of a single book"""
        obj.delete()

    def delete_selected(self, request, queryset):
        """Custom action to handle bulk deletion"""
        Book.bulk_delete(queryset)
    delete_selected.short_description = "Delete selected books"