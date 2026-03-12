"""
Exception handling middleware for Django views.

This middleware catches all exceptions raised in views and converts them
to consistent JSON responses using our exception handler.
"""

import logging
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.http import Http404

from .exceptions import BaseAppException, WarningException

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware:
    """
    Middleware that catches all exceptions and returns standardized JSON responses.
    
    Install this in settings.py MIDDLEWARE list.
    It should be placed near the beginning to catch exceptions from other middleware.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """Process the request normally"""
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """
        Called when a view raises an exception.
        
        Args:
            request: Django request object
            exception: The exception that was raised
        
        Returns:
            JsonResponse with standardized error format, or None to let Django handle it
        """
        
        # Log the exception
        logger.error(
            f"Exception in {request.path}: {exception.__class__.__name__}: {str(exception)}",
            exc_info=True
        )
        
        # ====================================================================
        # 1. Handle our custom BaseAppException
        # ====================================================================
        if isinstance(exception, BaseAppException):
            return self._handle_app_exception(exception)
        
        # ====================================================================
        # 2. Handle Django's built-in exceptions
        # ====================================================================
        if isinstance(exception, Http404):
            return JsonResponse({
                'type': 'not_found',
                'code': 'RESOURCE_NOT_FOUND',
                'message': 'The requested resource was not found',
            }, status=404)
        
        if isinstance(exception, PermissionDenied):
            return JsonResponse({
                'type': 'permission_denied',
                'code': 'PERMISSION_DENIED',
                'message': 'You do not have permission to perform this action',
            }, status=403)
        
        # ====================================================================
        # 3. Handle unknown exceptions (return 500)
        # ====================================================================
        logger.critical(
            f"Unhandled exception: {exception.__class__.__name__}: {str(exception)}",
            exc_info=True
        )
        
        return JsonResponse({
            'type': 'internal_error',
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'An internal server error occurred',
            'detail': str(exception) if logger.isEnabledFor(logging.DEBUG) else None,
        }, status=500)
    
    def _handle_app_exception(self, exc):
        """
        Handle our custom BaseAppException.
        
        Special case: WarningException returns 200 with warnings field.
        
        Args:
            exc: BaseAppException instance
        
        Returns:
            JsonResponse: Standardized response
        """
        data = exc.to_dict()
        status = exc.http_status
        
        # Special handling for WarningException
        # Warnings should return 200 OK but include warning information
        if isinstance(exc, WarningException):
            response_data = {
                'warnings': [data],  # Array of warnings for future extensibility
                'message': 'Operation completed with warnings',
            }
            return JsonResponse(response_data, status=200)
        
        # Regular error response
        return JsonResponse(data, status=status)
