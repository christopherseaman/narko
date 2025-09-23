"""
Security tests for file upload and processing functionality.
Tests for path traversal, injection attacks, and other security vulnerabilities.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch, Mock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from narko import (
    FileUploadBlock, process_file, upload_file_to_notion, 
    extract_page_id, create_rich_text
)

@pytest.mark.security
class TestPathTraversalPrevention:
    """Test prevention of path traversal attacks."""
    
    def test_basic_path_traversal_attempts(self):
        """Test basic directory traversal prevention."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam", 
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\sam",
            "..%2F..%2F..%2Fetc%2Fpasswd",  # URL encoded
            "..%5C..%5C..%5Cwindows%5Csystem32%5Cconfig%5Csam"
        ]
        
        for path in malicious_paths:
            # Create mock match for FileUploadBlock
            class MockMatch:
                def group(self, n):
                    if n == 2: return 'file'
                    if n == 3: return ''
                    if n == 4: return path
            
            block = FileUploadBlock(MockMatch())
            
            # Should handle malicious paths without crashing
            assert hasattr(block, 'file_path')
            assert block.file_path == path  # Path is stored as-is
            
            # The security check should happen during file access
            # process_file should handle non-existent/invalid paths safely
    
    def test_relative_path_handling(self, temp_dir):
        """Test handling of relative paths in different contexts."""
        # Create a markdown file with relative path references
        test_content = """# Test Document

![file](../../../sensitive_file.txt)
![image](./../../private/image.png)
![pdf](../system/document.pdf)
"""
        
        md_file = temp_dir / "relative_test.md"
        md_file.write_text(test_content)
        
        # Process should handle relative paths safely
        result = process_file(str(md_file))
        
        assert "error" not in result  # Should not crash
        assert len(result["blocks"]) > 0
        
        # Should contain error messages for missing files
        error_blocks = [
            block for block in result["blocks"]
            if block.get("type") == "paragraph" and
            "❌" in str(block.get("paragraph", {}).get("rich_text", []))
        ]
        assert len(error_blocks) > 0  # Should have error blocks for missing files
    
    def test_symlink_handling(self, temp_dir):
        """Test handling of symbolic links."""
        # Create a test file and symlink
        real_file = temp_dir / "real_file.txt"
        real_file.write_text("Real file content")
        
        symlink_file = temp_dir / "symlink_file.txt"
        try:
            symlink_file.symlink_to(real_file)
            
            # Test processing file with symlink reference
            md_content = f"![file]({symlink_file})"
            md_file = temp_dir / "symlink_test.md"
            md_file.write_text(md_content)
            
            result = process_file(str(md_file))
            
            # Should handle symlinks safely (follow or reject based on policy)
            assert isinstance(result, dict)
            
        except OSError:
            # Symlinks might not be supported on all systems
            pytest.skip("Symlinks not supported on this system")

@pytest.mark.security
class TestInputSanitization:
    """Test input sanitization and validation."""
    
    def test_malicious_filename_handling(self, temp_dir):
        """Test handling of files with malicious names."""
        malicious_names = [
            "file<script>alert('xss')</script>.txt",
            "file\x00null_byte.txt",
            "file\r\nCRLF_injection.txt",
            "file'; DROP TABLE users; --.txt",
            "file`rm -rf /`.txt",
            "file$(whoami).txt"
        ]
        
        for filename in malicious_names:
            try:
                # Create file with malicious name
                safe_filename = "".join(c for c in filename if c.isalnum() or c in '._-')
                if not safe_filename:
                    safe_filename = "malicious_test.txt"
                
                file_path = temp_dir / safe_filename
                file_path.write_text("Test content")
                
                # Test processing
                md_content = f"![file]({file_path})"
                md_file = temp_dir / "malicious_name_test.md"
                md_file.write_text(md_content)
                
                result = process_file(str(md_file))
                
                # Should handle without crashing
                assert isinstance(result, dict)
                
            except (OSError, ValueError):
                # Some malicious names might be rejected by filesystem
                pass
    
    def test_large_filename_handling(self, temp_dir):
        """Test handling of extremely long filenames."""
        # Create filename at or near filesystem limits
        long_name = "a" * 200 + ".txt"
        
        try:
            file_path = temp_dir / long_name
            file_path.write_text("Test content")
            
            md_content = f"![file]({file_path})"
            md_file = temp_dir / "long_name_test.md"
            md_file.write_text(md_content)
            
            result = process_file(str(md_file))
            
            # Should handle long names gracefully
            assert isinstance(result, dict)
            
        except OSError:
            # Filename too long for filesystem
            pytest.skip("Filesystem doesn't support long filenames")
    
    def test_unicode_filename_security(self, temp_dir):
        """Test security with Unicode filenames."""
        unicode_names = [
            "файл.txt",  # Cyrillic
            "文件.txt",   # Chinese
            "ファイル.txt", # Japanese
            "🚀📁💾.txt",  # Emoji
            "file\u202e.txt",  # Right-to-left override
            "file\u200b.txt"   # Zero-width space
        ]
        
        for filename in unicode_names:
            try:
                file_path = temp_dir / filename
                file_path.write_text("Unicode content")
                
                md_content = f"![file]({file_path})"
                md_file = temp_dir / "unicode_test.md"
                md_file.write_text(md_content)
                
                result = process_file(str(md_file))
                
                # Should handle Unicode safely
                assert isinstance(result, dict)
                
            except (UnicodeError, OSError):
                # Some Unicode might not be supported
                pass

