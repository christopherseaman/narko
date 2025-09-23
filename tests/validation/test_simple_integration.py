#!/usr/bin/env python3
"""
Simple Integration Tests

Basic integration tests that validate core functionality without
requiring external API access. These tests ensure the package
works end-to-end with mock data.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

# Add src to path for testing
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestBasicIntegration:
    """Test basic integration scenarios"""
    
    def test_config_creation_and_validation(self):
        """Test configuration creation with various scenarios"""
        from narko import Config
        
        # Test valid configuration
        config = Config(
            notion_api_key="test_key_123",
            notion_import_root="page_id_456"
        )
        
        assert config.notion_api_key == "test_key_123"
        assert config.notion_import_root == "page_id_456"
        
        # Test invalid configuration
        with pytest.raises(ValueError):
            Config(notion_api_key="", notion_import_root="")
    
    def test_extension_registration(self):
        """Test that NotionExtension can be registered with marko"""
        try:
            from narko import NotionExtension
            from marko import Markdown
            
            # Test extension creation
            extension = NotionExtension()
            assert extension is not None
            
            # Test registration with Markdown parser
            md = Markdown(extensions=[extension])
            assert md is not None
            
        except ImportError as e:
            pytest.skip(f"Dependencies not available: {e}")
    
    def test_markdown_parsing_basic(self):
        """Test basic markdown parsing functionality"""
        try:
            from narko import NotionExtension
            from marko import Markdown
            
            md = Markdown(extensions=[NotionExtension()])
            
            # Test simple markdown
            result = md.parse("# Hello World\n\nThis is a test.")
            assert result is not None
            
        except ImportError as e:
            pytest.skip(f"Dependencies not available: {e}")
    
    @patch('narko.notion.client.requests.post')
    def test_notion_client_basic_operation(self, mock_post):
        """Test NotionClient basic operations with mocked API"""
        try:
            from narko import Config, NotionClient
            
            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "test_page_id",
                "url": "https://notion.so/test_page_id"
            }
            mock_post.return_value = mock_response
            
            config = Config(
                notion_api_key="test_key",
                notion_import_root="test_root"
            )
            
            client = NotionClient(config)
            
            # Test page creation
            response = client.create_page(
                parent_id="parent_123",
                title="Test Page",
                blocks=[]
            )
            
            assert "id" in response
            assert "url" in response
            
        except ImportError as e:
            pytest.skip(f"Dependencies not available: {e}")
    
    def test_converter_basic_functionality(self):
        """Test NotionConverter basic functionality"""
        try:
            from narko import Config, NotionConverter
            
            config = Config(
                notion_api_key="test_key",
                notion_import_root="test_root"
            )
            
            # Mock dependencies
            mock_uploader = Mock()
            mock_importer = Mock()
            
            converter = NotionConverter(config, mock_uploader, mock_importer)
            assert converter is not None
            
        except ImportError as e:
            pytest.skip(f"Dependencies not available: {e}")


class TestFileProcessing:
    """Test file processing scenarios"""
    
    def test_markdown_file_processing(self):
        """Test processing a markdown file end-to-end"""
        try:
            # Create temporary markdown file
            test_content = """# Test Document

This is a test markdown document with:

- List item 1
- List item 2

## Section 2

Some **bold** and *italic* text.

```python
print("Hello World")
```

