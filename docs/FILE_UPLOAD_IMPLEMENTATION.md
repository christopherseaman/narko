# Notion File Upload Implementation

## Overview
File upload functionality for Notion API with automatic workaround for unsupported file types.

## Implementation Status: ✅ Complete

### Features
- **Native Support**: Direct upload for Notion-supported file types
- **Automatic Workaround**: Adds `.txt` suffix to unsupported text files
- **Full Content Preservation**: File content remains intact
- **Transparent to Users**: Original filename tracked in metadata

## Supported File Types

### Natively Supported (Direct Upload)
Based on [Notion API Documentation](https://developers.notion.com/docs/working-with-files-and-media):

#### Audio
`.aac`, `.adts`, `.mid`, `.midi`, `.mp3`, `.mpga`, `.m4a`, `.m4b`, `.mp4`, `.oga`, `.ogg`, `.wav`, `.wma`

#### Documents
`.pdf`, `.txt`, `.json`, `.doc`, `.dot`, `.docx`, `.dotx`, `.xls`, `.xlt`, `.xla`, `.xlsx`, `.xltx`, `.ppt`, `.pot`, `.pps`, `.ppa`, `.pptx`, `.potx`

#### Images
`.gif`, `.heic`, `.jpeg`, `.jpg`, `.png`, `.svg`, `.tif`, `.tiff`, `.webp`, `.ico`

#### Video
`.amv`, `.asf`, `.wmv`, `.avi`, `.f4v`, `.flv`, `.gifv`, `.m4v`, `.mkv`, `.webm`, `.mov`, `.qt`, `.mpeg`

### Unsupported Files (Use .txt Workaround)

#### Programming Languages
`.py`, `.sh`, `.bash`, `.md`, `.js`, `.ts`, `.jsx`, `.tsx`, `.java`, `.cpp`, `.c`, `.h`, `.hpp`, `.cs`, `.rb`, `.go`, `.rs`, `.swift`, `.kt`, `.scala`, `.r`, `.php`, `.pl`, `.lua`, `.dart`

#### Configuration/Data
`.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`, `.conf`, `.xml`, `.env`, `.properties`, `.gitignore`

#### Web Files
`.html`, `.css`, `.scss`, `.sass`, `.less`

#### Other
`.sql`, `.graphql`, `.proto`, `.dockerfile`, `.makefile`, `.gradle`, `.cmake`, `.rst`, `.adoc`, `.tex`

## How It Works

### For Supported Files
```python
# Direct upload with proper MIME type
uploader.upload_async("document.pdf")  # Uploads as-is
```

### For Unsupported Files
```python
# Automatic .txt suffix added
uploader.upload_async("script.py")  # Uploads as "script.py.txt"
# Original name preserved in metadata
```

## API Usage

```python
from narko.config import Config
from narko.notion.uploader import FileUploader

# Initialize
config = Config.from_env()
uploader = FileUploader(config)

# Upload any file - workaround applied automatically
result = await uploader.upload_async("myfile.py")

# Result includes:
# - file_id: Notion file ID
# - name: Uploaded filename (may include .txt)
# - original_name: Original filename
# - workaround_applied: Boolean flag
```

## File Size Limits
- **Free workspaces**: 5 MB per file
- **Paid workspaces**: 5 GB per file
- **Files > 20 MB**: Must use multi-part upload (not yet implemented)

## Test Results
✅ All 10 test cases passing:
- 4 native uploads (txt, pdf, png, json)
- 6 workaround uploads (py, md, sh, html, css, yaml)

## Implementation Files
- `/src/narko/config.py` - File type detection and MIME mappings
- `/src/narko/notion/uploader.py` - Upload logic with workaround
- `/tests/test_file_upload_implementation.py` - Comprehensive tests

## Future Improvements
- [ ] Multi-part upload for large files (>20MB)
- [ ] Progress callbacks for large uploads
- [ ] Batch upload optimization
- [ ] Better error messages for quota exceeded

## Notes
- The `.txt` workaround preserves file content perfectly
- Users can download and rename files to restore original extension
- This approach works within Notion's API constraints while maximizing compatibility