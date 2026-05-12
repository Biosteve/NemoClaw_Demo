"""
Pytest configuration and fixtures for AgenticTA tests.
"""
import pytest
import asyncio
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Configure pytest for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("NVIDIA_API_KEY", "test-nvidia-key")
    monkeypatch.setenv("INFERENCE_API_KEY", "test-inference-key")
    monkeypatch.setenv("ASTRA_TOKEN", "test-astra-token")
    monkeypatch.setenv("AI_WORKBENCH", "true")


@pytest.fixture
def temp_pdf_dir(tmp_path):
    """Create a temporary PDF directory."""
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    return pdf_dir


@pytest.fixture
def temp_mnt_dir(tmp_path):
    """Create a temporary mnt directory."""
    mnt_dir = tmp_path / "mnt"
    mnt_dir.mkdir()
    return mnt_dir


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return "This is a test response from the LLM."


@pytest.fixture
def mock_user():
    """Create a mock user object."""
    return {
        "user_id": "test_user_123",
        "study_buddy_preference": "patient and funny",
        "study_buddy_name": "TestBuddy",
        "study_buddy_persona": None,
    }


@pytest.fixture
def mock_chapter():
    """Create a mock chapter object."""
    return {
        "chapter_name": "Test Chapter",
        "subject": "Test Subject",
        "pdf_loc": "/test/path.pdf",
        "sub_topics": [],
        "status": "STARTED",
    }

