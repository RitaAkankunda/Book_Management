from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    Adds role-based access control and additional user fields
    """
    ROLES = [
        ('ADMIN', 'Admin'),
        ('MODERATOR', 'Moderator'),
        ('USER', 'User')
    ]

    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=20, choices=ROLES, default='USER')
    bio = models.TextField(max_length=500, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    
    # Override the groups field with a custom related_name
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    
    # Override the user_permissions field with a custom related_name
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set',
        related_query_name='custom_user'
    )

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    @property
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'ADMIN'

    @property
    def is_moderator(self):
        """Check if user has moderator role"""
        return self.role == 'MODERATOR'