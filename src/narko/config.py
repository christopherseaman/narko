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
    # Based on official Notion API docs: https://developers.notion.com/docs/working-with-files-and-media
    notion_supported_extensions: Set[str] = field(default_factory=lambda: {
        # Audio (from Notion docs)
        '.aac', '.adts', '.mid', '.midi', '.mp3', '.mpga', '.m4a', '.m4b', '.mp4',
        '.oga', '.ogg', '.wav', '.wma',
        # Documents (from Notion docs)
        '.pdf', '.txt', '.json', '.doc', '.dot', '.docx', '.dotx',
        '.xls', '.xlt', '.xla', '.xlsx', '.xltx',
        '.ppt', '.pot', '.pps', '.ppa', '.pptx', '.potx',
        # Images (from Notion docs)
        '.gif', '.heic', '.jpeg', '.jpg', '.png', '.svg', '.tif', '.tiff',
        '.webp', '.ico',
        # Video (from Notion docs)
        '.amv', '.asf', '.wmv', '.avi', '.f4v', '.flv', '.gifv',
        '.m4v', '.mkv', '.webm', '.mov', '.qt', '.mpeg'
    })

    # Extensions that need .txt suffix workaround (common text files not in Notion's list)
    unsupported_text_extensions: Set[str] = field(default_factory=lambda: {
        # Programming languages
        '.py', '.sh', '.bash', '.md', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.rb', '.go',
        '.rs', '.swift', '.kt', '.scala', '.r', '.m', '.mm',
        '.php', '.pl', '.lua', '.dart', '.elm', '.clj', '.ex', '.exs',
        # Config/data formats (not in Notion's supported list)
        '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.xml',
        '.env', '.properties', '.gitignore', '.editorconfig',
        # Web (not in supported list)
        '.html', '.css', '.scss', '.sass', '.less',
        # Database/query
        '.sql', '.graphql', '.proto',
        # Build/deploy
        '.dockerfile', '.makefile', '.gradle', '.cmake',
        # Documentation
        '.rst', '.adoc', '.tex'
    })

    # All file types we handle (supported + unsupported with workaround)
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
        '.md', '.html', '.css', '.js', '.ts', '.py', '.java', '.cpp', '.c', '.sh', '.bash'
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
    
    # MIME Type Mappings (from Notion API documentation)
    mime_type_mapping: Dict[str, str] = field(default_factory=lambda: {
        # Audio
        '.aac': 'audio/aac',
        '.adts': 'audio/aac',
        '.mid': 'audio/midi',
        '.midi': 'audio/midi',
        '.mp3': 'audio/mpeg',
        '.mpga': 'audio/mpeg',
        '.m4a': 'audio/mp4',
        '.m4b': 'audio/mp4',
        '.oga': 'audio/ogg',
        '.ogg': 'audio/ogg',
        '.wav': 'audio/wav',
        '.wma': 'audio/x-ms-wma',
        # Documents
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.json': 'application/json',
        '.doc': 'application/msword',
        '.dot': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.dotx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.template',
        '.xls': 'application/vnd.ms-excel',
        '.xlt': 'application/vnd.ms-excel',
        '.xla': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xltx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.template',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pot': 'application/vnd.ms-powerpoint',
        '.pps': 'application/vnd.ms-powerpoint',
        '.ppa': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.potx': 'application/vnd.openxmlformats-officedocument.presentationml.template',
        # Images
        '.gif': 'image/gif',
        '.heic': 'image/heic',
        '.jpeg': 'image/jpeg',
        '.jpg': 'image/jpeg',
        '.png': 'image/png',
        '.svg': 'image/svg+xml',
        '.tif': 'image/tiff',
        '.tiff': 'image/tiff',
        '.webp': 'image/webp',
        '.ico': 'image/vnd.microsoft.icon',
        # Video
        '.amv': 'video/x-amv',
        '.asf': 'video/x-ms-asf',
        '.wmv': 'video/x-ms-wmv',
        '.avi': 'video/x-msvideo',
        '.f4v': 'video/x-f4v',
        '.flv': 'video/x-flv',
        '.gifv': 'video/mp4',
        '.m4v': 'video/x-m4v',
        '.mp4': 'video/mp4',
        '.mkv': 'video/x-matroska',
        '.webm': 'video/webm',
        '.mov': 'video/quicktime',
        '.qt': 'video/quicktime',
        '.mpeg': 'video/mpeg'
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
        config.notion_supported_extensions = {
            '.aac', '.adts', '.mid', '.midi', '.mp3', '.mpga', '.m4a', '.m4b', '.mp4',
            '.oga', '.ogg', '.wav', '.wma',
            '.pdf', '.txt', '.json', '.doc', '.dot', '.docx', '.dotx',
            '.xls', '.xlt', '.xla', '.xlsx', '.xltx',
            '.ppt', '.pot', '.pps', '.ppa', '.pptx', '.potx',
            '.gif', '.heic', '.jpeg', '.jpg', '.png', '.svg', '.tif', '.tiff',
            '.webp', '.ico',
            '.amv', '.asf', '.wmv', '.avi', '.f4v', '.flv', '.gifv',
            '.m4v', '.mkv', '.webm', '.mov', '.qt', '.mpeg'
        }

        config.unsupported_text_extensions = {
            '.py', '.sh', '.bash', '.md', '.js', '.ts', '.jsx', '.tsx',
            '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.rb', '.go',
            '.rs', '.swift', '.kt', '.scala', '.r', '.m', '.mm',
            '.php', '.pl', '.lua', '.dart', '.elm', '.clj', '.ex', '.exs',
            '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.xml',
            '.env', '.properties', '.gitignore', '.editorconfig',
            '.html', '.css', '.scss', '.sass', '.less',
            '.sql', '.graphql', '.proto',
            '.dockerfile', '.makefile', '.gradle', '.cmake',
            '.rst', '.adoc', '.tex'
        }

        config.supported_file_types = {
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.ico',
            '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
            '.xls', '.xlsx', '.csv', '.ods',
            '.ppt', '.pptx', '.odp',
            '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg',
            '.mp3', '.wav', '.mp4', '.avi', '.mov', '.mkv', '.flv',
            '.zip', '.tar', '.gz', '.rar', '.7z',
            '.md', '.html', '.css', '.js', '.ts', '.py', '.java', '.cpp', '.c', '.sh', '.bash'
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
            '.md': 'text/markdown',
            '.py': 'text/x-python-script',
            '.sh': 'text/x-shellscript',
            '.bash': 'text/x-shellscript',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.html': 'text/html',
            '.css': 'text/css',
            '.csv': 'text/csv',
            '.yaml': 'text/x-yaml',
            '.yml': 'text/x-yaml'
        }
        
        return config
    
    def get_mime_type(self, file_extension: str) -> str:
        """Get Notion-compatible MIME type for file extension"""
        return self.mime_type_mapping.get(file_extension.lower(), 'application/octet-stream')
    
    def is_supported_file_type(self, file_extension: str) -> bool:
        """Check if file type is supported (either natively or with workaround)"""
        return file_extension.lower() in self.supported_file_types

    def needs_extension_workaround(self, file_extension: str) -> bool:
        """Check if file needs .txt extension workaround for Notion API"""
        return file_extension.lower() in self.unsupported_text_extensions

    def is_notion_native_support(self, file_extension: str) -> bool:
        """Check if file is natively supported by Notion without workaround"""
        return file_extension.lower() in self.notion_supported_extensions
    
    def is_embedding_enabled(self, file_extension: str) -> bool:
        """Check if file type supports embedding"""
        return file_extension.lower() in self.embedding_enabled_types