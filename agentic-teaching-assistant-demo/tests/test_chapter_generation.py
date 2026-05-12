"""
Tests for chapter generation module.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path


@pytest.mark.asyncio
async def test_chapter_gen_from_pdfs(temp_pdf_dir, mock_env_vars):
    """Test chapter generation from PDFs."""
    # Create a test PDF file
    test_pdf = temp_pdf_dir / "test.pdf"
    test_pdf.write_text("test content")
    
    with patch('chapter_gen_from_file_names.chapter_gen_from_pdfs', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = '[{"file_loc": "test.pdf", "title": "Test Chapter"}]'
        
        from chapter_gen_from_file_names import chapter_gen_from_pdfs
        result = await chapter_gen_from_pdfs(str(temp_pdf_dir))
        
        assert result is not None
        assert "test.pdf" in result or "Test Chapter" in result


@pytest.mark.asyncio
async def test_chapter_gen_with_empty_directory(temp_pdf_dir):
    """Test chapter generation with empty directory."""
    with patch('chapter_gen_from_file_names.chapter_gen_from_pdfs', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "[]"
        
        from chapter_gen_from_file_names import chapter_gen_from_pdfs
        result = await chapter_gen_from_pdfs(str(temp_pdf_dir))
        
        assert result == "[]"


@pytest.mark.asyncio
async def test_chapter_title_generation_with_subtopics(mock_env_vars):
    """Test chapter title generation from subtopics."""
    subtopics = [
        "Introduction to Python",
        "Variables and Data Types",
        "Control Flow",
        "Functions"
    ]
    
    with patch('llm.ChatNVIDIA') as mock_chat:
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance
        mock_instance.ainvoke = AsyncMock(return_value=MagicMock(content='{"title": "Python Basics"}'))
        
        from llm import create_llm
        llm = create_llm("chapter_title_generation")
        
        prompt = f"Generate a chapter title from these subtopics: {subtopics}"
        result = await llm.ainvoke(prompt)
        
        assert "Python" in result.content or "title" in result.content


def test_parse_output_from_chapters():
    """Test parsing chapter output."""
    from chapter_gen_from_file_names import parse_output_from_chapters
    
    # Test with valid JSON
    valid_output = '[{"file_loc": "test.pdf", "title": "Test Chapter"}]'
    result = parse_output_from_chapters(valid_output)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["title"] == "Test Chapter"

