"""
narko - Notion extension and uploader for marko

A modular, clean markdown to Notion converter with file upload capabilities.
"""

__version__ = "2.0.0"
__author__ = "narko contributors"

# Always available imports (no external dependencies)
from .config import Config
from .utils import TextProcessor, EmbeddingGenerator

# Lazy imports for components with dependencies
def _lazy_import():
    """Lazy import function for components requiring external dependencies"""
    imports = {}
    
    try:
        from .utils import UploadCache, FileValidator
        imports['UploadCache'] = UploadCache
        imports['FileValidator'] = FileValidator
    except ImportError:
        pass
    
    try:
        from .extensions import NotionExtension
        imports['NotionExtension'] = NotionExtension
    except ImportError:
        pass
    
    try:
        from .notion import NotionClient, FileUploader, ExternalImporter
        imports['NotionClient'] = NotionClient
        imports['FileUploader'] = FileUploader
        imports['ExternalImporter'] = ExternalImporter
    except ImportError:
        pass
        
    try:
        from .converter import NotionConverter
        imports['NotionConverter'] = NotionConverter
    except ImportError:
        pass
        
    return imports

# Make lazy imports available at module level
_available_imports = _lazy_import()
globals().update(_available_imports)

# Add main function for CLI compatibility
def main():
    """Main entry point for CLI"""
    try:
        from .cli import main as cli_main
        return cli_main()
    except ImportError:
        # Fallback to direct execution
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from narko import main as fallback_main
        return fallback_main()

__all__ = [
    # Always available
    "Config",
    "TextProcessor", 
    "EmbeddingGenerator",
    "main",
    # Conditionally available (if dependencies present)
] + list(_available_imports.keys())