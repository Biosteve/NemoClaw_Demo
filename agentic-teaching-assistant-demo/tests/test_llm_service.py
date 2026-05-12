"""
Tests for LLM service module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from llm import create_llm, get_available_use_cases, get_available_models, USE_CASES, MODELS
from llm import NVIDIA_API_BASE_URL, INFERENCE_BASE_URL


def test_get_available_use_cases():
    """Test that available use cases are returned correctly."""
    use_cases = get_available_use_cases()
    
    assert isinstance(use_cases, list)
    assert "study_material_generation" in use_cases
    assert "chapter_title_generation" in use_cases
    assert "subtopic_title_generation" in use_cases
    assert "extract_sub_chapters" in use_cases
    assert "curriculum_modification" in use_cases
    assert "document_search_rerank" in use_cases


def test_get_available_models():
    """Test that available models are returned correctly."""
    models = get_available_models()
    
    assert isinstance(models, list)
    assert "fast" in models
    assert "powerful" in models
    assert "reasoning" in models
    assert "astra" in models
    assert "gpt_5_nano" in models


def test_use_case_configurations():
    """Test that use case configurations are properly defined."""
    for use_case, config in USE_CASES.items():
        assert len(config) == 4, f"{use_case} should have 4 config values"
        model_alias, temp, top_p, max_tokens = config
        
        assert model_alias in MODELS, \
            f"{use_case} references unknown model: {model_alias}"
        assert 0.0 <= temp <= 1.0, f"{use_case} has invalid temperature: {temp}"
        assert 0.0 <= top_p <= 1.0, f"{use_case} has invalid top_p: {top_p}"
        assert max_tokens > 0, f"{use_case} has invalid max_tokens: {max_tokens}"


def test_model_configurations():
    """Test that model configurations are properly defined."""
    for model_alias, config in MODELS.items():
        assert len(config) == 3, f"{model_alias} should have 3 config values"
        model_name, api_key_env, base_url = config
        
        assert isinstance(model_name, str), f"{model_alias} has invalid model_name"
        assert api_key_env in ["NVIDIA_API_KEY", "INFERENCE_API_KEY"], \
            f"{model_alias} has unknown api_key_env: {api_key_env}"
        assert base_url is None or isinstance(base_url, str), \
            f"{model_alias} has invalid base_url: {base_url}"


@patch('llm.ChatNVIDIA')
def test_create_llm_with_use_case(mock_chat_nvidia, mock_env_vars):
    """Test create_llm with a use case name."""
    mock_chat_nvidia.return_value = MagicMock()
    
    llm = create_llm("study_material_generation")
    
    mock_chat_nvidia.assert_called_once()
    call_kwargs = mock_chat_nvidia.call_args[1]
    
    assert call_kwargs["model"] == "openai/openai/gpt-5-nano"
    assert call_kwargs["temperature"] == 0.6
    assert call_kwargs["max_tokens"] == 65000


@patch('llm.ChatNVIDIA')
def test_create_llm_with_model_alias(mock_chat_nvidia, mock_env_vars):
    """Test create_llm with a model alias."""
    mock_chat_nvidia.return_value = MagicMock()
    
    llm = create_llm("fast")
    
    mock_chat_nvidia.assert_called_once()
    call_kwargs = mock_chat_nvidia.call_args[1]
    
    assert call_kwargs["model"] == "openai/gpt-oss-120b"
    assert call_kwargs["temperature"] == 0.7
    assert call_kwargs["max_tokens"] == 4096


@patch('llm.ChatNVIDIA')
def test_create_llm_with_overrides(mock_chat_nvidia, mock_env_vars):
    """Test create_llm with parameter overrides."""
    mock_chat_nvidia.return_value = MagicMock()
    
    llm = create_llm("chapter_title_generation", temperature=0.9, max_tokens=2000)
    
    call_kwargs = mock_chat_nvidia.call_args[1]
    
    assert call_kwargs["temperature"] == 0.9
    assert call_kwargs["max_tokens"] == 2000


@patch('llm.ChatNVIDIA')
def test_create_llm_astra_uses_inference_hub(mock_chat_nvidia):
    """Test create_llm for 'astra' alias routes to Inference Hub."""
    mock_chat_nvidia.return_value = MagicMock()
    
    create_llm("astra")
    
    call_kwargs = mock_chat_nvidia.call_args[1]
    
    assert call_kwargs["base_url"] == INFERENCE_BASE_URL
    assert "inference.nvidia.com" in call_kwargs["base_url"]


@patch('llm.ChatNVIDIA')
def test_create_llm_nvidia_catalog_no_base_url(mock_chat_nvidia):
    """Test that NVIDIA API Catalog models use default (no explicit base_url)."""
    mock_chat_nvidia.return_value = MagicMock()
    
    create_llm("fast")
    
    call_kwargs = mock_chat_nvidia.call_args[1]
    assert "base_url" not in call_kwargs


@patch('llm.ChatNVIDIA')
def test_create_llm_with_direct_model_name(mock_chat_nvidia, mock_env_vars):
    """Test create_llm with a direct model name (not alias)."""
    mock_chat_nvidia.return_value = MagicMock()
    
    llm = create_llm("some/custom-model")
    
    call_kwargs = mock_chat_nvidia.call_args[1]
    
    assert call_kwargs["model"] == "some/custom-model"
    assert call_kwargs["base_url"] == INFERENCE_BASE_URL


def test_use_cases_match_original_config():
    """Test that use cases match the original llm_config.yaml structure."""
    expected_use_cases = [
        "chapter_title_generation",
        "subtopic_title_generation", 
        "curriculum_modification",
        "extract_sub_chapters",
        "study_material_generation",
        "document_search_rerank",
        "query_decomposition",
    ]
    
    for use_case in expected_use_cases:
        assert use_case in USE_CASES, f"Missing use case: {use_case}"
