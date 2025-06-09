from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that formats error responses consistently
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)

    if response is None:
        # If DRF's handler returns None, we handle the exception ourselves
        return Response({
            'success': False,
            'message': str(exc),
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Customize the response format
    error_response = {
        'success': False,
        'message': 'An error occurred',
        'errors': {}
    }

    if hasattr(response, 'data'):
        if isinstance(response.data, dict):
            for field, value in response.data.items():
                if isinstance(value, list):
                    error_response['errors'][field] = value[0]
                else:
                    error_response['errors'][field] = value
            
            # If we have validation errors, update the message
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                error_response['message'] = 'Validation error'
        else:
            error_response['message'] = response.data

    response.data = error_response
    return response