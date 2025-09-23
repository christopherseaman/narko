"""
Pytest configuration and shared fixtures for narko testing suite.
"""
import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
import requests

# Test configuration
TEST_DIR = Path(__file__).parent
FIXTURES_DIR = TEST_DIR / "fixtures"
SAMPLE_FILES_DIR = FIXTURES_DIR / "sample_files"

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_notion_api():
    """Mock Notion API responses."""
    with patch('requests.post') as mock_post, \
         patch('requests.get') as mock_get:
        
        # Mock successful file upload creation
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "id": "test-file-id-123",
            "upload_url": "https://test-upload-url.com",
            "name": "test_file.png",
            "size": 1024
        }
        
        yield {
            'post': mock_post,
            'get': mock_get
        }

@pytest.fixture
def sample_image_file(temp_dir):
    """Create a sample image file for testing."""
    # Create a minimal PNG file (1x1 transparent pixel)
    png_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13'
        b'\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```'
        b'\x00\x00\x00\x02\x00\x01H\xafDe\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    
    file_path = temp_dir / "test_image.png"
    file_path.write_bytes(png_data)
    return file_path

@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file for testing."""
    file_path = temp_dir / "test_document.txt"
    file_path.write_text("This is a test document for file upload testing.")
    return file_path

@pytest.fixture
def large_file(temp_dir):
    """Create a large file for performance testing."""
    file_path = temp_dir / "large_file.dat"
    # Create 4MB file (under 5MB limit)
    with open(file_path, 'wb') as f:
        f.write(b'x' * (4 * 1024 * 1024))
    return file_path

@pytest.fixture
def oversized_file(temp_dir):
    """Create an oversized file for limit testing."""
    file_path = temp_dir / "oversized_file.dat"
    # Create 6MB file (over 5MB limit)
    with open(file_path, 'wb') as f:
        f.write(b'x' * (6 * 1024 * 1024))
    return file_path

@pytest.fixture
def empty_file(temp_dir):
    """Create an empty file for edge case testing."""
    file_path = temp_dir / "empty_file.txt"
    file_path.touch()
    return file_path

@pytest.fixture
def unicode_filename_file(temp_dir):
    """Create a file with Unicode characters in name."""
    file_path = temp_dir / "测试文件_🚀.txt"
    file_path.write_text("Unicode filename test file")
    return file_path

@pytest.fixture
def markdown_with_uploads():
    """Sample markdown content with file upload syntax."""
    return """# Test Document

## External Files
![image](https://via.placeholder.com/400x300.png)
![pdf](https://example.com/document.pdf)

## Local Files
![file](./test_image.png)
![image:Test Image](./test_image.png)
![video:Demo Video](./demo.mp4)

## Combined Content
> [!TIP]
> This callout has an image:
> ![image](./inline_image.png)

- [x] Task with file: ![file](./task_file.pdf)
- [ ] Another task

$$
\\text{Math with file reference: } f(x) = \\int_{-\\infty}^{\\infty} e^{-x^2} dx
$$
"""

@pytest.fixture
def notion_blocks_sample():
    """Sample expected Notion blocks structure."""
    return [
        {
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": "Test Document"}}]
            }
        },
        {
            "type": "image",
            "image": {
                "type": "external",
                "external": {"url": "https://via.placeholder.com/400x300.png"},
                "caption": []
            }
        }
    ]

@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'NOTION_API_KEY': 'test_api_key_' + 'x' * 40,
        'NOTION_IMPORT_ROOT': 'test-page-id-123'
    }):
        yield

@pytest.fixture
def api_error_responses():
    """Common API error response patterns."""
    return {
        'unauthorized': {
            'status_code': 401,
            'json': {'message': 'Unauthorized'}
        },
        'rate_limited': {
            'status_code': 429,
            'json': {'message': 'Rate limited'}
        },
        'not_found': {
            'status_code': 404,
            'json': {'message': 'Not found'}
        },
        'invalid_file': {
            'status_code': 400,
            'json': {'message': 'Invalid file type'}
        }
    }

# Performance testing fixtures
@pytest.fixture
def performance_metrics():
    """Initialize performance metrics tracking."""
    return {
        'processing_times': [],
        'memory_usage': [],
        'api_call_times': []
    }

# Security testing fixtures
@pytest.fixture
def malicious_filename_file(temp_dir):
    """Create file with potentially malicious filename."""
    file_path = temp_dir / "../../../etc/passwd"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("malicious content")
    return file_path

@pytest.fixture
def setup_test_logging():
    """Configure logging for tests."""
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('narko.tests')

# Test markers for categorizing tests
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.performance = pytest.mark.performance
pytest.mark.security = pytest.mark.security