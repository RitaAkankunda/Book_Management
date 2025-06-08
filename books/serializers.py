# books/serializers.py

from rest_framework import serializers
from .models import Category, Author, Book


class CategorySerializer(serializers.ModelSerializer):  
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        return Category.objects.create(**validated_data)


class AuthorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Author
        fields = ['id', 'first_name', 'last_name', 'full_name', 'email', 
                 'bio', 'birth_date', 'created_at']
        read_only_fields = ['created_at']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class BookSerializer(serializers.ModelSerializer):
    # Nested serializers for readable output
    category_detail = CategorySerializer(source='category', read_only=True)
    authors_detail = AuthorSerializer(source='authors', many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    # Simple fields for write operations
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True)
    authors = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), many=True, write_only=True)
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'isbn', 'description', 'price', 'stock_quantity',
            'publication_date', 'pages', 'condition', 'rating', 'is_active',
            'created_at', 'updated_at',
            # Read-only nested fields
            'category_detail', 'authors_detail', 'created_by_name',
            # Write-only simple fields
            'category', 'authors'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']

    def create(self, validated_data):
        """Create book with many-to-many relationships"""
        authors_data = validated_data.pop('authors')
        book = Book.objects.create(**validated_data)
        book.authors.set(authors_data)
        return book

    def update(self, instance, validated_data):
        """Update book including many-to-many relationships"""
        authors_data = validated_data.pop('authors', None)
        
        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update many-to-many relationships
        if authors_data is not None:
            instance.authors.set(authors_data)
        
        return instance


class BookListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for book lists (better performance)
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    authors_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = ['id', 'title', 'category_name', 'price', 'stock_quantity', 'authors_count']
    
    def get_authors_count(self, obj):
        """Return number of authors for this book"""
        return obj.authors.count()