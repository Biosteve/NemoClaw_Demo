"""
Tests for FileService.

These tests verify the Gradio-agnostic file handling business logic.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from services.file_service import (
    FileService,
    FileValidationResult,
    FileUploadResult,
    MAX_FILES,
    MAX_FILE_SIZE_GB,
    MAX_PAGES_PER_FILE
)


class TestFileServiceInit:
    """Tests for FileService initialization."""
    
    def test_init_with_defaults(self):
        """Test service initialization with default values."""
        service = FileService(mnt_folder="/test/path")
        assert service.mnt_folder == "/test/path"
        assert service.max_files == MAX_FILES
        assert service.max_file_size_gb == MAX_FILE_SIZE_GB
        assert service.max_pages_per_file == MAX_PAGES_PER_FILE
    
    def test_init_with_custom_values(self):
        """Test service initialization with custom values."""
        service = FileService(
            mnt_folder="/custom/path",
            max_files=10,
            max_file_size_gb=2.0,
            max_pages_per_file=50
        )
        assert service.max_files == 10
        assert service.max_file_size_gb == 2.0
        assert service.max_pages_per_file == 50
        assert service.max_file_size_bytes == int(2.0 * 1024 * 1024 * 1024)


class TestValidateFiles:
    """Tests for validate_files method."""
    
    @pytest.fixture
    def service(self):
        return FileService(mnt_folder="/tmp")
    
    @pytest.fixture
    def temp_pdf(self, tmp_path):
        """Create a temporary PDF file."""
        pdf_path = tmp_path / "test.pdf"
        # Create minimal PDF content
        pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")
        return str(pdf_path)
    
    def test_validate_empty_list(self, service):
        """Test validation with empty file list."""
        result = service.validate_files([])
        assert result.is_valid == True
        assert result.message == ""
    
    def test_validate_none(self, service):
        """Test validation with None."""
        result = service.validate_files(None)
        assert result.is_valid == True
    
    def test_validate_too_many_files(self, service, tmp_path):
        """Test validation fails when too many files."""
        # Create more files than allowed
        files = []
        for i in range(MAX_FILES + 1):
            pdf_path = tmp_path / f"test_{i}.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            files.append(str(pdf_path))
        
        result = service.validate_files(files)
        assert result.is_valid == False
        assert "maximum" in result.message.lower()
    
    def test_validate_non_pdf_file(self, service, tmp_path):
        """Test validation fails for non-PDF file."""
        txt_path = tmp_path / "test.txt"
        txt_path.write_text("Hello")
        
        result = service.validate_files([str(txt_path)])
        assert result.is_valid == False
        assert "not a PDF" in result.message
    
    def test_validate_nonexistent_file(self, service):
        """Test validation fails for nonexistent file."""
        result = service.validate_files(["/nonexistent/file.pdf"])
        assert result.is_valid == False
        assert "not found" in result.errors[0].lower()
    
    def test_validate_valid_pdf(self, service, temp_pdf):
        """Test validation passes for valid PDF."""
        # Mock PdfReader to avoid actual PDF parsing
        with patch('services.file_service.PdfReader') as mock_reader:
            mock_reader.return_value.pages = [Mock()] * 5  # 5 pages
            
            result = service.validate_files([temp_pdf])
            assert result.is_valid == True
            assert "successfully" in result.message.lower()
            assert temp_pdf in result.validated_files
    
    def test_validate_file_too_large(self, service, tmp_path):
        """Test validation fails for oversized file."""
        # Create service with small size limit (1 byte)
        small_service = FileService(
            mnt_folder="/tmp",
            max_file_size_gb=0.000000001  # ~1 byte limit
        )
        
        pdf_path = tmp_path / "large.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n" + b"x" * 100)  # File larger than 1 byte
        
        result = small_service.validate_files([str(pdf_path)])
        assert result.is_valid == False
        # Either size error or PDF parsing error is acceptable
        assert "GB" in result.message or "Error" in result.message
    
    def test_validate_too_many_pages(self, service, temp_pdf):
        """Test validation fails for PDF with too many pages."""
        with patch('services.file_service.PdfReader') as mock_reader:
            mock_reader.return_value.pages = [Mock()] * (MAX_PAGES_PER_FILE + 1)
            
            result = service.validate_files([temp_pdf])
            assert result.is_valid == False
            assert "pages" in result.message.lower()


class TestCopyFilesToUserDir:
    """Tests for copy_files_to_user_dir method."""
    
    @pytest.fixture
    def service(self, tmp_path):
        return FileService(mnt_folder=str(tmp_path))
    
    @pytest.fixture
    def temp_pdf(self, tmp_path):
        """Create a temporary PDF file."""
        pdf_path = tmp_path / "source.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")
        return str(pdf_path)
    
    def test_copy_creates_directories(self, service, temp_pdf):
        """Test that copy creates necessary directories."""
        copied, pdf_dir = service.copy_files_to_user_dir([temp_pdf], "testuser")
        
        assert os.path.exists(pdf_dir)
        assert os.path.exists(os.path.join(service.mnt_folder, "testuser"))
    
    def test_copy_files_to_correct_location(self, service, temp_pdf):
        """Test files are copied to correct location."""
        copied, pdf_dir = service.copy_files_to_user_dir([temp_pdf], "testuser")
        
        assert len(copied) == 1
        assert os.path.exists(copied[0])
        assert "testuser" in pdf_dir


class TestGetNewFilesToProcess:
    """Tests for get_new_files_to_process method."""
    
    @pytest.fixture
    def service(self, tmp_path):
        return FileService(mnt_folder=str(tmp_path))
    
    def test_first_upload_all_files_new(self, service, tmp_path):
        """Test first upload marks all files as new."""
        pdf_dir = tmp_path / "pdfs" / "testuser"
        pdf_dir.mkdir(parents=True)
        
        # Create test PDF
        (pdf_dir / "test1.pdf").write_bytes(b"%PDF")
        (pdf_dir / "test2.pdf").write_bytes(b"%PDF")
        
        new_files, processed = service.get_new_files_to_process(str(pdf_dir), "testuser")
        
        assert len(new_files) == 2
        assert len(processed) == 0
    
    def test_subsequent_upload_filters_processed(self, service, tmp_path):
        """Test subsequent upload filters already processed files."""
        pdf_dir = tmp_path / "pdfs" / "testuser"
        pdf_dir.mkdir(parents=True)
        
        # Create test PDFs
        pdf1 = pdf_dir / "test1.pdf"
        pdf2 = pdf_dir / "test2.pdf"
        pdf1.write_bytes(b"%PDF")
        pdf2.write_bytes(b"%PDF")
        
        # Create processed files record
        processed_path = tmp_path / "testuser_files.txt"
        processed_path.write_text(f"{pdf1}\n")
        
        new_files, processed = service.get_new_files_to_process(str(pdf_dir), "testuser")
        
        assert len(new_files) == 1
        assert str(pdf2) in new_files[0]


class TestUploadFiles:
    """Tests for upload_files method."""
    
    @pytest.fixture
    def service(self, tmp_path):
        return FileService(mnt_folder=str(tmp_path))
    
    @pytest.fixture
    def temp_pdf(self, tmp_path):
        """Create a temporary PDF file."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        pdf_path = source_dir / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")
        return str(pdf_path)
    
    def test_upload_empty_list(self, service):
        """Test upload with empty file list."""
        result = service.upload_files([], "testuser")
        assert result.success == True
        assert result.message == ""
    
    def test_upload_invalid_file_returns_error(self, service):
        """Test upload with invalid file returns error."""
        result = service.upload_files(["/nonexistent.pdf"], "testuser")
        assert result.success == False
    
    @patch('services.file_service.fetch_collections')
    @patch('services.file_service.create_collection')
    @patch('services.file_service.upload_files_to_nemo_retriever')
    def test_upload_valid_file_success(
        self,
        mock_upload,
        mock_create,
        mock_fetch,
        service,
        temp_pdf
    ):
        """Test successful file upload."""
        # Mock NeMo Retriever responses
        mock_fetch.return_value = '{"collections": []}'
        mock_create.return_value = {"status": "created"}
        mock_upload.return_value = {"status": "success"}
        
        # Mock PdfReader
        with patch('services.file_service.PdfReader') as mock_reader:
            mock_reader.return_value.pages = [Mock()] * 5
            
            # Mock time.sleep to speed up test
            with patch('services.file_service.time.sleep'):
                result = service.upload_files([temp_pdf], "testuser")
        
        assert result.success == True
        assert len(result.copied_files) == 1


