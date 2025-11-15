"""
Custom exceptions for Sha8alny platform.

This module defines all custom exceptions used across the application,
following the coding standards for proper error handling.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


class Sha8alnyException(Exception):
    """Base exception for all Sha8alny platform errors."""

    def __init__(self, message="An error occurred", code="error"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AIServiceError(Sha8alnyException):
    """Raised when AI service (LLM, vector DB, etc.) fails."""

    def __init__(self, message="AI service encountered an error", details=None):
        self.details = details
        super().__init__(message, code="ai_service_error")


class InsufficientDataError(Sha8alnyException):
    """Raised when insufficient data is available for an operation."""

    def __init__(self, message="Insufficient data to complete this operation"):
        super().__init__(message, code="insufficient_data")


class AssessmentProcessingError(Sha8alnyException):
    """Raised when assessment processing fails."""

    def __init__(self, message="Assessment processing failed"):
        super().__init__(message, code="assessment_processing_error")


class RoadmapGenerationError(Sha8alnyException):
    """Raised when roadmap generation fails."""

    def __init__(self, message="Roadmap generation failed"):
        super().__init__(message, code="roadmap_generation_error")


class ExternalAPIError(Sha8alnyException):
    """Raised when external API call fails (courses, jobs, etc.)."""

    def __init__(self, message="External API request failed", api_name=None):
        self.api_name = api_name
        super().__init__(message, code="external_api_error")


class ScrapingError(Sha8alnyException):
    """Raised when web scraping fails."""

    def __init__(self, message="Web scraping failed", url=None):
        self.url = url
        super().__init__(message, code="scraping_error")


class InvalidAssessmentError(Sha8alnyException):
    """Raised when assessment data is invalid."""

    def __init__(self, message="Invalid assessment data"):
        super().__init__(message, code="invalid_assessment")


class RoadmapNotFoundError(Sha8alnyException):
    """Raised when roadmap is not found."""

    def __init__(self, message="Roadmap not found"):
        super().__init__(message, code="roadmap_not_found")


class UnauthorizedActionError(Sha8alnyException):
    """Raised when user attempts unauthorized action."""

    def __init__(self, message="You are not authorized to perform this action"):
        super().__init__(message, code="unauthorized_action")


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses.

    Formats all exceptions into a standardized response format:
    {
        "error": true,
        "code": "error_code",
        "message": "Error message",
        "details": {...}
    }

    Args:
        exc: The exception instance
        context: The context in which the exception occurred

    Returns:
        Response: Formatted error response
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Handle DRF exceptions
    if response is not None:
        error_data = {
            'error': True,
            'code': 'validation_error' if response.status_code == 400 else 'error',
            'message': str(exc),
            'details': response.data
        }
        response.data = error_data
        return response

    # Handle custom Sha8alny exceptions
    if isinstance(exc, Sha8alnyException):
        error_data = {
            'error': True,
            'code': exc.code,
            'message': exc.message,
        }

        # Add additional details if available
        if hasattr(exc, 'details') and exc.details:
            error_data['details'] = exc.details
        if hasattr(exc, 'api_name') and exc.api_name:
            error_data['api_name'] = exc.api_name
        if hasattr(exc, 'url') and exc.url:
            error_data['url'] = exc.url

        return Response(
            error_data,
            status=status.HTTP_400_BAD_REQUEST
        )

    # Handle generic Python exceptions
    error_data = {
        'error': True,
        'code': 'internal_server_error',
        'message': 'An unexpected error occurred',
        'details': {
            'exception_type': type(exc).__name__,
            'exception_message': str(exc)
        }
    }

    return Response(
        error_data,
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
