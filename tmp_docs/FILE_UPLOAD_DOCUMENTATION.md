# File Upload Extension Documentation

## Overview

The narko file upload extension allows you to embed files, images, videos, PDFs, and other media directly in your Notion pages using markdown syntax. This extension follows the marko extension pattern and integrates seamlessly with the existing NotionConverter.

## Syntax

The file upload extension uses an enhanced image-like syntax:

```markdown
![type:caption](path_or_url)
```

### Parameters

- **type**: File type (optional, auto-detected if not specified)
  - `image` - Image files (jpg, png, gif, etc.)
  - `video` - Video files (mp4, mov, avi, etc.)
  - `audio` - Audio files (mp3, wav, m4a, etc.)
  - `pdf` - PDF documents
  - `file` - Generic files
  - `embed` - Embedded content

- **caption**: Optional caption/title (after colon)
- **path_or_url**: Local file path or external URL

## Examples

### Basic Usage

```markdown
# Auto-detect file type from extension
![file](./document.pdf)
![file](./image.png)
![file](./video.mp4)

# Explicit file types
![image](./photo.jpg)
![video](./demo.mp4)
![pdf](./manual.pdf)
![audio](./music.mp3)
```

### With Captions

```markdown
![image:Company Logo](./logo.png)
![video:Product Demo](./demo.mp4)
![pdf:User Manual](./documentation.pdf)
```

### External URLs

```markdown
![image](https://example.com/image.png)
![video](https://example.com/video.mp4)
![embed](https://github.com/user/repo)
```

## File Type Auto-Detection

When using `![file](path)`, the extension automatically detects the file type based on the file extension:

| Extensions | Detected Type |
|------------|---------------|
| .jpg, .jpeg, .png, .gif, .bmp, .webp, .svg | image |
| .mp4, .mov, .avi, .mkv, .webm, .m4v | video |
| .mp3, .wav, .m4a, .aac, .ogg, .flac | audio |
| .pdf | pdf |
| All others | file |

## Local File Upload Process

For local files, the extension:

1. **Validates** file existence and accessibility
2. **Uploads** to Notion using the File Upload API
3. **Creates** appropriate Notion block with file reference
4. **Handles errors** gracefully with fallback messages

## External URL Handling

For external URLs (starting with `http://` or `https://`):

1. **Creates** external file blocks directly
2. **No upload** required - references URL
3. **Faster processing** - no file transfer

## Error Handling

The extension provides comprehensive error handling:

- **File not found**: Creates paragraph with error message
- **Upload failure**: Shows detailed error information
- **Invalid URLs**: Graceful fallback to text representation
- **Permission errors**: Clear error messages

## CLI Usage

### Basic Usage

```bash
# Test mode (no upload to Notion)
python narko.py --file document.md --test

# Import with file upload support
python narko.py --file document.md --import --upload-files

# Specify parent page
python narko.py --file document.md --parent PAGE_ID --import
```

### Environment Variables

```bash
# Required for file uploads
export NOTION_API_KEY="your_api_key"
export NOTION_IMPORT_ROOT="default_parent_page_id"
```

## Integration with Other Extensions

File uploads work seamlessly with other narko extensions:

```markdown
> [!TIP]
> You can include images in callouts!
> ![image:Example](./example.png)

- [x] Task with attached file
- ![file](./attachment.pdf)

$$
\text{Math equations with diagrams: }
$$
![image:Mathematical Diagram](./diagram.png)
```

## Limitations

1. **File size limits** (Notion API):
   - Free workspaces: 5 MiB per file
   - Paid workspaces: 5 GiB per file

2. **Upload time limit**: Files must be attached within 1 hour of upload

3. **Supported formats**: Limited to Notion's supported file types

4. **API requirements**: Requires valid Notion API key for uploads

## Security Considerations

- **File validation**: All files are validated before upload
- **Path traversal protection**: Relative paths are safely handled
- **API authentication**: Secure token-based authentication
- **Error information**: Minimal error exposure to prevent information leakage

## Performance Tips

1. **Use external URLs** when possible for faster processing
2. **Optimize file sizes** before upload
3. **Batch multiple files** in the same markdown document
4. **Consider file placement** relative to markdown document

## Troubleshooting

### Common Issues

**File not found**:
```
❌ File not found: ./missing.png
```
*Solution*: Check file path and permissions

**Upload failed**:
```
❌ File upload failed: Authentication error
```
*Solution*: Verify NOTION_API_KEY environment variable

**Large file errors**:
*Solution*: Use external hosting for files > 20MB

### Debug Mode

Use `--test` flag to see processed blocks without uploading:

```bash
python narko.py --file test.md --test
```

This shows all file blocks that would be created, including error handling.

## Implementation Details

The file upload extension is implemented as a marko `BlockElement`:

- **Pattern matching**: Uses regex to detect file upload syntax
- **Priority**: High priority (9) to override standard image processing
- **Type inference**: Automatic file type detection from extensions
- **Notion integration**: Uses official Notion File Upload API
- **Error resilience**: Comprehensive error handling with graceful fallbacks

## Future Enhancements

Planned improvements include:

- Multi-part upload for large files
- Drag-and-drop file support
- Batch file operations
- File compression options
- Progress indicators for large uploads
- Caching for repeated uploads

---

This extension maintains the clean, extension-based architecture of narko while adding powerful file upload capabilities that integrate seamlessly with Notion's block system.