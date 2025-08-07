"""
NotionConverter - Convert Marko AST to Notion blocks
"""
import re
import os
import mimetypes
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from marko import element
from .config import Config
from .notion.uploader import FileUploader, ExternalImporter


class NotionConverter:
    """Convert Marko AST to Notion blocks with file upload support"""
    
    def __init__(self, config: Config, file_uploader: FileUploader, external_importer: ExternalImporter):
        self.config = config
        self.file_uploader = file_uploader
        self.external_importer = external_importer
    
    def convert(self, ast) -> List[Dict[str, Any]]:
        """Convert Marko AST to Notion blocks"""
        blocks = []
        
        for child in ast.children:
            block_data = self._convert_node(child)
            if block_data:
                if isinstance(block_data, list):
                    blocks.extend(block_data)
                else:
                    blocks.append(block_data)
        
        return blocks
    
    def _convert_node(self, node) -> Optional[Dict[str, Any]]:
        """Convert a single AST node to Notion block(s)"""
        node_type = type(node).__name__
        
        # Handle different node types
        if node_type == 'Paragraph':
            return self._convert_paragraph(node)
        elif node_type == 'Heading':
            return self._convert_heading(node)
        elif node_type == 'CodeBlock':
            return self._convert_code_block(node)
        elif node_type == 'FencedCode':
            return self._convert_fenced_code(node)
        elif node_type == 'List':
            return self._convert_list(node)
        elif node_type == 'ListItem':
            return self._convert_list_item(node)
        elif node_type == 'Quote':
            return self._convert_quote(node)
        elif node_type == 'ThematicBreak':
            return {"type": "divider", "divider": {}}
        elif node_type == 'Image':
            return self._convert_image(node)
        elif node_type == 'Link':
            return self._convert_link_as_embed(node)
        elif node_type == 'HTMLBlock':
            return self._convert_html_block(node)
        
        # Handle custom extension nodes
        elif node_type == 'MathBlock':
            return self._convert_math_block(node)
        elif node_type == 'CalloutBlock':
            return self._convert_callout_block(node)
        elif node_type == 'TaskListItem':
            return self._convert_task_list_item(node)
        elif node_type == 'FileUploadBlock':
            return self._convert_file_upload_block(node)
        
        # Fallback for unknown nodes - convert to paragraph
        else:
            return self._convert_unknown_node(node)
    
    def _convert_paragraph(self, node) -> Dict[str, Any]:
        """Convert paragraph to Notion paragraph block"""
        rich_text = self._extract_rich_text(node.children)
        
        return {
            "type": "paragraph",
            "paragraph": {
                "rich_text": rich_text
            }
        }
    
    def _convert_heading(self, node) -> Dict[str, Any]:
        """Convert heading to Notion heading block"""
        level = min(node.level, 3)  # Notion supports h1, h2, h3
        heading_type = f"heading_{level}"
        
        rich_text = self._extract_rich_text(node.children)
        
        return {
            "type": heading_type,
            heading_type: {
                "rich_text": rich_text
            }
        }
    
    def _convert_code_block(self, node) -> Dict[str, Any]:
        """Convert code block to Notion code block"""
        language = getattr(node, 'lang', '') or 'plain text'
        
        return {
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": node.children[0].children}}],
                "language": language.lower()
            }
        }
    
    def _convert_fenced_code(self, node) -> Dict[str, Any]:
        """Convert fenced code block to Notion code block"""
        language = getattr(node, 'lang', '') or 'plain text'
        content = getattr(node, 'children', '') or str(node)
        
        return {
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": content}}],
                "language": language.lower()
            }
        }
    
    def _convert_list(self, node) -> List[Dict[str, Any]]:
        """Convert list to Notion list items"""
        blocks = []
        is_ordered = getattr(node, 'ordered', False)
        
        for item in node.children:
            block = self._convert_list_item(item, is_ordered)
            if block:
                blocks.append(block)
        
        return blocks
    
    def _convert_list_item(self, node, is_ordered: bool = False) -> Dict[str, Any]:
        """Convert list item to Notion list item block"""
        list_type = "numbered_list_item" if is_ordered else "bulleted_list_item"
        
        # Extract rich text from the first paragraph if exists
        rich_text = []
        children = []
        
        for child in node.children:
            if type(child).__name__ == 'Paragraph':
                rich_text.extend(self._extract_rich_text(child.children))
            else:
                # Handle nested items
                child_block = self._convert_node(child)
                if child_block:
                    children.append(child_block)
        
        block = {
            "type": list_type,
            list_type: {
                "rich_text": rich_text
            }
        }
        
        if children:
            block[list_type]["children"] = children
        
        return block
    
    def _convert_quote(self, node) -> Dict[str, Any]:
        """Convert quote to Notion quote block"""
        rich_text = []
        
        for child in node.children:
            if type(child).__name__ == 'Paragraph':
                rich_text.extend(self._extract_rich_text(child.children))
        
        return {
            "type": "quote",
            "quote": {
                "rich_text": rich_text
            }
        }
    
    def _convert_image(self, node) -> Dict[str, Any]:
        """Convert image to Notion image block"""
        url = node.dest
        title = getattr(node, 'title', '') or ''
        alt = self._extract_plain_text(node.children)
        
        # Handle local files vs URLs
        if self._is_local_file(url):
            # Upload local file
            try:
                upload_result = self.file_uploader.upload_file(url)
                if upload_result and 'id' in upload_result:
                    return {
                        "type": "image",
                        "image": {
                            "type": "file_upload",
                            "file_upload": {"id": upload_result['id']},
                            "caption": [{"type": "text", "text": {"content": title or alt}}] if (title or alt) else []
                        }
                    }
            except Exception as e:
                print(f"Failed to upload image {url}: {e}")
                return self._create_text_block(f"[Image upload failed: {url}]")
        else:
            # External image
            return {
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {"url": url},
                    "caption": [{"type": "text", "text": {"content": title or alt}}] if (title or alt) else []
                }
            }
    
    def _convert_link_as_embed(self, node) -> Optional[Dict[str, Any]]:
        """Convert standalone links to embeds when appropriate"""
        url = node.dest
        text = self._extract_plain_text(node.children)
        
        # Only create embeds for standalone links (not inline)
        if self._is_embeddable_url(url):
            return {
                "type": "embed",
                "embed": {"url": url}
            }
        
        # Return None for inline links (handled in rich text)
        return None
    
    def _convert_html_block(self, node) -> Dict[str, Any]:
        """Convert HTML block to Notion paragraph"""
        content = getattr(node, 'children', str(node))
        
        return {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        }
    
    # Custom extension converters
    
    def _convert_math_block(self, node) -> Dict[str, Any]:
        """Convert math block to Notion equation block"""
        content = getattr(node, 'content', '')
        
        return {
            "type": "equation",
            "equation": {
                "expression": content.strip()
            }
        }
    
    def _convert_callout_block(self, node) -> Dict[str, Any]:
        """Convert callout block to Notion callout block"""
        callout_type = getattr(node, 'callout_type', 'info').lower()
        title = getattr(node, 'title', '')
        
        # Map callout types to Notion callout icons
        icon_map = {
            'note': '📝',
            'info': 'ℹ️',
            'tip': '💡',
            'warning': '⚠️',
            'danger': '🚨',
            'success': '✅'
        }
        
        icon = icon_map.get(callout_type, 'ℹ️')
        
        # Extract content from children
        rich_text = []
        if hasattr(node, 'children'):
            for child in node.children:
                if type(child).__name__ == 'Paragraph':
                    rich_text.extend(self._extract_rich_text(child.children))
        
        # Prepend title if present
        if title:
            rich_text.insert(0, {
                "type": "text",
                "text": {"content": f"{title}: "},
                "annotations": {"bold": True}
            })
        
        return {
            "type": "callout",
            "callout": {
                "rich_text": rich_text,
                "icon": {"type": "emoji", "emoji": icon}
            }
        }
    
    def _convert_task_list_item(self, node) -> Dict[str, Any]:
        """Convert task list item to Notion to-do block"""
        checked = getattr(node, 'checked', False)
        
        rich_text = []
        if hasattr(node, 'children'):
            for child in node.children:
                if type(child).__name__ == 'Paragraph':
                    rich_text.extend(self._extract_rich_text(child.children))
        
        return {
            "type": "to_do",
            "to_do": {
                "rich_text": rich_text,
                "checked": checked
            }
        }
    
    def _convert_file_upload_block(self, node) -> Dict[str, Any]:
        """Convert file upload block to appropriate Notion block"""
        file_path = getattr(node, 'file_path', '')
        file_type = getattr(node, 'file_type', 'file')
        title = getattr(node, 'title', '')
        
        # Handle local files vs URLs
        if self._is_local_file(file_path):
            try:
                if file_type in ['image', 'video', 'audio', 'pdf']:
                    # Upload specific file types
                    upload_result = self.file_uploader.upload_file(file_path)
                    if upload_result and 'id' in upload_result:
                        return {
                            "type": file_type,
                            file_type: {
                                "type": "file_upload",
                                "file_upload": {"id": upload_result['id']},
                                "caption": [{"type": "text", "text": {"content": title}}] if title else []
                            }
                        }
                else:
                    # Generic file upload
                    upload_result = self.file_uploader.upload_file(file_path)
                    if upload_result and 'id' in upload_result:
                        return {
                            "type": "file",
                            "file": {
                                "type": "file_upload",
                                "file_upload": {"id": upload_result['id']},
                                "caption": [{"type": "text", "text": {"content": title}}] if title else []
                            }
                        }
            except Exception as e:
                print(f"Failed to upload file {file_path}: {e}")
                return self._create_text_block(f"[File upload failed: {file_path}]")
        else:
            # External file/URL
            return {
                "type": file_type,
                file_type: {
                    "type": "external",
                    "external": {"url": file_path},
                    "caption": [{"type": "text", "text": {"content": title}}] if title else []
                }
            }
    
    def _convert_unknown_node(self, node) -> Dict[str, Any]:
        """Convert unknown node to text paragraph"""
        content = str(node)[:500]  # Truncate long content
        
        return {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": f"[Unknown node: {content}]"}}]
            }
        }
    
    # Helper methods
    
    def _extract_rich_text(self, children) -> List[Dict[str, Any]]:
        """Extract rich text from AST children"""
        rich_text = []
        
        for child in children:
            text_data = self._extract_text_data(child)
            if text_data:
                rich_text.append(text_data)
        
        return rich_text
    
    def _extract_text_data(self, node) -> Optional[Dict[str, Any]]:
        """Extract text data from a single node"""
        node_type = type(node).__name__
        
        if node_type == 'RawText':
            return {
                "type": "text",
                "text": {"content": node.children}
            }
        elif node_type == 'Emphasis':
            content = self._extract_plain_text([node])
            return {
                "type": "text",
                "text": {"content": content},
                "annotations": {"italic": True}
            }
        elif node_type == 'StrongEmphasis':
            content = self._extract_plain_text([node])
            return {
                "type": "text",
                "text": {"content": content},
                "annotations": {"bold": True}
            }
        elif node_type == 'InlineCode':
            return {
                "type": "text",
                "text": {"content": node.children},
                "annotations": {"code": True}
            }
        elif node_type == 'Link':
            content = self._extract_plain_text(node.children)
            return {
                "type": "text",
                "text": {
                    "content": content,
                    "link": {"url": node.dest}
                }
            }
        elif node_type == 'Image':
            alt_text = self._extract_plain_text(node.children)
            return {
                "type": "text",
                "text": {"content": f"[Image: {alt_text or node.dest}]"}
            }
        
        # Handle custom inline extensions
        elif node_type == 'InlineMath':
            content = getattr(node, 'content', '')
            return {
                "type": "equation",
                "equation": {"expression": content}
            }
        elif node_type == 'Highlight':
            content = self._extract_plain_text(node.children if hasattr(node, 'children') else [node])
            return {
                "type": "text",
                "text": {"content": content},
                "annotations": {"color": "yellow_background"}
            }
        
        # Fallback
        else:
            content = str(node)
            if content.strip():
                return {
                    "type": "text", 
                    "text": {"content": content}
                }
        
        return None
    
    def _extract_plain_text(self, children) -> str:
        """Extract plain text content from AST children"""
        text = ""
        
        for child in children:
            if hasattr(child, 'children'):
                if isinstance(child.children, str):
                    text += child.children
                else:
                    text += self._extract_plain_text(child.children)
            else:
                text += str(child)
        
        return text
    
    def _is_local_file(self, path: str) -> bool:
        """Check if path is a local file"""
        return not path.startswith(('http://', 'https://')) and os.path.exists(path)
    
    def _is_embeddable_url(self, url: str) -> bool:
        """Check if URL should be embedded"""
        embeddable_domains = [
            'youtube.com', 'youtu.be', 'vimeo.com',
            'twitter.com', 'x.com',
            'github.com', 'gist.github.com',
            'codepen.io', 'jsfiddle.net'
        ]
        
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in embeddable_domains)
    
    def _create_text_block(self, content: str) -> Dict[str, Any]:
        """Create a simple text block"""
        return {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        }