# Notion File Upload Fix Documentation

## Problem Summary
File uploads for `.py`, `.sh`, and `.md` files were failing due to incorrect MIME type mappings. The Notion API expects specific Content-Type headers for different file types.

## Root Cause
The original configuration in `src/narko/config.py` was mapping these file types to generic `text/plain`, but Notion requires:
- Python files (`.py`): `text/x-python-script`
- Shell scripts (`.sh`): `text/x-shellscript`
- Markdown files (`.md`): `text/markdown`

## Solution Implemented

### 1. Fixed MIME Type Mappings
Updated `src/narko/config.py` to use correct Content-Type headers:

```python
mime_type_mapping: Dict[str, str] = {
    '.py': 'text/x-python-script',  # Was 'text/plain'
    '.sh': 'text/x-shellscript',    # Was missing
    '.md': 'text/markdown',          # Was 'text/plain'
    # ... other mappings
}
```

### 2. Updated Uploader Logic
Modified `src/narko/notion/uploader.py` to handle both:
- Direct uploads via `/send` endpoint (new API)
- S3 presigned URL uploads (legacy/browser method)

Key changes:
- Detection of upload endpoint type
- Proper header handling for multipart/form-data
- Support for both 200/201 (API) and 204 (S3) success codes

### 3. Test Files Created
Created comprehensive test files in `/tests/test_files/`:
- `test_upload.py` - Python script with shebang and functions
- `test_upload.sh` - Shell script with bash commands
- `test_upload.md` - Markdown with various formatting

### 4. Test Scripts
- `/tests/test_notion_upload.py` - Python test script
- `/tests/curl_upload_test.sh` - Bash/curl test script

## Upload Process

The correct upload process is:

1. **Create Upload Object**
   ```
   POST https://api.notion.com/v1/file_uploads
   Body: {} or {"filename": "name", "content_type": "mime/type"}
   Returns: {"id": "upload_id", "upload_url": "..."}
   ```

2. **Upload File Content**
   ```
   POST https://api.notion.com/v1/file_uploads/{id}/send
   Headers: Authorization, Notion-Version
   Body: multipart/form-data with file
   ```

3. **Attach to Page/Block**
   ```
   PATCH https://api.notion.com/v1/blocks/{page_id}/children
   Body: {"children": [{"type": "file", "file": {...}}]}
   ```

## Testing

Test against: https://www.notion.so/sqrlly/File-Extension-Test-Simple-Uploader-278d9fdd1a1a8065b95fc0a1d216418f

### Run Python Test:
```bash
export NOTION_API_KEY="your_api_key"
python3 tests/test_notion_upload.py
```

### Run Curl Test:
```bash
export NOTION_API_KEY="your_api_key"
chmod +x tests/curl_upload_test.sh
./tests/curl_upload_test.sh
```

## Integration with Narko

The fixes are integrated into the existing narko uploader module. The `FileUploader` class now:
1. Uses correct MIME types from config
2. Handles both API endpoints correctly
3. Supports streaming for large files
4. Includes proper error handling

## Verified Working

✅ Python files (.py) - Upload with `text/x-python-script`
✅ Shell scripts (.sh) - Upload with `text/x-shellscript`
✅ Markdown files (.md) - Upload with `text/markdown`

## Additional Notes

- The HAR file analysis revealed Notion uses S3 presigned URLs in the browser
- The API provides a simpler `/send` endpoint for direct uploads
- Content-Type must match Notion's expectations for proper file recognition
- File size limit is 5MB for direct uploads (can use multi-part for larger)

## Future Improvements

Consider adding:
- Support for more file types (`.ts`, `.jsx`, `.yml`, etc.)
- Multi-part upload for files > 5MB
- Batch upload functionality
- Progress indicators for large files