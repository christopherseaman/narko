# Notion API File Upload Documentation

## Working with Files and Media

### Upload Methods
1. **Direct Upload (single-part)**: For files ≤ 20MB
2. **Direct Upload (multi-part)**: For files > 20MB  
3. **Indirect Import**: Import from publicly accessible URLs

### Supported Block Types
- **Media blocks**: file, image, PDF, audio, video
- **Database file properties**
- **Page icon and cover**

### File Type Support
- **Audio**: .mp3, .wav, .aac (and others)
- **Documents**: .pdf, .docx, .xlsx, .pptx
- **Images**: .jpg, .png, .gif, .webp
- **Video**: .mp4, .mov, .webm

### File Size Limits
- **Free workspaces**: 5 MiB per file
- **Paid workspaces**: 5 GiB per file

### Key Restrictions
- File type must match block context
- Filename max length: 900 bytes
- Recommend shorter filenames for performance

### Important Considerations
- Check file type compatibility before uploading
- Use appropriate upload method based on file size
- Verify workspace-specific file size limits

## File Upload API Reference

### Endpoints
1. **Create a file upload** (POST)
2. **Send a file upload** (POST) 
3. **Complete a file upload** (POST)
4. **Retrieve a file upload** (GET)
5. **List file uploads** (GET)

### File Upload Object Properties
- `id`: Unique identifier for the file upload
- `status`: Possible values - "pending", "uploaded", "expired", "failed"
- `filename`: Name of the uploaded file
- `content_type`: MIME content type
- `content_length`: File size in bytes
- `upload_url`: URL for sending file contents
- `complete_url`: URL for completing multi-part uploads
- `expiry_time`: Timestamp when upload will expire

### Important Notes
- Once a file upload has "uploaded" status, it can be attached to blocks, pages, and databases
- Uploads have an expiration time if not attached to a workspace object
- Supports both single-part and multi-part upload modes

### Status Flow
1. **pending** → File upload created, ready for content
2. **uploaded** → File content sent successfully
3. **expired** → Upload expired before completion
4. **failed** → Upload failed due to error

## Implementation Notes for narko

### Current Implementation Status
- ✅ API key authentication working
- ✅ Create file upload endpoint working
- ✅ Send file upload endpoint working (with Bearer token)
- ⚠️ MIME type compatibility - use `text/plain` for text files
- 📋 Need to test with various file types

### Supported MIME Types (based on testing)
- `text/plain` ✅ (for .txt, .md, .py, .js, .css files)
- `application/json` ✅
- `application/xml` ✅  
- `text/html` ✅
- ❌ `text/markdown` - Not supported, use `text/plain`
- ❌ `text/x-python` - Not supported, use `text/plain`
- ❌ `text/javascript` - Not supported, use `text/plain`

### Next Steps
1. Test corrected MIME types
2. Implement embedding generation for uploaded files
3. Add comprehensive file type validation
4. Test with various file sizes and types