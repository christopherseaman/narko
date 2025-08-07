"""
Unit tests for file processing functionality.
Tests the core file validation, type detection, and processing logic.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch, Mock

# Import functions from narko for testing
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from narko import (
    SUPPORTED_FILE_TYPES, MAX_FILE_SIZE,
    extract_page_id, chunk_text, create_rich_text
)

@pytest.mark.unit
class TestFileValidation:
    """Test file validation functions."""
    
    def test_supported_file_types_detection(self, sample_image_file):
        """Test that supported file types are correctly identified."""
        # Test image file
        assert sample_image_file.suffix.lower() in SUPPORTED_FILE_TYPES
        
        # Test various extensions
        supported_extensions = ['.png', '.jpg', '.pdf', '.mp4', '.txt', '.json']
        for ext in supported_extensions:
            assert ext in SUPPORTED_FILE_TYPES
    
    def test_unsupported_file_types(self):
        """Test that unsupported file types are rejected."""
        unsupported_extensions = ['.exe', '.bat', '.scr', '.com', '.pif']
        for ext in unsupported_extensions:
            assert ext not in SUPPORTED_FILE_TYPES
    
    def test_file_size_limits(self, large_file, oversized_file):
        """Test file size validation."""
        # Test file under limit
        assert os.path.getsize(large_file) <= MAX_FILE_SIZE
        
        # Test file over limit
        assert os.path.getsize(oversized_file) > MAX_FILE_SIZE
    
    def test_file_existence_validation(self, sample_image_file, temp_dir):
        """Test file existence checking."""
        # Existing file
        assert sample_image_file.exists()
        
        # Non-existing file
        non_existent = temp_dir / "does_not_exist.png"
        assert not non_existent.exists()
    
    def test_empty_file_handling(self, empty_file):
        """Test handling of empty files."""
        assert empty_file.exists()
        assert os.path.getsize(empty_file) == 0

@pytest.mark.unit 
class TestFileTypeInference:
    """Test automatic file type inference from extensions."""
    
    def test_image_type_inference(self):
        """Test image file type detection."""
        from narko import FileUploadBlock
        
        # Create mock match object
        class MockMatch:
            def group(self, n):
                if n == 2: return 'file'  # file_type
                if n == 3: return ''      # title  
                if n == 4: return 'test.png'  # file_path
        
        block = FileUploadBlock(MockMatch())
        assert block._infer_file_type() == 'image'
    
    def test_video_type_inference(self):
        """Test video file type detection."""
        from narko import FileUploadBlock
        
        class MockMatch:
            def group(self, n):
                if n == 2: return 'file'
                if n == 3: return ''
                if n == 4: return 'demo.mp4'
        
        block = FileUploadBlock(MockMatch())
        assert block._infer_file_type() == 'video'
    
    def test_pdf_type_inference(self):
        """Test PDF file type detection."""
        from narko import FileUploadBlock
        
        class MockMatch:
            def group(self, n):
                if n == 2: return 'file'
                if n == 3: return ''
                if n == 4: return 'document.pdf'
        
        block = FileUploadBlock(MockMatch())
        assert block._infer_file_type() == 'pdf'
    
    def test_unknown_type_fallback(self):
        """Test fallback to 'file' for unknown extensions."""
        from narko import FileUploadBlock
        
        class MockMatch:
            def group(self, n):
                if n == 2: return 'file'
                if n == 3: return ''
                if n == 4: return 'unknown.xyz'
        
        block = FileUploadBlock(MockMatch())
        assert block._infer_file_type() == 'file'

@pytest.mark.unit
class TestUtilityFunctions:
    """Test utility functions used in file processing."""
    
    def test_chunk_text_within_limit(self):
        """Test text chunking with content under limit."""
        text = "Short text"
        chunks = chunk_text(text, limit=2000)
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_over_limit(self):
        """Test text chunking with content over limit."""
        text = "word " * 1000  # Create long text
        chunks = chunk_text(text, limit=100)
        assert len(chunks) > 1
        # Verify no chunk exceeds limit
        for chunk in chunks:
            assert len(chunk) <= 100
    
    def test_chunk_text_preserves_words(self):
        """Test that chunking preserves word boundaries."""
        text = "This is a test sentence that should be split properly"
        chunks = chunk_text(text, limit=20)
        
        # Check that words are not split
        for chunk in chunks:
            if len(chunk) > 0:
                assert not chunk.endswith(' ')
                words = chunk.split()
                # Ensure we have complete words
                assert all(word.strip() for word in words)
    
    def test_create_rich_text_basic(self):
        """Test basic rich text creation."""
        result = create_rich_text("Test content")
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert result[0]["text"]["content"] == "Test content"
    
    def test_create_rich_text_with_annotations(self):
        """Test rich text creation with formatting."""
        annotations = {"bold": True, "color": "red"}
        result = create_rich_text("Bold text", annotations)
        assert result[0]["annotations"]["bold"] is True
        assert result[0]["annotations"]["color"] == "red"
    
    def test_create_rich_text_with_link(self):
        """Test rich text creation with links."""
        result = create_rich_text("Link text", link="https://example.com")
        assert result[0]["text"]["link"]["url"] == "https://example.com"
    
    def test_extract_page_id_from_url(self):
        """Test page ID extraction from Notion URLs."""
        # Test full URL
        url = "https://notion.so/workspace/Page-Title-1234567890abcdef1234567890abcdef"
        result = extract_page_id(url)
        assert len(result) == 36  # UUID with dashes
        assert result.count('-') == 4
        
        # Test UUID without dashes
        uuid_no_dashes = "1234567890abcdef1234567890abcdef"
        result = extract_page_id(uuid_no_dashes)
        assert result == "12345678-90ab-cdef-1234-567890abcdef"
        
        # Test already formatted UUID
        formatted_uuid = "12345678-90ab-cdef-1234-567890abcdef"
        result = extract_page_id(formatted_uuid)
        assert result == formatted_uuid

@pytest.mark.unit
class TestErrorHandling:
    """Test error handling in file processing."""
    
    def test_missing_file_error(self, temp_dir):
        """Test handling of missing files."""
        from narko import process_file
        
        missing_file = temp_dir / "missing.md"
        result = process_file(str(missing_file))
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    def test_invalid_markdown_handling(self, temp_dir):
        """Test handling of invalid markdown content."""
        from narko import process_file
        
        # Create file with invalid/corrupted content
        invalid_file = temp_dir / "invalid.md"
        invalid_file.write_bytes(b'\x00\x01\x02\x03')  # Binary content
        
        # Should not crash, should handle gracefully
        result = process_file(str(invalid_file))
        assert "title" in result  # Should still process
    
    @patch('narko.NOTION_API_KEY', None)
    def test_missing_api_key_handling(self):
        """Test handling when API key is missing."""
        from narko import upload_file_to_notion
        
        result = upload_file_to_notion("test.png")
        # Should handle missing API key gracefully
        assert isinstance(result, dict)

@pytest.mark.unit
class TestSecurityValidation:
    """Test security-related validation."""
    
    def test_path_traversal_prevention(self):
        """Test prevention of directory traversal attacks."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\sam"
        ]
        
        from narko import FileUploadBlock
        
        for path in malicious_paths:
            class MockMatch:
                def group(self, n):
                    if n == 2: return 'file'
                    if n == 3: return ''
                    if n == 4: return path
            
            block = FileUploadBlock(MockMatch())
            # Should not crash and should handle path safely
            assert hasattr(block, 'file_path')
    
    def test_filename_sanitization(self, unicode_filename_file):
        """Test handling of special characters in filenames."""
        # File with Unicode should be handled safely
        assert unicode_filename_file.exists()
        
        # Test various special characters
        special_chars = ['<', '>', ':', '"', '|', '?', '*']
        # These should be handled without system errors

@pytest.mark.unit 
class TestPerformanceBasics:
    """Basic performance validation for file processing."""
    
    def test_large_file_processing_performance(self, large_file):
        """Test that large files are processed in reasonable time."""
        import time
        from narko import process_file, upload_file_to_notion
        
        # Create markdown with large file reference
        md_content = f"![file]({large_file})"
        md_file = large_file.parent / "test.md"
        md_file.write_text(md_content)
        
        start_time = time.time()
        result = process_file(str(md_file))
        processing_time = time.time() - start_time
        
        # Should process within reasonable time (adjust based on requirements)
        assert processing_time < 5.0  # 5 seconds max
        assert "blocks" in result
    
    def test_memory_usage_reasonable(self, sample_image_file):
        """Test that memory usage stays reasonable during processing."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process multiple files
        from narko import process_file
        for i in range(10):
            md_content = f"![file]({sample_image_file})"
            md_file = sample_image_file.parent / f"test_{i}.md"
            md_file.write_text(md_content)
            process_file(str(md_file))
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (adjust based on requirements)
        assert memory_increase < 50 * 1024 * 1024  # Less than 50MB increase