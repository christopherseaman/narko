# narko Installation Guide

## Standard Python Installation (Recommended)

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Quick Installation

1. **Clone or download the narko project:**
   ```bash
   git clone <repository-url>
   cd narko
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install narko package:**
   ```bash
   # Install from source in development mode
   pip install -e .
   
   # Or install with all development dependencies
   pip install -e .[dev,test]
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Notion API key and settings
   ```

5. **Verify installation:**
   ```bash
   narko --help
   narko --validate "*.md"  # Test with existing markdown files
   ```

### Alternative Installation Methods

#### Using requirements.txt
```bash
pip install -r requirements.txt
python -m pip install -e .
```

#### Development Installation
```bash
python scripts/install_dev.py
```

## Configuration

### Required Configuration
Create a `.env` file with:
```env
NOTION_API_KEY=your_notion_api_key_here
NOTION_IMPORT_ROOT=your_notion_page_id_here
```

### Optional Configuration
```env
# File Upload Settings
NOTION_FILE_UPLOAD_ENABLED=true
NOTION_MAX_FILE_SIZE=10485760  # 10MB
NOTION_UPLOAD_TIMEOUT=30

# Cache Settings
NOTION_CACHE_ENABLED=true
NOTION_CACHE_TTL=3600  # 1 hour
NOTION_CACHE_DIR=.narko_cache

# Embedding Settings
EMBEDDING_ENABLED_TYPES=.py,.js,.md,.txt
```

## Usage Examples

### Basic Usage
```bash
# Process and import a markdown file
narko --file document.md --import

# Test processing without importing
narko --file document.md --test

# Validate markdown files
narko --validate "docs/*.md"
```

### Advanced Usage
```bash
# Import with specific parent page
narko --file doc.md --parent PAGE_ID --import

# Show processing details
narko --file doc.md --test --show-embeddings --verbose

# Cache management
narko --cache-info
narko --cache-cleanup
```

## Package Structure

```
narko/
├── src/narko/                 # Main package
│   ├── __init__.py           # Package initialization
│   ├── cli.py                # Command line interface
│   ├── config.py             # Configuration management
│   ├── converter.py          # Markdown to Notion converter
│   ├── extensions/           # Marko extensions
│   ├── notion/              # Notion API client
│   ├── utils/               # Utility modules
│   └── tests/               # Unit tests
├── scripts/                 # Setup and utility scripts
├── docs/                    # Documentation
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Modern Python packaging
├── setup.py                # Traditional Python packaging
└── .env.example            # Configuration template
```

## Dependencies

### Runtime Dependencies
- marko[gfm] >= 2.0.0 - Markdown parsing with GitHub flavored markdown
- requests >= 2.28.0 - HTTP client for Notion API
- python-dotenv >= 0.19.0 - Environment variable management
- aiohttp >= 3.8.0 - Async HTTP client
- aiofiles >= 22.1.0 - Async file operations

### Development Dependencies
- pytest >= 7.0.0 - Testing framework
- pytest-asyncio >= 0.21.0 - Async test support
- pytest-cov >= 4.0.0 - Coverage reporting
- black >= 22.0.0 - Code formatting
- flake8 >= 5.0.0 - Linting
- mypy >= 1.0.0 - Type checking

## Troubleshooting

### Common Issues

1. **Import Errors:**
   ```bash
   # Make sure you're in the right directory and virtual environment
   pip install -e .
   ```

2. **Missing Dependencies:**
   ```bash
   # Install all dependencies
   pip install -r requirements.txt
   ```

3. **Configuration Errors:**
   ```bash
   # Check your .env file
   cat .env
   # Verify Notion API key and page ID
   ```

4. **Permission Issues:**
   ```bash
   # Check Notion integration permissions
   # Ensure the integration has access to your target page
   ```

### Testing Installation

```bash
# Run package structure test
python scripts/test_package.py

# Run unit tests
pytest src/narko/tests/ -v

# Test CLI functionality
narko --help
```

## Migration from UV

If you were using the UV-based version, here's how to migrate:

1. **Remove UV shebang references**
2. **Install with standard pip:**
   ```bash
   pip install -e .
   ```
3. **Use standard Python commands:**
   ```bash
   # Old: uv run narko.py --file doc.md
   # New: narko --file doc.md
   ```

## Support

- Check the troubleshooting section above
- Review the example usage in the CLI help: `narko --help`
- Ensure all dependencies are installed: `pip list | grep narko`