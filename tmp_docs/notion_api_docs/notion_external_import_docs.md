# Notion External File Import Documentation

## Importing External Files (Indirect Import)

### Process Overview
The indirect import method allows importing files from external URLs without uploading them directly.

### Step 1: Start File Upload with External URL
Use the Create a File Upload API endpoint with:
- `mode`: "external_url" 
- `filename`: Name for the file in Notion
- `external_url`: Publicly accessible URL

### Example Request
```json
POST https://api.notion.com/v1/file_uploads
{
  "mode": "external_url",
  "filename": "example.jpg",
  "external_url": "https://example.com/image.jpg"
}
```

### URL Requirements
The external URL must be:
- ✅ SSL-enabled (HTTPS)
- ✅ Publicly accessible (no authentication required)
- ✅ Expose `Content-Type` header
- ✅ Within workspace file size limit

### Step 2: Track Import Status
Two methods available:

#### 1. Polling Method
- Periodically check file upload status
- GET /v1/file_uploads/{file_upload_id}
- Monitor `status` field

#### 2. Webhooks Method
Listen for events:
- `file_upload.complete` - Import successful
- `file_upload.upload_failed` - Import failed

### Step 3: Attach File Upload
- Use File Upload ID in blocks, pages, or databases
- Same structure as direct uploads: `file_upload.id`

### Limitations
- **Free workspace**: 5 MiB file size limit
- **Paid workspace**: 5 GiB file size limit  
- **Time limit**: File upload must be attached within one hour
- **URL requirements**: Must be publicly accessible with SSL

### Status Flow
1. **pending** → External file import initiated
2. **uploaded** → File successfully imported from URL
3. **expired** → Import expired (not attached within 1 hour)
4. **failed** → Import failed (URL invalid, too large, etc.)

## Implementation Notes for narko

### Current Status
- ✅ Direct upload working
- ❌ External import not implemented yet
- 🔄 Need to add external_url mode support

### Required Changes
1. Add external URL detection in file upload blocks
2. Implement external_url mode in upload functions
3. Add polling mechanism for import status
4. Update block creation to handle external imports

### External URL Detection
```markdown
![image](https://example.com/image.jpg)  # Should use external import
![file](local_file.txt)                  # Should use direct upload
```

### Implementation Strategy
1. Detect HTTP/HTTPS URLs in file references
2. Use external_url mode for web URLs
3. Implement status polling until import completes
4. Create blocks with imported file_upload ID