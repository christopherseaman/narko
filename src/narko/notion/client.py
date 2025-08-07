"""
Notion API client for page and block operations
"""
import requests
import logging
from typing import List, Dict, Any, Optional
from ..config import Config

logger = logging.getLogger(__name__)


class NotionClient:
    """Clean Notion API client focused on core operations"""
    
    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.notion_api_key
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": config.notion_version
        }
    
    def extract_page_id(self, url_or_id: str) -> str:
        """Extract page ID from Notion URL or return ID if already formatted"""
        if not url_or_id:
            return url_or_id
        
        import re
        # If it's already a UUID, return as-is
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if re.match(uuid_pattern, url_or_id, re.IGNORECASE):
            return url_or_id
        
        # Extract from URL - look for the UUID pattern in the URL
        uuid_match = re.search(r'([0-9a-f]{8}[0-9a-f]{4}[0-9a-f]{4}[0-9a-f]{4}[0-9a-f]{12})', url_or_id, re.IGNORECASE)
        if uuid_match:
            uuid_str = uuid_match.group(1)
            # Add dashes to make it a proper UUID
            return f"{uuid_str[0:8]}-{uuid_str[8:12]}-{uuid_str[12:16]}-{uuid_str[16:20]}-{uuid_str[20:32]}"
        
        return url_or_id
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get page information"""
        page_id = self.extract_page_id(page_id)
        response = requests.get(f"{self.base_url}/pages/{page_id}", headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get page: {response.status_code} - {response.text}")
    
    def create_page(self, parent_id: str, title: str, blocks: List[Dict], properties: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a page in Notion with blocks"""
        parent_id = self.extract_page_id(parent_id)
        
        # Validate all blocks before sending
        validated_blocks = self._validate_blocks(blocks[:100])  # Notion limit
        
        data = {
            "parent": {"page_id": parent_id},
            "properties": properties or {
                "title": {"title": [{"text": {"content": title}}]}
            },
            "children": validated_blocks
        }
        
        response = requests.post(f"{self.base_url}/pages", headers=self.headers, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            raise Exception(f"Failed to create page: {response.status_code} - {error_data}")
    
    def _validate_blocks(self, blocks: List[Dict]) -> List[Dict]:
        """Validate and clean blocks before sending to Notion"""
        validated = []
        
        for block in blocks:
            block_type = block.get('type')
            if not block_type:
                logger.warning("Block missing type, skipping")
                continue
            
            # Validate rich text content
            if block_type in block and 'rich_text' in block[block_type]:
                rich_text = block[block_type]['rich_text']
                for rt_item in rich_text:
                    if 'text' in rt_item and 'content' in rt_item['text']:
                        content = rt_item['text']['content']
                        if not isinstance(content, str):
                            rt_item['text']['content'] = str(content) if content else ""
            
            validated.append(block)
        
        return validated
    
    def append_blocks(self, block_id: str, blocks: List[Dict]) -> Dict[str, Any]:
        """Append blocks to an existing page or block"""
        block_id = self.extract_page_id(block_id)
        validated_blocks = self._validate_blocks(blocks[:100])
        
        data = {"children": validated_blocks}
        response = requests.patch(f"{self.base_url}/blocks/{block_id}/children", headers=self.headers, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            raise Exception(f"Failed to append blocks: {response.status_code} - {error_data}")
    
    def get_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """Get all blocks from a page recursively"""
        page_id = self.extract_page_id(page_id)
        all_blocks = []
        
        def fetch_blocks(block_id: str, start_cursor: Optional[str] = None) -> List[Dict]:
            params = {"page_size": 100}
            if start_cursor:
                params["start_cursor"] = start_cursor
            
            response = requests.get(
                f"{self.base_url}/blocks/{block_id}/children", 
                headers=self.headers, 
                params=params
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                raise Exception(f"Failed to get blocks: {response.status_code} - {error_data}")
            
            data = response.json()
            blocks = data.get('results', [])
            
            # Recursively fetch more pages if available
            if data.get('has_more'):
                blocks.extend(fetch_blocks(block_id, data.get('next_cursor')))
            
            return blocks
        
        all_blocks = fetch_blocks(page_id)
        return all_blocks
    
    def delete_blocks(self, block_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple blocks"""
        results = {"deleted": [], "errors": []}
        
        for block_id in block_ids:
            try:
                response = requests.delete(
                    f"{self.base_url}/blocks/{block_id}", 
                    headers=self.headers
                )
                if response.status_code == 200:
                    results["deleted"].append(block_id)
                else:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                    results["errors"].append({"block_id": block_id, "error": f"Status {response.status_code}: {error_data}"})
            except Exception as e:
                results["errors"].append({"block_id": block_id, "error": str(e)})
        
        return results
    
    def replace_all_blocks(self, page_id: str, new_blocks: List[Dict]) -> Dict[str, Any]:
        """Replace ALL blocks on a page with new blocks"""
        page_id = self.extract_page_id(page_id)
        
        try:
            # Step 1: Get all existing blocks
            existing_blocks = self.get_page_blocks(page_id)
            
            # Step 2: Delete all existing blocks
            if existing_blocks:
                block_ids = [block['id'] for block in existing_blocks]
                delete_result = self.delete_blocks(block_ids)
                
                if delete_result["errors"]:
                    logger.warning(f"Some blocks couldn't be deleted: {delete_result['errors']}")
            
            # Step 3: Add new blocks
            validated_blocks = self._validate_blocks(new_blocks[:100])
            data = {"children": validated_blocks}
            
            response = requests.patch(
                f"{self.base_url}/blocks/{page_id}/children", 
                headers=self.headers, 
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                result["mode"] = "replace_all"
                result["deleted_blocks"] = len(existing_blocks)
                result["added_blocks"] = len(validated_blocks)
                return result
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                raise Exception(f"Failed to add new blocks: {response.status_code} - {error_data}")
                
        except Exception as e:
            return {"error": f"Replace all blocks failed: {str(e)}"}
    
    def replace_content_blocks(self, page_id: str, new_blocks: List[Dict]) -> Dict[str, Any]:
        """Replace content blocks but preserve sub-pages (append new content below sub-pages)"""
        page_id = self.extract_page_id(page_id)
        
        try:
            # Step 1: Get all existing blocks
            existing_blocks = self.get_page_blocks(page_id)
            
            # Step 2: Identify content blocks vs sub-pages
            content_blocks = []
            subpage_blocks = []
            
            for block in existing_blocks:
                if block.get('type') == 'child_page':
                    subpage_blocks.append(block)
                else:
                    content_blocks.append(block)
            
            # Step 3: Delete only content blocks
            if content_blocks:
                content_block_ids = [block['id'] for block in content_blocks]
                delete_result = self.delete_blocks(content_block_ids)
                
                if delete_result["errors"]:
                    logger.warning(f"Some content blocks couldn't be deleted: {delete_result['errors']}")
            
            # Step 4: Add new blocks (they will appear before sub-pages)
            validated_blocks = self._validate_blocks(new_blocks[:100])
            data = {"children": validated_blocks}
            
            response = requests.patch(
                f"{self.base_url}/blocks/{page_id}/children", 
                headers=self.headers, 
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                result["mode"] = "replace_content"
                result["deleted_content_blocks"] = len(content_blocks)
                result["preserved_subpages"] = len(subpage_blocks)
                result["added_blocks"] = len(validated_blocks)
                return result
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                raise Exception(f"Failed to add new blocks: {response.status_code} - {error_data}")
                
        except Exception as e:
            return {"error": f"Replace content blocks failed: {str(e)}"}