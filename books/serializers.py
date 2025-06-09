# books/serializers.py - Step by step validation examples

from rest_framework import serializers
from .models import Book, Category, Author
import re
from decimal import Decimal

# STEP 1: Basic field validation
class AuthorSerializer(serializers.ModelSerializer):
    # Add computed fields (read-only)
    full_name = serializers.SerializerMethodField()
    book_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Author
        fields = ['id', 'first_name', 'last_name', 'full_name', 'email', 'bio', 'book_count']
    
    # METHOD 1: Custom field validation
    def validate_first_name(self, value):
        """
        This method automatically validates the 'first_name' field
        Django calls this when validating first_name
        """        # Check if name contains only letters and spaces
        if not re.match(r"^[a-zA-Z\s]+$", value):
            raise serializers.ValidationError("First name should contain only letters and spaces.")
        
        # Check minimum length
        if len(value) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters long.")
        
        # Auto-capitalize (Title Case)
        return value.title()
    
    def validate_last_name(self, value):
        """
        This method automatically validates the 'last_name' field
        Django calls this when validating last_name
        """
        # Check if name contains only letters and spaces
        if not re.match(r"^[a-zA-Z\s]+$", value):
            raise serializers.ValidationError("Last name should contain only letters and spaces.")
        
        # Check minimum length
        if len(value) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters long.")
        
        # Auto-capitalize (Title Case)
        return value.title()
    
    def validate_email(self, value):
        """
        Check if email is unique among authors
        """
        if value:  # Only check if email is provided
            # Check if another author already has this email
            existing = Author.objects.filter(email=value)
            
            # If updating, exclude current instance
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise serializers.ValidationError("An author with this email already exists.")
        
        return value
    
    # METHOD 2: Computed fields (SerializerMethodField)
    def get_full_name(self, obj):
        """Returns the full name of the author"""
        return f"{obj.first_name} {obj.last_name}"
    
    def get_book_count(self, obj):
        """Returns how many books this author has written"""
        return obj.books.count()


# STEP 2: Category validation with slug auto-generation
class CategorySerializer(serializers.ModelSerializer):
    book_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'book_count', 'created_at']
        read_only_fields = ['slug', 'created_at']  # User can't set these directly
    
    def validate_name(self, value):
        """
        Validate category name with business rules
        """
        # Minimum length check
        if len(value) < 3:
            raise serializers.ValidationError("Category name must be at least 3 characters long.")
        
        # Check for uniqueness (case-insensitive)
        existing = Category.objects.filter(name__iexact=value)
        if self.instance:  # If updating
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise serializers.ValidationError("A category with this name already exists.")
        
        # Auto-capitalize each word
        return value.title()
    
    def get_book_count(self, obj):
        """Returns number of books in this category"""
        return obj.books.count()


# STEP 3: Complex book validation with multiple rules
class BookSerializer(serializers.ModelSerializer):
    # Include related object details in response
    authors_details = AuthorSerializer(source='authors', many=True, read_only=True)
    category_details = CategorySerializer(source='category', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    # Computed fields
    is_available = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'isbn', 'description', 'price', 'stock_quantity',
            'category', 'category_details', 'authors', 'authors_details',
            'created_by_username', 'is_available', 'stock_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def validate_title(self, value):
        """Validate book title"""
        if len(value) < 3:
            raise serializers.ValidationError("Book title must be at least 3 characters long.")
        
        # Check for duplicate titles (case-insensitive)
        existing = Book.objects.filter(title__iexact=value)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise serializers.ValidationError("A book with this title already exists.")
        
        return value.title()
    
    def validate_isbn(self, value):
        """Validate ISBN format and uniqueness"""
        if not value:
            return value

        # Remove any spaces or dashes
        clean_isbn = re.sub(r'[\s-]', '', value)
        
        # Check if it's 10 or 13 digits
        if not re.match(r'^\d{10}$|^\d{13}$', clean_isbn):
            raise serializers.ValidationError("ISBN must be 10 or 13 digits long.")
        
        # Check uniqueness
        existing = Book.objects.filter(isbn=clean_isbn)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise serializers.ValidationError("A book with this ISBN already exists.")
        
        return clean_isbn
    
    def validate_price(self, value):
        """Validate price is reasonable"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        
        if value > Decimal('10000.00'):
            raise serializers.ValidationError("Price cannot exceed $10,000.")
        
        return value
    
    def validate_stock_quantity(self, value):
        """Validate stock quantity"""
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative.")
        
        if value > 10000:
            raise serializers.ValidationError("Stock quantity cannot exceed 10,000.")
        
        return value
    
    def validate(self, data):
        """
        Cross-field validation
        """
        if 'authors' in data and not data['authors']:
            raise serializers.ValidationError({"authors": "At least one author is required."})
        
        if 'category' not in data:
            raise serializers.ValidationError({"category": "Category is required."})
            
        return data
    
    # Computed fields
    def get_is_available(self, obj):
        """Check if book is available in stock"""
        return obj.stock_quantity > 0
    
    def get_stock_status(self, obj):
        """Get human-readable stock status"""
        if obj.stock_quantity == 0:
            return "Out of Stock"
        elif obj.stock_quantity <= 5:
            return "Low Stock"
        else:
            return "In Stock"
        
class BookListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for book lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    author_names = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = ['id', 'title', 'isbn', 'price', 'stock_quantity', 'category_name', 'author_names', 'stock_status', 'condition']
    
    def get_author_names(self, obj):
        return [f"{author.first_name} {author.last_name}" for author in obj.authors.all()]
        
    def get_stock_status(self, obj):
        """Get human-readable stock status"""
        if obj.stock_quantity == 0:
            return "Out of Stock"
        elif obj.stock_quantity <= 5:
            return "Low Stock"
        else:
            return "In Stock"