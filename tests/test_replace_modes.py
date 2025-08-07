"""
Test the new replace modes functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from narko.notion.client import NotionClient
from narko.config import Config

@pytest.fixture
def mock_config():
    """Mock configuration"""
    config = Mock(spec=Config)
    config.notion_api_key = "test_api_key"
    config.notion_version = "2022-06-28"
    return config

@pytest.fixture 
def notion_client(mock_config):
    """Create NotionClient instance with mocked config"""
    return NotionClient(mock_config)

class TestReplaceModes:
    """Test new replace functionality"""
    
    @patch('requests.get')
    def test_get_page_blocks_success(self, mock_get, notion_client):
        """Test getting page blocks successfully"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {'id': 'block-1', 'type': 'paragraph'},
                {'id': 'block-2', 'type': 'heading_1'},
                {'id': 'block-3', 'type': 'child_page'}
            ],
            'has_more': False
        }
        mock_get.return_value = mock_response
        
        blocks = notion_client.get_page_blocks('test-page-id')
        
        assert len(blocks) == 3
        assert blocks[0]['id'] == 'block-1'
        assert blocks[2]['type'] == 'child_page'
    
    @patch('requests.delete')
    def test_delete_blocks_success(self, mock_delete, notion_client):
        """Test deleting blocks successfully"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response
        
        result = notion_client.delete_blocks(['block-1', 'block-2'])
        
        assert len(result['deleted']) == 2
        assert len(result['errors']) == 0
        assert mock_delete.call_count == 2
    
    @patch('requests.delete')
    def test_delete_blocks_with_errors(self, mock_delete, notion_client):
        """Test deleting blocks with some failures"""
        def mock_delete_response(url, **kwargs):
            mock_response = Mock()
            if 'block-1' in url:
                mock_response.status_code = 200
            else:
                mock_response.status_code = 404
                mock_response.json.return_value = {'message': 'Block not found'}
                mock_response.headers = {'content-type': 'application/json'}
            return mock_response
        
        mock_delete.side_effect = mock_delete_response
        
        result = notion_client.delete_blocks(['block-1', 'block-2'])
        
        assert len(result['deleted']) == 1
        assert len(result['errors']) == 1
        assert result['errors'][0]['block_id'] == 'block-2'
    
    @patch('requests.patch')
    @patch('narko.notion.client.NotionClient.delete_blocks') 
    @patch('narko.notion.client.NotionClient.get_page_blocks')
    def test_replace_all_blocks_success(self, mock_get_blocks, mock_delete, mock_patch, notion_client):
        """Test replace all blocks functionality"""
        # Setup mocks
        mock_get_blocks.return_value = [
            {'id': 'old-block-1', 'type': 'paragraph'},
            {'id': 'old-block-2', 'type': 'child_page'}
        ]
        mock_delete.return_value = {'deleted': ['old-block-1', 'old-block-2'], 'errors': []}
        
        # Mock the PATCH request for adding new blocks
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'results': [{'id': 'new-block-1'}]}
        mock_patch.return_value = mock_response
        
        new_blocks = [{'type': 'paragraph', 'paragraph': {'rich_text': [{'text': {'content': 'New content'}}]}}]
        
        result = notion_client.replace_all_blocks('test-page-id', new_blocks)
        
        assert result['mode'] == 'replace_all'
        assert result['deleted_blocks'] == 2
        assert result['added_blocks'] == 1
        mock_get_blocks.assert_called_once()
        mock_delete.assert_called_once_with(['old-block-1', 'old-block-2'])
        mock_patch.assert_called_once()
    
    @patch('requests.patch')
    @patch('narko.notion.client.NotionClient.delete_blocks')
    @patch('narko.notion.client.NotionClient.get_page_blocks')
    def test_replace_content_blocks_preserves_subpages(self, mock_get_blocks, mock_delete, mock_patch, notion_client):
        """Test replace content blocks preserves sub-pages"""
        # Setup mocks - mix of content and sub-pages
        mock_get_blocks.return_value = [
            {'id': 'content-1', 'type': 'paragraph'},
            {'id': 'content-2', 'type': 'heading_1'}, 
            {'id': 'subpage-1', 'type': 'child_page'},
            {'id': 'content-3', 'type': 'bulleted_list_item'},
            {'id': 'subpage-2', 'type': 'child_page'}
        ]
        mock_delete.return_value = {'deleted': ['content-1', 'content-2', 'content-3'], 'errors': []}
        
        # Mock the PATCH request for adding new blocks
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'results': [{'id': 'new-content-1'}]}
        mock_patch.return_value = mock_response
        
        new_blocks = [{'type': 'paragraph', 'paragraph': {'rich_text': [{'text': {'content': 'New content'}}]}}]
        
        result = notion_client.replace_content_blocks('test-page-id', new_blocks)
        
        assert result['mode'] == 'replace_content'
        assert result['deleted_content_blocks'] == 3  # Only content blocks deleted
        assert result['preserved_subpages'] == 2     # Sub-pages preserved
        assert result['added_blocks'] == 1
        
        # Verify only content blocks were deleted (not sub-pages)
        delete_call_args = mock_delete.call_args[0][0]
        assert 'content-1' in delete_call_args
        assert 'content-2' in delete_call_args  
        assert 'content-3' in delete_call_args
        assert 'subpage-1' not in delete_call_args
        assert 'subpage-2' not in delete_call_args

class TestCLIIntegration:
    """Test CLI integration with new modes"""
    
    def test_import_mode_detection(self):
        """Test that CLI correctly detects import modes"""
        from run_narko import main
        
        # Test that the argument parser supports new modes
        # This would require more complex setup to test the full CLI
        # For now, we verify the methods exist
        from narko.notion.client import NotionClient
        
        assert hasattr(NotionClient, 'get_page_blocks')
        assert hasattr(NotionClient, 'delete_blocks') 
        assert hasattr(NotionClient, 'replace_all_blocks')
        assert hasattr(NotionClient, 'replace_content_blocks')

if __name__ == "__main__":
    pytest.main([__file__])