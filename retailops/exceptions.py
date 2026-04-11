"""
Unified exception handling system for the application.

All business logic should raise subclasses of BaseAppException.
The exception_handler will convert them to consistent JSON responses.
"""


class BaseAppException(Exception):
    """
    Base exception class for all application-specific exceptions.
    
    Attributes:
        type: Error type identifier ('validation_error', 'block_error', 'warning')
        code: Specific error code (e.g., 'STORE_ID_CONFLICT')
        message: Human-readable error message
        detail: Additional context or details (optional)
        http_status: HTTP status code to return
    """
    
    # Default values (to be overridden by subclasses)
    default_type = 'error'
    default_code = 'UNKNOWN_ERROR'
    default_message = 'An unknown error occurred'
    default_status = 500
    
    def __init__(self, message=None, code=None, detail=None, status=None):
        """
        Initialize the exception.
        
        Args:
            message: Custom error message (uses default_message if not provided)
            code: Custom error code (uses default_code if not provided)
            detail: Additional details (dict or any serializable object)
            status: Custom HTTP status (uses default_status if not provided)
        """
        self.type = self.default_type
        self.code = code or self.default_code
        self.message = message or self.default_message
        self.detail = detail
        self.http_status = status or self.default_status
        
        # Call parent Exception constructor
        super().__init__(self.message)
    
    def to_dict(self):
        """
        Convert exception to dictionary for JSON response.
        
        Returns:
            dict: Exception data in standardized format
        """
        data = {
            'type': self.type,
            'code': self.code,
            'message': self.message,
        }
        
        if self.detail is not None:
            data['detail'] = self.detail
        
        return data


class ValidationError(BaseAppException):
    """
    Raised when user input fails validation.
    
    Examples:
        - Store ID doesn't match required format
        - Customer ID doesn't have the correct number of digits
        - Missing required fields
        - Invalid data types
    
    HTTP Status: 400 Bad Request
    """
    
    default_type = 'validation_error'
    default_code = 'VALIDATION_FAILED'
    default_message = 'Input validation failed'
    default_status = 400


class BlockError(BaseAppException):
    """
    Raised when business rules prevent the operation.
    
    Examples:
        - Store ID already exists with different name
        - Same customer + same category + same day feedback duplicate
        - Conflicting data that cannot be resolved
    
    HTTP Status: 409 Conflict
    """
    
    default_type = 'block_error'
    default_code = 'OPERATION_BLOCKED'
    default_message = 'Operation blocked by business rules'
    default_status = 409


class WarningException(BaseAppException):
    """
    Raised when there's a potential issue that requires user confirmation.
    
    This is NOT an error - the operation can succeed if user confirms.
    
    Examples:
        - Same customer + same category feedback on different day
        - Customer data conflicts that might be intentional
        - Suspicious but potentially valid operations
    
    HTTP Status: 200 OK (with warnings field)
    
    Note: This will be handled specially to return 200 instead of error status.
    """
    
    default_type = 'warning'
    default_code = 'CONFIRMATION_REQUIRED'
    default_message = 'Operation requires user confirmation'
    default_status = 200  # Special case: warnings return 200


# ============================================================================
# Specific Exception Classes (for better semantics and code clarity)
# ============================================================================

class StoreValidationError(ValidationError):
    """Store data validation failed"""
    default_code = 'STORE_VALIDATION_FAILED'
    default_message = 'Store data validation failed'


class CustomerValidationError(ValidationError):
    """Customer data validation failed"""
    default_code = 'CUSTOMER_VALIDATION_FAILED'
    default_message = 'Customer data validation failed'


class FeedbackValidationError(ValidationError):
    """Feedback data validation failed"""
    default_code = 'FEEDBACK_VALIDATION_FAILED'
    default_message = 'Feedback data validation failed'


class StoreConflictError(BlockError):
    """Store ID already exists with a different name — hard block."""
    default_code = 'STORE_ID_CONFLICT'
    default_message = 'Store ID already exists with different name'


class FeedbackDuplicateError(BlockError):
    """Same store + customer + category submitted twice on the same day."""
    default_code = 'FEEDBACK_DUPLICATE'
    default_message = 'Duplicate feedback detected for today'


class FeedbackWarning(WarningException):
    """Same store + customer + category submitted on a different day — requires confirmation."""
    default_code = 'FEEDBACK_ALREADY_EXISTS'
    default_message = 'Similar feedback already exists on a different day'
