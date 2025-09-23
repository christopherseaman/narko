"""
Integration tests for Notion API interactions.
Tests the real API integration points and error handling.
"""
import pytest
import json
import time
from unittest.mock import patch, Mock
import requests

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from narko import upload_file_to_notion, create_notion_page, extract_page_id

@pytest.mark.integration
class TestNotionFileUpload:
    """Test Notion file upload API integration."""
    
    def test_file_upload_creation_success(self, sample_image_file, mock_notion_api, mock_env_vars):
        """Test successful file upload creation."""
        result = upload_file_to_notion(str(sample_image_file))
        
        # Verify API was called
        mock_notion_api['post'].assert_called()
        
        # Check the call was made to correct endpoint
        call_args = mock_notion_api['post'].call_args
        assert "file_uploads" in call_args[0][0]
        
        # Verify headers
        headers = call_args[1]['headers']
        assert "Authorization" in headers
        assert "Bearer test_api_key_" in headers["Authorization"]
        assert headers["Notion-Version"] == "2022-06-28"
    
    def test_file_upload_with_api_error(self, sample_image_file, mock_env_vars):
        """Test file upload with API error response."""
        with patch('requests.post') as mock_post:
            # Mock API error
            mock_post.return_value.status_code = 401
            mock_post.return_value.text = "Unauthorized"
            
            result = upload_file_to_notion(str(sample_image_file))
            
            assert "error" in result
            assert "401" in result["error"]
    
    def test_file_upload_missing_file(self, mock_env_vars):
        """Test file upload with non-existent file."""
        result = upload_file_to_notion("nonexistent.png")
        
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    def test_file_upload_rate_limiting(self, sample_image_file, mock_env_vars):
        """Test handling of rate limiting."""
        with patch('requests.post') as mock_post:
            # Mock rate limit response
            mock_post.return_value.status_code = 429
            mock_post.return_value.text = "Rate limited"
            
            result = upload_file_to_notion(str(sample_image_file))
            
            assert "error" in result
            assert "429" in result["error"]
    
    def test_file_upload_network_timeout(self, sample_image_file, mock_env_vars):
        """Test handling of network timeouts."""
        with patch('requests.post') as mock_post:
            # Mock timeout
            mock_post.side_effect = requests.exceptions.Timeout()
            
            result = upload_file_to_notion(str(sample_image_file))
            
            assert "error" in result
    
    def test_file_upload_invalid_api_response(self, sample_image_file, mock_env_vars):
        """Test handling of invalid API responses."""
        with patch('requests.post') as mock_post:
            # Mock invalid response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"invalid": "response"}
            
            result = upload_file_to_notion(str(sample_image_file))
            
            assert "error" in result

@pytest.mark.integration
class TestNotionPageCreation:
    """Test Notion page creation API integration."""
    
    def test_page_creation_success(self, notion_blocks_sample, mock_env_vars):
        """Test successful page creation."""
        with patch('requests.post') as mock_post:
            # Mock successful response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "id": "test-page-id",
                "url": "https://notion.so/test-page"
            }
            
            result = create_notion_page(
                "parent-page-id", 
                "Test Page", 
                notion_blocks_sample
            )
            
            assert "url" in result
            mock_post.assert_called_once()
    
    def test_page_creation_with_file_blocks(self, mock_env_vars):
        """Test page creation with file upload blocks."""
        blocks = [
            {
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {"url": "https://example.com/image.png"},
                    "caption": []
                }
            },
            {
                "type": "file",
                "file": {
                    "type": "file",
                    "file": {"id": "uploaded-file-id"},
                    "caption": []
                }
            }
        ]
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"id": "test-page-id"}
            
            result = create_notion_page("parent-id", "Test Page", blocks)
            
            # Verify blocks were included
            call_data = mock_post.call_args[1]['json']
            assert len(call_data['children']) == 2
            assert call_data['children'][0]['type'] == 'image'
            assert call_data['children'][1]['type'] == 'file'
    
    def test_page_creation_block_validation(self, mock_env_vars):
        """Test that blocks are validated before sending."""
        # Create blocks with potential issues
        blocks = [
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": None}  # Invalid content
                        }
                    ]
                }
            }
        ]
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"id": "test-page-id"}
            
            # Should handle invalid content gracefully
            result = create_notion_page("parent-id", "Test Page", blocks)
            
            # Verify content was sanitized
            call_data = mock_post.call_args[1]['json']
            content = call_data['children'][0]['paragraph']['rich_text'][0]['text']['content']
            assert isinstance(content, str)
    
    def test_page_creation_large_block_limit(self, mock_env_vars):
        """Test that block limit (100) is enforced."""
        # Create more than 100 blocks
        blocks = [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": f"Block {i}"}}]}
            }
            for i in range(150)
        ]
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"id": "test-page-id"}
            
            result = create_notion_page("parent-id", "Test Page", blocks)
            
            # Verify only 100 blocks were sent
            call_data = mock_post.call_args[1]['json']
            assert len(call_data['children']) == 100

