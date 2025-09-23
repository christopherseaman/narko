"""
Configuration and constants for narko
"""
import os
from pathlib import Path
from typing import Set, Dict, Any
from dataclasses import dataclass, field

# Load environment variables if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fall back to basic os.environ if dotenv not available
    pass

@dataclass
class Config:
    """Configuration for narko operations"""
    
    # API Configuration
    notion_api_key: str = field(default_factory=lambda: os.getenv('NOTION_API_KEY', ''))
    notion_import_root: str = field(default_factory=lambda: os.getenv('NOTION_IMPORT_ROOT', ''))
    notion_version: str = "2022-06-28"
    
    # File Upload Configuration
    max_file_size: int = 5 * 1024 * 1024  # 5MB
    max_batch_size: int = 10
    stream_chunk_size: int = 1024 * 1024  # 1MB
    max_concurrent_uploads: int = 5
    max_retries: int = 3
    base_retry_delay: float = 1.0
    
    # Cache Configuration
    cache_ttl_hours: int = 24
    cache_file: str = "upload_cache.json"
    compression_threshold: int = 1024 * 100  # 100KB
    
    # File Type Support
    supported_file_types: Set[str] = field(default_factory=lambda: {
        # Images
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.ico',
        # Documents  
        '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
        # Spreadsheets
        '.xls', '.xlsx', '.csv', '.ods',
        # Presentations
        '.ppt', '.pptx', '.odp',
        # Code and data
        '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg',
        # Media
        '.mp3', '.wav', '.mp4', '.avi', '.mov', '.mkv', '.flv',
        # Archives
        '.zip', '.tar', '.gz', '.rar', '.7z',
        # Other
        '.md', '.html', '.css', '.js', '.ts', '.py', '.java', '.cpp', '.c'
    })
    
    embedding_enabled_types: Set[str] = field(default_factory=lambda: {
        '.txt', '.md', '.py', '.js', '.json', '.csv', '.xml', '.html'
    })
    
    text_extraction_types: Set[str] = field(default_factory=lambda: {
        '.pdf', '.doc', '.docx', '.txt', '.md', '.rtf'
    })
    
    image_analysis_types: Set[str] = field(default_factory=lambda: {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'
    })
    
    # MIME Type Mappings (Notion-compatible)
    mime_type_mapping: Dict[str, str] = field(default_factory=lambda: {
        '.txt': 'text/plain',
        '.md': 'text/plain',  # Notion treats markdown as plain text
        '.py': 'text/plain',  # Python files as plain text
        '.js': 'text/plain',  # JavaScript as plain text
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.html': 'text/html',
        '.css': 'text/plain',  # CSS as plain text
        '.csv': 'text/csv',
        '.yaml': 'text/plain',
        '.yml': 'text/plain'
    })
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.notion_api_key:
            raise ValueError("NOTION_API_KEY is required")
        
        if not self.notion_import_root:
            raise ValueError("NOTION_IMPORT_ROOT is required")
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables"""
        return cls()
    
    @classmethod  
    def create_minimal(cls) -> 'Config':
        """Create minimal config for testing (doesn't require env vars)"""
        config = cls.__new__(cls)  # Create without calling __init__
        config.notion_api_key = 'test_key'
        config.notion_import_root = 'test_root'
        config.notion_version = "2022-06-28"
        config.max_file_size = 5 * 1024 * 1024
        config.max_batch_size = 10
        config.stream_chunk_size = 1024 * 1024
        config.max_concurrent_uploads = 5
        config.max_retries = 3
        config.base_retry_delay = 1.0
        config.cache_ttl_hours = 24
        config.cache_file = "upload_cache.json"
        config.compression_threshold = 1024 * 100
        
        # Set default collections
        config.supported_file_types = {
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.ico',
            '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
            '.xls', '.xlsx', '.csv', '.ods',
            '.ppt', '.pptx', '.odp',
            '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg',
            '.mp3', '.wav', '.mp4', '.avi', '.mov', '.mkv', '.flv',
            '.zip', '.tar', '.gz', '.rar', '.7z',
            '.md', '.html', '.css', '.js', '.ts', '.py', '.java', '.cpp', '.c'
        }
        
        config.embedding_enabled_types = {
            '.txt', '.md', '.py', '.js', '.json', '.csv', '.xml', '.html'
        }
        
        config.text_extraction_types = {
            '.pdf', '.doc', '.docx', '.txt', '.md', '.rtf'
        }
        
        config.image_analysis_types = {
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'
        }
        
        config.mime_type_mapping = {
            '.txt': 'text/plain',
            '.md': 'text/plain',
            '.py': 'text/plain', 
            '.js': 'text/plain',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.html': 'text/html',
            '.css': 'text/plain',
            '.csv': 'text/csv',
            '.yaml': 'text/plain',
            '.yml': 'text/plain'
        }
        
        return config
    
    def get_mime_type(self, file_extension: str) -> str:
        """Get Notion-compatible MIME type for file extension"""
        return self.mime_type_mapping.get(file_extension.lower(), 'application/octet-stream')
    
    def is_supported_file_type(self, file_extension: str) -> bool:
        """Check if file type is supported"""
        return file_extension.lower() in self.supported_file_types
    
    def is_embedding_enabled(self, file_extension: str) -> bool:
        """Check if file type supports embedding"""
        return file_extension.lower() in self.embedding_enabled_types