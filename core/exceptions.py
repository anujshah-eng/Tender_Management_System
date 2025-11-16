#core/exceptions.py
"""
Custom Exceptions for the application
"""

class TenderManagementException(Exception):
    """Base exception for the application"""
    pass


class DocumentNotFoundException(TenderManagementException):
    """Raised when a document is not found"""
    pass


class IngestionFailedException(TenderManagementException):
    """Raised when document ingestion fails"""
    pass


class EmbeddingGenerationException(TenderManagementException):
    """Raised when embedding generation fails"""
    pass


class DatabaseOperationException(TenderManagementException):
    """Raised when database operation fails"""
    pass


class InvalidRequestException(TenderManagementException):
    """Raised when request validation fails"""
    pass