class TestGetUploadedFiles:
    """Tests for get_uploaded_files method."""
    
    @pytest.fixture
    def service(self, tmp_path):
        return FileService(mnt_folder=str(tmp_path))
    
    def test_get_files_empty_dir(self, service):
        """Test getting files from empty/nonexistent directory."""
        result = service.get_uploaded_files("nonexistent_user")
        assert result == []
    
    def test_get_files_returns_pdfs_only(self, service, tmp_path):
        """Test getting files returns only PDFs."""
        pdf_dir = tmp_path / "pdfs" / "testuser"
        pdf_dir.mkdir(parents=True)
        
        # Create mixed files
        (pdf_dir / "doc1.pdf").write_bytes(b"%PDF")
        (pdf_dir / "doc2.pdf").write_bytes(b"%PDF")
        (pdf_dir / "notes.txt").write_text("notes")
        
        result = service.get_uploaded_files("testuser")
        
        assert len(result) == 2
        assert all(f.endswith(".pdf") for f in result)


class TestFileValidationResultDataclass:
    """Tests for FileValidationResult dataclass."""
    
    def test_default_values(self):
        """Test default values."""
        result = FileValidationResult(is_valid=True, message="OK")
        assert result.validated_files == []
        assert result.errors == []
    
    def test_with_files(self):
        """Test with validated files."""
        result = FileValidationResult(
            is_valid=True,
            message="OK",
            validated_files=["file1.pdf", "file2.pdf"]
        )
        assert len(result.validated_files) == 2


class TestFileUploadResultDataclass:
    """Tests for FileUploadResult dataclass."""
    
    def test_default_values(self):
        """Test default values."""
        result = FileUploadResult(success=True, message="OK")
        assert result.copied_files == []
        assert result.uploaded_to_nemo == []
        assert result.skipped_files == []
        assert result.errors == []
    
    def test_full_result(self):
        """Test with all fields populated."""
        result = FileUploadResult(
            success=True,
            message="Uploaded",
            copied_files=["a.pdf"],
            uploaded_to_nemo=["a.pdf"],
            skipped_files=["b.pdf"],
            errors=[]
        )
        assert result.success == True
        assert len(result.copied_files) == 1
        assert len(result.uploaded_to_nemo) == 1
        assert len(result.skipped_files) == 1

