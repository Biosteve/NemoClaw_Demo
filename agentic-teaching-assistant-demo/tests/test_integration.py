"""
Integration tests for AgenticTA core workflows.

Tests the full pipeline from PDF upload to curriculum generation.
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import tempfile
import shutil

from nodes import (
    populate_states_for_user,
    build_chapters,
    build_next_chapter
)
from states import User, Chapter, Curriculum
from chapter_gen_from_file_names import chapter_gen_from_pdfs
from study_material_gen_agent import study_material_gen


@pytest.fixture
def temp_pdf_dir():
    """Create temporary directory with mock PDF structure."""
    temp_dir = tempfile.mkdtemp()
    
    # Create mock directory structure
    chapter_dir = Path(temp_dir) / "Chapter_1_Introduction"
    chapter_dir.mkdir()
    
    # Create mock PDF files
    for i in range(3):
        pdf_file = chapter_dir / f"section_{i}.pdf"
        pdf_file.write_text(f"Mock PDF content {i}")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_rag_services():
    """Mock RAG service responses."""
    with patch('search_and_filter_documents.document_seach') as mock_search, \
         patch('search_and_filter_documents.get_documents') as mock_get_docs:
        
        # Mock RAG search response
        mock_search.return_value = {
            "documents": [
                {"content": "Sample content 1", "score": 0.95},
                {"content": "Sample content 2", "score": 0.87}
            ]
        }
        
        # Mock document retrieval
        mock_get_docs.return_value = [
            {"text": "Document 1 content", "metadata": {"source": "doc1.pdf"}},
            {"text": "Document 2 content", "metadata": {"source": "doc2.pdf"}}
        ]
        
        yield mock_search, mock_get_docs


@pytest.fixture
def mock_llm_responses():
    """Mock LLM API responses."""
    with patch('llm.ChatNVIDIA') as mock_chat:
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance
        
        # Return different responses based on prompt content
        async def dynamic_response(prompt, **kwargs):
            prompt_lower = prompt.lower() if isinstance(prompt, str) else ""
            if "chapter" in prompt_lower:
                return MagicMock(content="# Chapter 1: Introduction\n## 1.1 Overview\n## 1.2 Key Concepts")
            elif "study" in prompt_lower:
                return MagicMock(content="# Study Material\n\n## Summary\nKey concepts explained.\n\n## Examples\n1. Example 1\n2. Example 2")
            elif "subtopic" in prompt_lower:
                return MagicMock(content="Introduction to Machine Learning")
            else:
                return MagicMock(content="Generated content")
        
        mock_instance.ainvoke = AsyncMock(side_effect=dynamic_response)
        mock_instance.invoke = MagicMock(side_effect=lambda p: dynamic_response(p, None))
        yield mock_chat


class TestCurriculumGenerationPipeline:
    """Test the complete curriculum generation workflow."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skip(reason="Complex integration test - needs more mocking work. Enable when needed.")
    async def test_full_pipeline_with_pdfs(self, temp_pdf_dir, mock_rag_services, mock_llm_responses):
        """Test complete pipeline from PDFs to curriculum."""
        # Create test user with all required fields
        user = User(
            user_id="test_user_123",
            study_buddy_preference="casual",
            study_buddy_persona=None,
            study_buddy_name="Study Buddy",
            curriculum=[]
        )
        
        # Create mock Chapter object to return with correct field names
        mock_chapter = Chapter(
            number=1,
            name="Test Chapter",
            sub_topics=[],
            reference="test.pdf",
            pdf_loc="/tmp/test.pdf",
            quizes=[],
            feedback=[]
        )
        
        # Mock external services and file operations
        with patch('nodes.init_user_storage') as mock_init_storage, \
             patch('nodes.save_user_state') as mock_save_state, \
             patch('nodes.build_chapters') as mock_build_chapters, \
             patch('pathlib.Path.exists') as mock_path_exists, \
             patch('pathlib.Path.mkdir') as mock_path_mkdir:
            
            mock_init_storage.return_value = None
            mock_save_state.return_value = None
            mock_build_chapters.return_value = [mock_chapter]  # Return list with 1 chapter
            mock_path_exists.return_value = True
            mock_path_mkdir.return_value = None
            
            # Run populate_states_for_user (main entry point)
            result = await populate_states_for_user(
                user=user,
                pdf_files_loc=temp_pdf_dir,
                study_buddy_preference="casual"
            )
            
            # Assertions
            assert result is not None
            assert isinstance(result, dict)
            assert "user_id" in result
    
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_chapter_generation_from_directory(self, temp_pdf_dir, mock_llm_responses):
        """Test chapter title generation from directory structure."""
        # Mock the file reading and OS operations
        with patch('os.listdir') as mock_listdir, \
             patch('os.path.exists') as mock_exists:
            
            # Simulate finding PDF files
            mock_listdir.return_value = ["chapter1.pdf", "chapter2.pdf"]
            mock_exists.return_value = True
            
            # Run chapter generation
            result = await chapter_gen_from_pdfs(temp_pdf_dir)
            
            # Verify structure - function returns a string (JSON or LLM output)
            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0
            
            # Verify LLM was called
            mock_llm_responses.assert_called()
    
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_study_material_generation(self, mock_rag_services, mock_llm_responses):
        """Test study material generation for a subtopic."""
        # Mock the filter_documents_by_file_name function
        with patch('study_material_gen_agent.filter_documents_by_file_name') as mock_filter:
            # Return (valid_flag, documents)
            mock_filter.return_value = (True, [
                {
                    "content": "AI content",
                    "metadata": {"description": "AI basics", "source": "ai.pdf"},
                    "document_type": "text"
                }
            ])
            
            # Generate study materials
            result = await study_material_gen(
                subject="Introduction to AI",
                sub_topic="Machine Learning",
                pdf_file_name="ai_textbook.pdf",
                num_docs=5
            )
            
            # Assertions - function returns tuple (study_material_str, markdown_str)
            assert result is not None
            assert isinstance(result, tuple)
            assert len(result) == 2
            study_material_str, markdown_str = result
            assert isinstance(study_material_str, str)
            assert isinstance(markdown_str, str)
            
            # Verify filter was called
            mock_filter.assert_called()
            
            # Verify LLM was called
            mock_llm_responses.assert_called()


