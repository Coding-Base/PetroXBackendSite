from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Handle Google auth errors specifically
    if response is not None:
        if response.status_code == 400 and 'detail' in response.data:
            return Response(
                {'error': response.data['detail']},
                status=response.status_code
            )
    
    return response