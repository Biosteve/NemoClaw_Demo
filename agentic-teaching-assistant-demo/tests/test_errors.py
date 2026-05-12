"""
Tests for custom error classes and error handling.
"""
import pytest
from errors import (
    LLMAPIError,
    LLMRateLimitError,
    RAGConnectionError,
    DocumentProcessingError,
    get_user_friendly_message
)


def test_llm_api_error():
    """Test LLMAPIError creation and attributes."""
    error = LLMAPIError("API call failed", provider="nvidia", status_code=500)
    
    assert str(error) == "API call failed"
    assert error.provider == "nvidia"
    assert error.status_code == 500


def test_llm_rate_limit_error():
    """Test LLMRateLimitError with retry_after."""
    error = LLMRateLimitError("Rate limit exceeded", retry_after=60)
    
    assert str(error) == "Rate limit exceeded"
    assert error.retry_after == 60


def test_rag_connection_error():
    """Test RAGConnectionError with server_url."""
    error = RAGConnectionError("Cannot connect", server_url="http://localhost:8081")
    
    assert "Cannot connect" in str(error)
    assert error.server_url == "http://localhost:8081"


def test_document_processing_error():
    """Test DocumentProcessingError with pdf details."""
    error = DocumentProcessingError(
        "Failed to process PDF",
        pdf_path="/path/to/doc.pdf",
        page_number=5
    )
    
    assert error.pdf_path == "/path/to/doc.pdf"
    assert error.page_number == 5


def test_get_user_friendly_message_llm_error():
    """Test user-friendly message for LLM errors."""
    error = LLMAPIError("Connection timeout", provider="nvidia")
    message = get_user_friendly_message(error)
    
    assert "AI Service Issue" in message
    assert "temporarily unavailable" in message.lower()


def test_get_user_friendly_message_rate_limit():
    """Test user-friendly message for rate limit errors."""
    error = LLMRateLimitError("Too many requests", retry_after=30)
    message = get_user_friendly_message(error)
    
    assert "Rate Limit" in message
    assert "30" in message


def test_get_user_friendly_message_rag_error():
    """Test user-friendly message for RAG errors."""
    error = RAGConnectionError("Connection failed", server_url="http://rag-server:8081")
    message = get_user_friendly_message(error)
    
    assert "Connection Issue" in message
    assert "rag-server" in message.lower()


def test_get_user_friendly_message_document_error():
    """Test user-friendly message for document errors."""
    error = DocumentProcessingError("Parse error", pdf_path="document.pdf")
    message = get_user_friendly_message(error)
    
    assert "PDF Processing Error" in message
    assert "document.pdf" in message


def test_get_user_friendly_message_generic_error():
    """Test user-friendly message for generic errors."""
    error = ValueError("Some random error")
    message = get_user_friendly_message(error)
    
    assert "An Error Occurred" in message
    assert "Some random error" in message

