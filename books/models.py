from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
class Author(models.Model):   
    first_name = models.CharField(max_length=100, help_text="Author's first name" )
    last_name = models.CharField(max_length=100, help_text="Author's last name")
    email = models.EmailField(unique=True, blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True, help_text="Brief biography of the author")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
         unique_together = ['first_name', 'last_name']    
         ordering = ['last_name', 'first_name']
         indexes = [models.Index(fields=['last_name', 'first_name'])]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"   

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
class Book(models.Model):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]        
    title = models.CharField(max_length=200, help_text="Title of the book")
    isbn = models.CharField(max_length=13, unique=True, help_text="13-digit ISBN number")
    authors = models.ManyToManyField(Author, related_name='books', help_text="Authors of this book")
    category = models.ForeignKey(Category,on_delete=models.CASCADE, related_name='books', help_text="Book category")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_books', help_text="User who added this book")
    description = models.TextField(help_text="Book description or summary")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Book price in USD")
    stock_quantity = models.PositiveIntegerField(default=0, help_text="Number of books in stock")
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='new', help_text="Physical condition of the book")
    publication_date = models.DateField(help_text="When the book was published")
    pages = models.PositiveIntegerField(help_text="Number of pages")
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="Average rating (0-5)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Whether this book is active/visible")

    class Meta:
        ordering = ['-created_at']  # Newest first 

         # Database indexes for common queries
        indexes = [
            models.Index(fields=['title']),       # Search by title
            models.Index(fields=['isbn']),        # Lookup by ISBN
            models.Index(fields=['category']),    # Filter by category
            models.Index(fields=['created_at']),  # Order by date
            models.Index(fields=['is_active']),   # Filter active books
        ]

    def __str__(self):
        return self.title   
    
    def get_authors_display(self): #Return comma-separated list of author names
        return ", ".join([author.full_name for author in self.authors.all()])
    
    def is_in_stock(self): #Check if book is available
        return self.stock_quantity > 0
    
    def get_price_display(self): #Format price nicely
        return f"${self.price:.2f}"