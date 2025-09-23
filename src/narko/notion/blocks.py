"""
Notion block building utilities

Provides utilities for building Notion API blocks from parsed content.
"""

from typing import Dict, List, Any, Optional


class NotionBlockBuilder:
    """Utility class for building Notion API blocks"""
    
    def __init__(self):
        pass
    
    def text_block(self, content: str, block_type: str = "paragraph") -> Dict[str, Any]:
        """Create a text block"""
        return {
            "type": block_type,
            block_type: {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": content
                        }
                    }
                ]
            }
        }
    
    def heading_block(self, content: str, level: int = 1) -> Dict[str, Any]:
        """Create a heading block"""
        heading_type = f"heading_{min(level, 3)}"
        return {
            "type": heading_type,
            heading_type: {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": content
                        }
                    }
                ]
            }
        }
    
    def code_block(self, content: str, language: str = "plain text") -> Dict[str, Any]:
        """Create a code block"""
        return {
            "type": "code",
            "code": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": content
                        }
                    }
                ],
                "language": language
            }
        }
    
    def bulleted_list_item(self, content: str) -> Dict[str, Any]:
        """Create a bulleted list item"""
        return {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": content
                        }
                    }
                ]
            }
        }
    
    def numbered_list_item(self, content: str) -> Dict[str, Any]:
        """Create a numbered list item"""
        return {
            "type": "numbered_list_item", 
            "numbered_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": content
                        }
                    }
                ]
            }
        }
    
    def quote_block(self, content: str) -> Dict[str, Any]:
        """Create a quote block"""
        return {
            "type": "quote",
            "quote": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": content
                        }
                    }
                ]
            }
        }
    
    def divider_block(self) -> Dict[str, Any]:
        """Create a divider block"""
        return {
            "type": "divider",
            "divider": {}
        }
    
    def image_block(self, url: str, caption: str = "") -> Dict[str, Any]:
        """Create an image block"""
        block = {
            "type": "image",
            "image": {
                "type": "external",
                "external": {
                    "url": url
                }
            }
        }
        
        if caption:
            block["image"]["caption"] = [
                {
                    "type": "text",
                    "text": {
                        "content": caption
                    }
                }
            ]
        
        return block
    
    def file_block(self, url: str, caption: str = "") -> Dict[str, Any]:
        """Create a file block"""
        block = {
            "type": "file",
            "file": {
                "type": "external", 
                "external": {
                    "url": url
                }
            }
        }
        
        if caption:
            block["file"]["caption"] = [
                {
                    "type": "text",
                    "text": {
                        "content": caption
                    }
                }
            ]
        
        return block