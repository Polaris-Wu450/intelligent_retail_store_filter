"""
Unified exception handler for Django REST Framework.

This handler processes all exceptions and returns consistent JSON responses.
It handles both our custom BaseAppException and DRF's built-in exceptions.
"""

import logging
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework import exceptions as drf_exceptions

from .exceptions import BaseAppException, WarningException

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent JSON responses.
    
    This handler processes exceptions in the following order:
    1. Our custom BaseAppException (ValidationError, BlockError, WarningException)
    2. DRF's built-in exceptions (ValidationError, etc.)
    3. Django's built-in exceptions (Http404, PermissionDenied)
    4. Unknown exceptions (returns 500)
    
    Args:
        exc: The exception instance
        context: Additional context (view, request, etc.)
    
    Returns:
        JsonResponse: Standardized error response
    """
    
    # Get the view and request from context
    view = context.get('view', None)
    request = context.get('request', None)
    
    # Log exception details
    if view:
        logger.error(
            f"Exception in {view.__class__.__name__}: {exc.__class__.__name__}: {str(exc)}",
            exc_info=True
        )
    else:
        logger.error(f"Exception: {exc.__class__.__name__}: {str(exc)}", exc_info=True)
    
    # ========================================================================
    # 1. Handle our custom BaseAppException
    # ========================================================================
    if isinstance(exc, BaseAppException):
        return handle_app_exception(exc)
    
    # ========================================================================
    # 2. Handle DRF's built-in exceptions
    # ========================================================================
    if isinstance(exc, drf_exceptions.ValidationError):
        return handle_drf_validation_error(exc)
    
    if isinstance(exc, drf_exceptions.APIException):
        return handle_drf_api_exception(exc)
    
    # ========================================================================
    # 3. Handle Django's built-in exceptions
    # ========================================================================
    if isinstance(exc, Http404):
        return JsonResponse({
            'type': 'not_found',
            'code': 'RESOURCE_NOT_FOUND',
            'message': 'The requested resource was not found',
        }, status=404)
    
    if isinstance(exc, PermissionDenied):
        return JsonResponse({
            'type': 'permission_denied',
            'code': 'PERMISSION_DENIED',
            'message': 'You do not have permission to perform this action',
        }, status=403)
    
    # ========================================================================
    # 4. Handle unknown exceptions (fallback to DRF's handler, then 500)
    # ========================================================================
    response = drf_exception_handler(exc, context)
    
    if response is not None:
        # DRF handled it, return its response
        return response
    
    # Unknown exception - return 500
    logger.critical(f"Unhandled exception: {exc.__class__.__name__}: {str(exc)}", exc_info=True)
    return JsonResponse({
        'type': 'internal_error',
        'code': 'INTERNAL_SERVER_ERROR',
        'message': 'An internal server error occurred',
        'detail': str(exc) if logger.isEnabledFor(logging.DEBUG) else None,
    }, status=500)


def handle_app_exception(exc):
    """
    Handle our custom BaseAppException.
    
    Special case: WarningException returns 200 with warnings field instead of error.
    
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
            'warnings': [data],  # Array of warnings
            'message': 'Operation completed with warnings',
        }
        return JsonResponse(response_data, status=200)
    
    # Regular error response
    return JsonResponse(data, status=status)


def handle_drf_validation_error(exc):
    """
    Handle DRF's ValidationError (from serializers).
    
    Convert it to our standard format.
    
    Args:
        exc: DRF ValidationError instance
    
    Returns:
        JsonResponse: Standardized validation error response
    """
    # DRF ValidationError.detail can be a list, dict, or string
    detail = exc.detail
    
    # Format the detail based on its type
    if isinstance(detail, dict):
        # Field-specific errors: {'field_name': ['error1', 'error2']}
        formatted_detail = {}
        for field, errors in detail.items():
            if isinstance(errors, list):
                formatted_detail[field] = [str(e) for e in errors]
            else:
                formatted_detail[field] = [str(errors)]
    elif isinstance(detail, list):
        # Non-field errors: ['error1', 'error2']
        formatted_detail = {'non_field_errors': [str(e) for e in detail]}
    else:
        # Single error message
        formatted_detail = {'non_field_errors': [str(detail)]}
    
    return JsonResponse({
        'type': 'validation_error',
        'code': 'VALIDATION_FAILED',
        'message': 'Input validation failed',
        'detail': formatted_detail,
    }, status=400)


def handle_drf_api_exception(exc):
    """
    Handle other DRF APIException subclasses.
    
    Examples: AuthenticationFailed, NotAuthenticated, PermissionDenied, etc.
    
    Args:
        exc: DRF APIException instance
    
    Returns:
        JsonResponse: Standardized error response
    """
    # Map common DRF exception types to our error types
    type_mapping = {
        'AuthenticationFailed': 'authentication_error',
        'NotAuthenticated': 'authentication_error',
        'PermissionDenied': 'permission_denied',
        'NotFound': 'not_found',
        'MethodNotAllowed': 'method_not_allowed',
        'NotAcceptable': 'not_acceptable',
        'UnsupportedMediaType': 'unsupported_media_type',
        'Throttled': 'throttled',
    }
    
    exc_class_name = exc.__class__.__name__
    error_type = type_mapping.get(exc_class_name, 'api_error')
    
    return JsonResponse({
        'type': error_type,
        'code': exc.default_code.upper() if hasattr(exc, 'default_code') else 'API_ERROR',
        'message': str(exc.detail),
    }, status=exc.status_code)


def plain_exception_handler(exc, context):
    """
    Exception handler for plain Django views (non-DRF views).
    
    Use this if you want consistent error handling in regular Django views
    that don't use DRF.
    
    Usage in views.py:
        @csrf_exempt
        def my_view(request):
            try:
                # your logic
            except Exception as e:
                return plain_exception_handler(e, {'view': my_view, 'request': request})
    """
    return custom_exception_handler(exc, context)
