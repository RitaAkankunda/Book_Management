# core/exceptions.py - Custom error handling

from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the error for debugging
        logger.error(f"API Error: {exc} - Context: {context}")
        
        # Get the view and request info
        view = context.get('view')
        request = context.get('request')
        
        # Create custom error response format
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data,
            'status_code': response.status_code,
        }
        
        # Customize message based on error type
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response_data['message'] = 'Invalid data provided'
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            custom_response_data['message'] = 'Authentication required'
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            custom_response_data['message'] = 'Permission denied'
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            custom_response_data['message'] = 'Resource not found'
        elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            custom_response_data['message'] = 'Method not allowed'
        elif response.status_code >= 500:
            custom_response_data['message'] = 'Server error occurred'
        
        # Add request information for debugging (only in development)
        if hasattr(request, 'user') and request.user.is_staff:
            custom_response_data['debug_info'] = {
                'view': view.__class__.__name__ if view else None,
                'method': request.method if request else None,
                'path': request.path if request else None,
            }
        
        response.data = custom_response_data
    
    return response


# Custom validation helpers
def validate_positive_number(value, field_name):
    """Reusable validator for positive numbers"""
    if value <= 0:
        raise ValueError(f"{field_name} must be a positive number")
    return value

def validate_required_string(value, field_name, min_length=1):
    """Reusable validator for required strings"""
    if not value or len(value.strip()) < min_length:
        raise ValueError(f"{field_name} is required and must be at least {min_length} characters")
    return value.strip()