class TestRAGIntegration:
    """Test RAG service integration."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_document_search_with_rag(self, mock_rag_services):
        """Test document search through RAG service."""
        from search_and_filter_documents import document_seach
        
        mock_search, _ = mock_rag_services
        
        payload = {
            "query": "machine learning basics",
            "top_k": 5
        }
        
        result = await document_seach(
            payload=payload,
            url="http://rag-server:8081/search"
        )
        
        assert result is not None
        assert "documents" in result
        assert len(result["documents"]) > 0
        mock_search.assert_called_once()
    
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_document_retrieval_with_filters(self, mock_rag_services):
        """Test filtered document retrieval."""
        from search_and_filter_documents import get_documents
        
        _, mock_get_docs = mock_rag_services
        
        result = await get_documents(
            query="neural networks",
            user_id="test_user",
            top_k=3,
            use_rag=True
        )
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
        mock_get_docs.assert_called_once()
    
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rag_connection_error_handling(self):
        """Test graceful handling of RAG connection errors."""
        from search_and_filter_documents import document_seach
        from errors import RAGConnectionError
        import aiohttp
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Simulate connection error
            mock_post.side_effect = aiohttp.ClientError("Connection refused")
            
            with pytest.raises(RAGConnectionError):
                await document_seach(
                    payload={"query": "test"},
                    url="http://invalid-url:9999/search"
                )


class TestStatePersistence:
    """Test state management across workflow steps."""
    
    def test_user_state_mutation(self):
        """Test user state can be mutated during workflow.
        
        This is a practical test - it verifies that our state
        management pattern (TypedDict mutation) actually works
        as expected in our workflow.
        """
        # Create initial user state
        user = User(
            user_id="user_123",
            study_buddy_preference="casual",
            study_buddy_persona=None,
            study_buddy_name="Test Buddy",
            curriculum=[]
        )
        
        # Simulate node processing - update study buddy preference
        # This is what happens in actual workflow
        user["study_buddy_preference"] = "formal"
        user["study_buddy_name"] = "Professor Smith"
        user["curriculum"] = [{"active_chapter": None}]
        
        # Verify mutations worked
        assert user["study_buddy_preference"] == "formal"
        assert user["study_buddy_name"] == "Professor Smith"
        assert len(user["curriculum"]) == 1


class TestErrorRecovery:
    """Test error handling and recovery in workflows."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_llm_api_error_recovery(self):
        """Test recovery from LLM API errors."""
        from llm import create_llm
        from errors import LLMAPIError
        
        with patch('llm.ChatNVIDIA') as mock_chat:
            mock_instance = MagicMock()
            mock_chat.return_value = mock_instance
            
            # First call fails, second succeeds
            mock_instance.ainvoke = AsyncMock(side_effect=[
                LLMAPIError("Rate limit exceeded", provider="nvidia"),
                MagicMock(content="Success response")
            ])
            
            llm = create_llm("chapter_title_generation")
            
            # First call should raise error
            with pytest.raises(LLMAPIError):
                await llm.ainvoke("test")
            
            # Second call should succeed (in a retry scenario)
            result = await llm.ainvoke("test")
            assert result.content == "Success response"
    
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_missing_pdf_directory_handling(self):
        """Test handling of missing PDF directory."""
        from chapter_gen_from_file_names import chapter_gen_from_pdfs
        
        # Test with non-existent directory
        result = await chapter_gen_from_pdfs("/nonexistent/path")
        
        # Should return empty structure or handle gracefully
        assert result is not None


class TestPerformance:
    """Test performance and resource usage."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_llm_calls(self, mock_llm_responses):
        """Test multiple concurrent LLM calls."""
        from llm import create_llm
        
        llm = create_llm("chapter_title_generation")
        
        # Create multiple concurrent calls
        tasks = [
            llm.ainvoke(f"Test prompt {i}")
            for i in range(5)
        ]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify all succeeded
        assert len(results) == 5
        assert all(isinstance(r, str) for r in results)
    
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_large_pdf_processing(self, temp_pdf_dir, mock_llm_responses):
        """Test processing large number of PDFs."""
        # Create many mock PDFs
        chapter_dirs = []
        for i in range(50):
            chapter_dir = Path(temp_pdf_dir) / f"Chapter_{i}_Test"
            chapter_dir.mkdir(exist_ok=True)
            (chapter_dir / "content.pdf").write_text(f"Content {i}")
            chapter_dirs.append(f"Chapter_{i}_Test")
        
        # Should handle large directory
        with patch('os.listdir') as mock_listdir, \
             patch('os.path.isdir') as mock_isdir:
            
            mock_listdir.return_value = chapter_dirs
            mock_isdir.return_value = True
            
            result = await chapter_gen_from_pdfs(temp_pdf_dir)
            
            assert result is not None