> This is a blockquote
"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(test_content)
                temp_file = f.name
            
            try:
                # Test file processing without actual import
                sys.path.insert(0, str(project_root))
                
                # Import the main NarkoApp
                from narko import NarkoApp
                
                # Mock the config to avoid environment dependencies
                with patch('narko.config.Config.from_env') as mock_config:
                    mock_config.return_value = Mock(
                        notion_api_key="test_key",
                        notion_import_root="test_root",
                        embedding_enabled_types=set()
                    )
                    
                    # Mock other dependencies
                    with patch('narko.notion.client.NotionClient'), \
                         patch('narko.notion.uploader.FileUploader'), \
                         patch('narko.notion.uploader.ExternalImporter'), \
                         patch('narko.utils.cache.UploadCache'), \
                         patch('narko.utils.validation.FileValidator'):
                        
                        app = NarkoApp()
                        result = app.process_file(temp_file)
                        
                        # Verify result structure
                        assert "title" in result
                        assert "blocks" in result
                        assert "file_path" in result
                        assert result["title"] == Path(temp_file).stem
                        
            finally:
                # Clean up temp file
                os.unlink(temp_file)
                
        except ImportError as e:
            pytest.skip(f"Dependencies not available: {e}")
    
    def test_cache_functionality(self):
        """Test cache functionality"""
        try:
            from narko.utils import UploadCache
            from narko import Config
            
            config = Config(
                notion_api_key="test_key",
                notion_import_root="test_root"
            )
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Override cache location
                config.cache_file = Path(temp_dir) / "test_cache.json"
                
                cache = UploadCache(config)
                
                # Test cache operations
                test_file_path = "test.md"
                test_file_data = {"url": "https://example.com/test.md", "id": "file_123"}
                
                # Store in cache
                cache.store(test_file_path, test_file_data)
                
                # Retrieve from cache
                cached_data = cache.get(test_file_path)
                assert cached_data == test_file_data
                
                # Test cache stats
                stats = cache.get_stats()
                assert stats["cached_files"] >= 1
                
        except ImportError as e:
            pytest.skip(f"Dependencies not available: {e}")
    
    def test_file_validation(self):
        """Test file validation functionality"""
        try:
            from narko.utils import FileValidator
            from narko import Config
            
            config = Config(
                notion_api_key="test_key",
                notion_import_root="test_root"
            )
            
            validator = FileValidator(config)
            
            # Create test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write("# Test\nValid markdown content")
                temp_file = f.name
            
            try:
                # Test validation
                result = validator.validate_file(temp_file)
                
                assert "valid" in result
                assert "errors" in result
                assert "warnings" in result
                
            finally:
                os.unlink(temp_file)
                
        except ImportError as e:
            pytest.skip(f"Dependencies not available: {e}")


class TestCLIIntegration:
    """Test CLI integration scenarios"""
    
    def test_cli_script_structure(self):
        """Test that the CLI script has proper structure"""
        narko_script = project_root / "narko.py"
        
        if not narko_script.exists():
            pytest.skip("Main narko.py script not found")
        
        content = narko_script.read_text()
        
        # Test script structure
        assert "class NarkoApp:" in content, "Should have main app class"
        assert "def main():" in content, "Should have main function"
        assert "if __name__ == \"__main__\":" in content, "Should have main guard"
        assert "argparse" in content, "Should use argparse for CLI"
    
    def test_cli_argument_parsing(self):
        """Test CLI argument parsing"""
        try:
            import sys
            from unittest.mock import patch
            
            # Mock sys.argv to test argument parsing
            test_args = ["narko.py", "--help"]
            
            with patch.object(sys, 'argv', test_args):
                # Import and test argument parser
                sys.path.insert(0, str(project_root))
                
                # This will test the import and basic structure
                # The actual CLI test is in the CLI functionality tests
                import narko
                assert hasattr(narko, 'main')
                
        except SystemExit:
            # Expected for --help
            pass
        except ImportError as e:
            pytest.skip(f"Dependencies not available: {e}")


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_missing_file_handling(self):
        """Test handling of missing files"""
        try:
            from narko import Config
            
            config = Config(
                notion_api_key="test_key", 
                notion_import_root="test_root"
            )
            
            # Mock dependencies to test error handling
            with patch('narko.notion.client.NotionClient'), \
                 patch('narko.notion.uploader.FileUploader'), \
                 patch('narko.notion.uploader.ExternalImporter'), \
                 patch('narko.utils.cache.UploadCache'), \
                 patch('narko.utils.validation.FileValidator'):
                
                sys.path.insert(0, str(project_root))
                from narko import NarkoApp
                
                with patch('narko.config.Config.from_env', return_value=config):
                    app = NarkoApp()
                    
                    # Test missing file handling
                    result = app.process_file("nonexistent_file.md")
                    assert "error" in result
                    assert "not found" in result["error"].lower()
                    
        except ImportError as e:
            pytest.skip(f"Dependencies not available: {e}")
    
    def test_invalid_config_handling(self):
        """Test handling of invalid configuration"""
        try:
            from narko import Config
            
            # Test invalid API key
            with pytest.raises(ValueError):
                Config(notion_api_key="", notion_import_root="valid_root")
            
            # Test invalid root
            with pytest.raises(ValueError):
                Config(notion_api_key="valid_key", notion_import_root="")
                
        except ImportError as e:
            pytest.skip(f"Dependencies not available: {e}")


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])