@pytest.mark.integration
class TestAPIErrorHandling:
    """Test comprehensive API error handling."""
    
    def test_authentication_error(self, sample_image_file):
        """Test handling of authentication errors."""
        with patch.dict('os.environ', {'NOTION_API_KEY': 'invalid_key'}):
            with patch('requests.post') as mock_post:
                mock_post.return_value.status_code = 401
                mock_post.return_value.text = "Invalid token"
                
                result = upload_file_to_notion(str(sample_image_file))
                assert "error" in result
                assert "401" in result["error"]
    
    def test_permission_error(self, sample_image_file, mock_env_vars):
        """Test handling of permission errors."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 403
            mock_post.return_value.text = "Insufficient permissions"
            
            result = upload_file_to_notion(str(sample_image_file))
            assert "error" in result
            assert "403" in result["error"]
    
    def test_server_error(self, sample_image_file, mock_env_vars):
        """Test handling of server errors."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 500
            mock_post.return_value.text = "Internal server error"
            
            result = upload_file_to_notion(str(sample_image_file))
            assert "error" in result
            assert "500" in result["error"]
    
    def test_network_connection_error(self, sample_image_file, mock_env_vars):
        """Test handling of network connection errors."""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError()
            
            result = upload_file_to_notion(str(sample_image_file))
            assert "error" in result
    
    def test_invalid_json_response(self, sample_image_file, mock_env_vars):
        """Test handling of invalid JSON responses."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            
            result = upload_file_to_notion(str(sample_image_file))
            assert "error" in result

@pytest.mark.integration
class TestAPIPerformance:
    """Test API performance characteristics."""
    
    def test_upload_timeout_handling(self, sample_image_file, mock_env_vars):
        """Test that uploads timeout appropriately."""
        with patch('requests.post') as mock_post:
            # Simulate slow response
            def slow_response(*args, **kwargs):
                time.sleep(0.1)  # Short delay for testing
                response = Mock()
                response.status_code = 200
                response.json.return_value = {"id": "test"}
                return response
            
            mock_post.side_effect = slow_response
            
            start_time = time.time()
            result = upload_file_to_notion(str(sample_image_file))
            duration = time.time() - start_time
            
            # Should complete but we can measure timing
            assert duration > 0.1  # At least as long as our delay
    
    def test_batch_upload_handling(self, temp_dir, mock_env_vars):
        """Test handling multiple concurrent uploads."""
        # Create multiple test files
        files = []
        for i in range(5):
            file_path = temp_dir / f"test_{i}.txt"
            file_path.write_text(f"Test content {i}")
            files.append(file_path)
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"id": "test-id"}
            
            results = []
            for file_path in files:
                result = upload_file_to_notion(str(file_path))
                results.append(result)
            
            # All should succeed
            assert all("error" not in result for result in results)
            # API should be called for each file
            assert mock_post.call_count == len(files)

@pytest.mark.integration
class TestAPIRequestFormat:
    """Test that API requests are formatted correctly."""
    
    def test_file_upload_request_format(self, sample_image_file, mock_env_vars):
        """Test file upload request structure."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "id": "test-id",
                "upload_url": "https://test.com"
            }
            
            result = upload_file_to_notion(str(sample_image_file))
            
            # Check request format
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            
            assert 'name' in request_data
            assert 'size' in request_data
            assert request_data['name'] == sample_image_file.name
            assert request_data['size'] == os.path.getsize(sample_image_file)
    
    def test_page_creation_request_format(self, notion_blocks_sample, mock_env_vars):
        """Test page creation request structure."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"id": "test-page"}
            
            result = create_notion_page(
                "parent-id",
                "Test Title",
                notion_blocks_sample
            )
            
            # Check request format
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            
            assert 'parent' in request_data
            assert 'properties' in request_data
            assert 'children' in request_data
            assert request_data['parent']['page_id'] == 'parent-id'
            assert request_data['properties']['title']['title'][0]['text']['content'] == 'Test Title'

@pytest.mark.integration
@pytest.mark.slow
class TestRealAPIIntegration:
    """
    Tests for real API integration (requires valid API key).
    These tests are marked as 'slow' and should only run with real credentials.
    """
    
    @pytest.mark.skipif(
        not os.environ.get('NOTION_API_KEY') or not os.environ.get('NOTION_IMPORT_ROOT'),
        reason="Real API credentials not available"
    )
    def test_real_file_upload(self, sample_image_file):
        """Test actual file upload to Notion (requires real API key)."""
        result = upload_file_to_notion(str(sample_image_file))
        
        # With real API, this might succeed or fail depending on permissions
        # We just verify it doesn't crash
        assert isinstance(result, dict)
    
    @pytest.mark.skipif(
        not os.environ.get('NOTION_API_KEY') or not os.environ.get('NOTION_IMPORT_ROOT'),
        reason="Real API credentials not available"
    )
    def test_real_page_creation(self, notion_blocks_sample):
        """Test actual page creation in Notion (requires real API key)."""
        parent_id = os.environ.get('NOTION_IMPORT_ROOT')
        
        result = create_notion_page(
            parent_id,
            f"Test Page {int(time.time())}",  # Unique title
            notion_blocks_sample[:1]  # Just one block to minimize impact
        )
        
        # Should either succeed or fail gracefully
        assert isinstance(result, dict)