@pytest.mark.security
class TestContentSecurityValidation:
    """Test content security and injection prevention."""
    
    def test_script_injection_in_content(self, temp_dir):
        """Test prevention of script injection in file content."""
        malicious_content = """
        <script>alert('XSS')</script>
        <img src=x onerror=alert('XSS')>
        <svg onload=alert('XSS')>
        javascript:alert('XSS')
        data:text/html,<script>alert('XSS')</script>
        """
        
        file_path = temp_dir / "malicious_content.html"
        file_path.write_text(malicious_content)
        
        md_content = f"![file]({file_path})"
        md_file = temp_dir / "injection_test.md"
        md_file.write_text(md_content)
        
        with patch('narko.upload_file_to_notion') as mock_upload:
            mock_upload.return_value = {
                "file_id": "safe-file-123",
                "success": True
            }
            
            result = process_file(str(md_file))
            
            # Should process without executing malicious content
            assert "error" not in result
            assert len(result["blocks"]) > 0
    
    def test_binary_file_content_safety(self, temp_dir):
        """Test safe handling of binary file content."""
        # Create a binary file with potentially malicious content
        binary_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100 + b'<script>alert("xss")</script>'
        
        file_path = temp_dir / "malicious_binary.png"
        file_path.write_bytes(binary_content)
        
        # Test embedding generation for binary file
        from narko import generate_file_embedding_data
        embedding_data = generate_file_embedding_data(str(file_path))
        
        # Should handle binary content safely
        assert isinstance(embedding_data, dict)
        assert "file_hash" in embedding_data
        
        # Text content should be limited/safe for binary files
        text_content = embedding_data.get("text_content", "")
        assert len(text_content) < 1000  # Should be metadata only
    
    def test_markdown_injection_prevention(self, temp_dir):
        """Test prevention of markdown injection attacks."""
        malicious_markdown = """# Normal Title

![image](javascript:alert('XSS'))
![file](data:text/html,<script>alert('XSS')</script>)
![pdf](http://malicious-site.com/malware.exe)

[Link](javascript:alert('XSS'))
[Link](data:text/html,<script>alert('XSS')</script>)

<script>alert('XSS')</script>
<iframe src="javascript:alert('XSS')"></iframe>
<img src=x onerror=alert('XSS')>
"""
        
        md_file = temp_dir / "markdown_injection.md"
        md_file.write_text(malicious_markdown)
        
        result = process_file(str(md_file))
        
        # Should process without executing malicious content
        assert "error" not in result
        assert len(result["blocks"]) > 0
        
        # Check that dangerous URLs are handled safely
        # External file blocks should preserve URLs as-is (validation happens client-side)
        # but should not execute them during processing
        image_blocks = [b for b in result["blocks"] if b.get("type") == "image"]
        for block in image_blocks:
            if "external" in block.get("image", {}):
                url = block["image"]["external"]["url"]
                # URL should be preserved but not executed
                assert isinstance(url, str)

