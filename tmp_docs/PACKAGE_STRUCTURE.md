# narko Package Structure

## Overview

The narko package has been successfully restructured to work with standard Python packaging tools instead of UV. The package now supports both basic functionality (without dependencies) and full functionality (with all dependencies installed).

## Fixed Issues

### 1. Removed UV Dependency
- **Before**: `#!/usr/bin/env -S uv run --script`
- **After**: `#!/usr/bin/env python3`
- **Impact**: Can now be used with standard Python virtual environments

### 2. Created Missing Text Processor Module
- **Issue**: `ModuleNotFoundError: No module named 'narko.utils.text'`
- **Solution**: Created comprehensive `TextProcessor` class with:
  - Basic text cleaning (`clean_text()`)
  - Advanced markdown analysis
  - Code content extraction
  - Keyword extraction
  - Content summarization

### 3. Created Missing Embedding Generator Module
- **Issue**: `ModuleNotFoundError: No module named 'narko.utils.embedding'`
- **Solution**: Created full `EmbeddingGenerator` class with:
  - Mock embedding generation
  - File metadata extraction
  - Similarity calculation
  - Content clustering
  - Caching support

### 4. Fixed Import Dependencies
- **Issue**: Lazy imports to handle missing dependencies gracefully
- **Solution**: Core functionality (Config, TextProcessor, EmbeddingGenerator) works without dependencies
- **Benefit**: Package can be partially used even without marko, requests, etc.

### 5. Added Proper Packaging Files
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Modern Python packaging configuration
- `setup.py` - Traditional Python packaging support
- `MANIFEST.in` - Include/exclude files for packaging
- `.env.example` - Configuration template

## Package Structure

```
narko/
├── src/narko/                    # Main package source
│   ├── __init__.py              # Package init with lazy imports
│   ├── cli.py                   # Command line interface
│   ├── config.py                # Configuration management
│   ├── converter.py             # Markdown to Notion converter
│   ├── extensions/              # Marko extensions
│   │   ├── __init__.py
│   │   ├── extension.py         # Main NotionExtension
│   │   ├── blocks.py            # Block-level extensions
│   │   └── inline.py            # Inline extensions
│   ├── notion/                  # Notion API components
│   │   ├── __init__.py
│   │   ├── client.py            # NotionClient API wrapper
│   │   └── uploader.py          # File upload functionality
│   ├── utils/                   # Utility modules
│   │   ├── __init__.py
│   │   ├── cache.py             # Upload caching
│   │   ├── validation.py        # File validation
│   │   ├── text.py              # Text processing (NEW)
│   │   └── embedding.py         # Embedding generation (NEW)
│   └── tests/                   # Unit tests
├── scripts/                     # Setup and test scripts
│   ├── test_package.py          # Package structure tests
│   ├── install_dev.py           # Development setup
│   └── install_and_test.py      # Complete installation
├── docs/                        # Documentation
│   ├── INSTALLATION.md          # Installation guide
│   └── PACKAGE_STRUCTURE.md     # This file
├── requirements.txt             # Dependencies
├── pyproject.toml              # Modern packaging
├── setup.py                    # Traditional packaging
├── MANIFEST.in                 # Package manifest
├── .env.example                # Configuration template
└── narko.py                    # Original script (now calls CLI)
```

## Installation Methods

### Method 1: Development Installation (Recommended)
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Or with all dependencies
pip install -e .[dev,test]
```

### Method 2: Using Installation Script
```bash
python3 scripts/install_and_test.py
```

### Method 3: Manual Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

## Usage Examples

### Basic Usage (After Installation)
```bash
# Use new CLI command
narko --file document.md --test

# Import to Notion
narko --file document.md --import

# Validate files
narko --validate "*.md"

# Show help
narko --help
```

### Programmatic Usage
```python
from narko import Config, TextProcessor, EmbeddingGenerator

# Create minimal config (for testing)
config = Config.create_minimal()

# Or create from environment
try:
    config = Config.from_env()  # Requires .env file
except ValueError:
    config = Config.create_minimal()

# Use utilities
text_proc = TextProcessor(config)
clean = text_proc.clean_text("  Hello   World  ")

embed_gen = EmbeddingGenerator(config)
metadata = embed_gen.extract_metadata("somefile.py")
```

### With Full Dependencies
```python
# After pip install -r requirements.txt
from narko import NotionClient, NotionExtension, NotionConverter
from marko import Markdown

# Full functionality available
markdown = Markdown(extensions=[NotionExtension])
client = NotionClient(config)
# ... etc
```

## Key Features

### Modular Architecture
- Clean separation of concerns
- Each module has specific responsibility
- Optional dependencies handled gracefully

### Lazy Loading
- Core functionality works without external dependencies
- Advanced features loaded only when dependencies available
- Graceful degradation

### Configuration Management
- Environment-based configuration
- Fallback to minimal config for testing
- Type validation and defaults

### Comprehensive Testing
- Package structure validation
- Basic functionality tests
- Dependency-aware testing
- Installation verification

### Standard Python Packaging
- Works with pip, venv, virtualenv
- Supports editable installation
- Proper dependency management
- Entry point scripts

## Migration Guide

### From UV Version
1. **Remove UV**: No longer needed
2. **Install normally**: `pip install -e .`
3. **Use CLI**: `narko` instead of `python narko.py`
4. **Same functionality**: All features preserved

### Environment Setup
1. **Copy configuration**: `cp .env.example .env`
2. **Set variables**: Edit `.env` with your Notion API key and page ID
3. **Test installation**: `python scripts/test_package.py`

## Testing

### Package Structure Test
```bash
python3 scripts/test_package.py
```

### Complete Installation Test
```bash
python3 scripts/install_and_test.py
```

### Unit Tests (After Dependencies)
```bash
pytest src/narko/tests/ -v
```

## Dependencies

### Runtime Dependencies
- marko[gfm] >= 2.0.0 (Markdown parsing)
- requests >= 2.28.0 (HTTP client)
- python-dotenv >= 0.19.0 (Environment variables)
- aiohttp >= 3.8.0 (Async HTTP)
- aiofiles >= 22.1.0 (Async file operations)

### Development Dependencies
- pytest >= 7.0.0 (Testing)
- pytest-asyncio >= 0.21.0 (Async testing)
- pytest-cov >= 4.0.0 (Coverage)
- black >= 22.0.0 (Formatting)
- flake8 >= 5.0.0 (Linting)
- mypy >= 1.0.0 (Type checking)

## Status

✅ **Package structure**: Working  
✅ **Basic imports**: Working  
✅ **Core functionality**: Working  
✅ **Configuration**: Working  
✅ **Utilities**: Working  
🔄 **Full functionality**: Requires dependencies  
✅ **Installation scripts**: Working  
✅ **Documentation**: Complete  

The narko package is now ready for standard Python development workflows!