@pytest.mark.security
class TestApiSecurityValidation:
    """Test API security measures."""
    
    def test_api_key_exposure_prevention(self, mock_env_vars):
        """Test that API keys are not exposed in error messages."""
        with patch('requests.post') as mock_post:
            # Mock API error that might include sensitive info
            mock_post.return_value.status_code = 401
            mock_post.return_value.text = f"Invalid API key: {os.environ.get('NOTION_API_KEY', 'test-key')}"
            
            result = upload_file_to_notion("test.png")
            
            # Error message should not contain the actual API key
            assert "error" in result
            error_message = result["error"]
            assert "test_api_key_" not in error_message  # Mock key from fixture
    
    def test_request_data_sanitization(self, sample_text_file, mock_env_vars):
        """Test that request data is properly sanitized."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "id": "sanitized-test",
                "upload_url": "https://test.com"
            }
            
            result = upload_file_to_notion(str(sample_text_file))
            
            # Check that request data was properly formatted
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            
            # Should contain only expected fields
            expected_fields = {'name', 'size'}
            assert set(request_data.keys()).issubset(expected_fields)
            
            # Values should be properly typed
            assert isinstance(request_data['name'], str)
            assert isinstance(request_data['size'], int)
            assert request_data['size'] >= 0
    
    def test_response_data_validation(self, sample_text_file, mock_env_vars):
        """Test validation of API response data."""
        test_cases = [
            # Missing required fields
            {"invalid": "response"},
            # Wrong data types
            {"id": 123, "upload_url": None},
            # Empty response
            {},
            # Malicious response
            {
                "id": "<script>alert('xss')</script>",
                "upload_url": "javascript:alert('xss')"
            }
        ]
        
        for response_data in test_cases:
            with patch('requests.post') as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = response_data
                
                result = upload_file_to_notion(str(sample_text_file))
                
                # Should handle invalid responses safely
                if not response_data.get("id") or not response_data.get("upload_url"):
                    assert "error" in result
                else:
                    # Should sanitize malicious content if processing continues
                    assert isinstance(result, dict)

@pytest.mark.security
class TestFileSystemSecurity:
    """Test file system security measures."""
    
    def test_temporary_file_cleanup(self, temp_dir):
        """Test that temporary files are cleaned up properly."""
        # This test would verify temporary file cleanup
        # Current implementation doesn't create temp files, but good to have
        # for future enhancements
        
        initial_files = set(temp_dir.glob("*"))
        
        # Process a file that might create temporary files
        md_content = "# Test\n\nContent that might need temp files."
        md_file = temp_dir / "temp_test.md"
        md_file.write_text(md_content)
        
        result = process_file(str(md_file))
        
        # Check that no unexpected temporary files were left behind
        final_files = set(temp_dir.glob("*"))
        new_files = final_files - initial_files
        
        # Should only have the files we explicitly created
        expected_new_files = {md_file}
        unexpected_files = new_files - expected_new_files
        
        assert len(unexpected_files) == 0, f"Unexpected temporary files: {unexpected_files}"
    
    def test_file_permission_validation(self, temp_dir):
        """Test file permission handling."""
        try:
            # Create file with restricted permissions
            restricted_file = temp_dir / "restricted.txt"
            restricted_file.write_text("Restricted content")
            restricted_file.chmod(0o000)  # No permissions
            
            md_content = f"![file]({restricted_file})"
            md_file = temp_dir / "permission_test.md"
            md_file.write_text(md_content)
            
            result = process_file(str(md_file))
            
            # Should handle permission errors gracefully
            assert isinstance(result, dict)
            
        except (OSError, PermissionError):
            # Permission changes might not work on all systems
            pytest.skip("Cannot modify file permissions on this system")
        finally:
            # Restore permissions for cleanup
            try:
                restricted_file.chmod(0o644)
            except:
                pass
    
    def test_file_size_attack_prevention(self, temp_dir):
        """Test prevention of file size-based attacks."""
        # Test with file exactly at limit
        file_path = temp_dir / "at_limit.txt"
        content = "x" * (5 * 1024 * 1024)  # Exactly 5MB
        file_path.write_text(content)
        
        result = upload_file_to_notion(str(file_path))
        
        # Should handle file at limit
        # Note: Actual limit check happens in upload_file_to_notion
        if os.path.getsize(file_path) > 5 * 1024 * 1024:
            assert "error" in result
            assert "too large" in result["error"].lower()
        
        # Test with oversized file (already tested in other test files)
        # This validates the security boundary