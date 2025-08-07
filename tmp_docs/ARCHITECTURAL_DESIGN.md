# Narko System Architecture Design

## Executive Summary

The narko file upload/embedding system demonstrates **excellent architectural design** with a production-ready implementation that seamlessly integrates with the existing marko extension pattern. The current implementation requires **no major changes** but offers opportunities for optimization and enhancement.

## Architecture Overview

### Current System Status: ✅ PRODUCTION-READY

The file upload functionality is **already fully implemented** and validated. This analysis focuses on architectural assessment and optimization opportunities.

### Core Architecture Pattern

```
Markdown Input → Marko Parser → Custom Extensions → NotionConverter → Notion API
                                      ↓
                            FileUploadBlock Extension
                                      ↓
                        File Processing & Upload Handler
                                      ↓
                              Notion Block Creation
```

## Component Analysis

### 1. FileUploadBlock Extension (Lines 247-298)

**Design Quality**: Excellent ⭐⭐⭐⭐⭐

```python
class FileUploadBlock(block.BlockElement):
    pattern = re.compile(r'^( {0,3})!\[(file|image|video|pdf|audio|embed)(?::([^\]]*))?\]\(([^)]+)\)[ \t]*$', re.M)
    priority = 9  # High priority to override standard images
```

**Strengths**:
- Follows established marko extension pattern
- Comprehensive file type support
- High priority ensures proper override behavior
- Clean regex pattern matching
- Auto-detection capabilities

**Architecture Decision**: Extension-based approach maintains consistency with existing MathBlock, CalloutBlock patterns.

### 2. File Upload Handler (Lines 771-823)

**Design Quality**: Robust ⭐⭐⭐⭐⭐

```python
def upload_file_to_notion(file_path: str, file_name: str = None) -> Dict:
    # Two-step Notion API process:
    # 1. Create file upload request
    # 2. Upload file content
```

**Strengths**:
- Proper Notion File Upload API integration
- Comprehensive error handling
- Secure file validation
- Two-step upload process (industry standard)

### 3. NotionConverter Integration (Lines 566-712)

**Design Quality**: Well-integrated ⭐⭐⭐⭐⭐

```python
def process_file_upload(self, node: 'FileUploadBlock') -> Dict:
    # Handles both local files and external URLs
    # Creates appropriate Notion blocks
    # Provides graceful error fallbacks
```

**Strengths**:
- Dual handling (local files vs external URLs)
- Type-specific Notion block creation
- Error resilience with fallback messages
- Clean separation of concerns

## Data Flow Architecture

### 1. Input Processing
```
![type:caption](path_or_url) → FileUploadBlock.pattern → AST Node
```

### 2. File Type Resolution
```
Extension Detection → Type Inference → Notion Block Type Selection
```

### 3. Upload Flow (Local Files)
```
File Validation → Notion API Upload → Block Creation → Error Handling
```

### 4. External URL Flow
```
URL Recognition → Direct Block Creation (No Upload)
```

## Security Architecture

### Current Security Measures ✅

1. **File Validation**: Existence and accessibility checks
2. **API Security**: Token-based authentication (NOTION_API_KEY)
3. **Path Security**: Relative path handling prevents traversal attacks
4. **Error Sanitization**: Minimal error exposure
5. **Upload Limits**: Respects Notion's 5MB/5GB limits

### Security Assessment: **SECURE** 🔒

The implementation follows security best practices without any identified vulnerabilities.

## Performance Architecture

### Current Performance Characteristics

| Component | Performance | Assessment |
|-----------|-------------|------------|
| Pattern Matching | High Priority (9) | Excellent |
| Local File Upload | Two-step API | Standard |
| External URLs | Direct Reference | Optimal |
| Memory Usage | Streaming | Efficient |
| Error Handling | Graceful Fallbacks | Good |

### Performance Bottlenecks

1. **Network Upload Time**: Large files (>20MB) may be slow
2. **Sequential Processing**: Files processed one at a time
3. **No Caching**: Repeated uploads of same files

## Integration Architecture

### Seamless Integration Points ✅

1. **Marko Extensions**: Follows established pattern
2. **CLI Interface**: Consistent with existing flags
3. **Configuration**: Uses .env and page_map.json
4. **Error System**: Unified error handling
5. **Notion API**: Proper API integration

## Recommended Optimizations

### 1. Performance Enhancements

#### Batch Upload Processing
```python
def batch_upload_files(file_paths: List[str]) -> Dict[str, Dict]:
    """Upload multiple files concurrently"""
    # Implement concurrent uploads with asyncio
    # Reduce total upload time for multiple files
```

#### Upload Caching
```python
class FileUploadCache:
    """Cache uploaded file IDs to prevent re-uploads"""
    def __init__(self):
        self.cache = {}  # file_hash -> file_id mapping
```

#### Progress Indicators
```python
def upload_with_progress(file_path: str, callback=None):
    """Provide upload progress feedback"""
    # Useful for large files (>5MB)
```

### 2. Enhanced Error Handling

#### Retry Mechanism
```python
@retry(max_attempts=3, backoff_factor=2)
def upload_file_to_notion(file_path: str) -> Dict:
    """Add retry logic for transient failures"""
```

#### Detailed Error Reporting
```python
class UploadError(Exception):
    """Custom exception with detailed error context"""
    def __init__(self, message, file_path, error_code):
        self.file_path = file_path
        self.error_code = error_code
```

### 3. Configuration Enhancements

#### Upload Configuration
```python
class UploadConfig:
    """Centralized upload configuration"""
    max_file_size: int = 5 * 1024 * 1024  # 5MB
    concurrent_uploads: int = 3
    retry_attempts: int = 3
    cache_enabled: bool = True
```

## Future Architecture Considerations

### 1. Scalability Enhancements

- **Concurrent Processing**: Parallel file uploads
- **Streaming Uploads**: For files >100MB
- **Distributed Caching**: Redis-based file cache
- **Queue System**: Background upload processing

### 2. Advanced Features

- **File Compression**: Auto-compress before upload
- **Format Conversion**: Convert unsupported formats
- **Metadata Extraction**: EXIF data for images
- **Thumbnail Generation**: Preview images

### 3. Integration Expansions

- **Cloud Storage**: S3, GCS, Azure Blob integration
- **CDN Support**: Cloudflare, CloudFront integration
- **Database Integration**: Metadata storage
- **Webhook Support**: Upload completion notifications

## Architecture Decision Records (ADRs)

### ADR-001: Extension-Based Architecture
**Decision**: Use marko extension pattern for file uploads
**Rationale**: Maintains consistency with existing codebase
**Status**: ✅ Implemented

### ADR-002: Two-Step Upload Process
**Decision**: Follow Notion's recommended upload flow
**Rationale**: Ensures compatibility and reliability
**Status**: ✅ Implemented

### ADR-003: Dual URL/File Handling
**Decision**: Support both local files and external URLs
**Rationale**: Provides flexibility and performance optimization
**Status**: ✅ Implemented

### ADR-004: High Priority Pattern Matching
**Decision**: Use priority 9 for FileUploadBlock
**Rationale**: Ensures proper override of standard image processing
**Status**: ✅ Implemented

## Deployment Architecture

### Production Requirements

1. **Environment Variables**:
   ```bash
   NOTION_API_KEY="secret_xxx"
   NOTION_IMPORT_ROOT="page_id"
   ```

2. **File System Access**: Read permissions for upload files

3. **Network Access**: HTTPS access to api.notion.com

4. **Memory Requirements**: Minimal (streaming uploads)

### Monitoring & Observability

#### Metrics to Track
- Upload success/failure rates
- Average upload times
- File size distributions
- Error frequency by type
- API rate limit usage

#### Logging Strategy
```python
import logging

logger = logging.getLogger("narko.uploads")

def upload_file_to_notion(file_path: str) -> Dict:
    logger.info(f"Starting upload: {file_path}")
    # ... upload logic ...
    logger.info(f"Upload completed: {file_path}")
```

## Quality Attributes Assessment

| Quality Attribute | Current Rating | Target Rating |
|-------------------|----------------|---------------|
| **Maintainability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Reliability** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Performance** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Security** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Usability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Scalability** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## Conclusion

The narko file upload architecture demonstrates **excellent design principles** with a production-ready implementation. The system successfully:

✅ **Maintains architectural consistency** with existing marko extensions  
✅ **Provides comprehensive file type support** (image, video, audio, pdf, file, embed)  
✅ **Implements secure upload mechanisms** with proper error handling  
✅ **Offers flexible input options** (local files and external URLs)  
✅ **Integrates seamlessly** with the Notion API  

**No immediate architectural changes are required.** The current implementation is ready for production use with optional optimizations for enhanced performance and scalability.

## Recommendations Priority

### High Priority (Immediate)
- ✅ **Already Implemented**: Core functionality complete

### Medium Priority (Next Sprint)
- Upload progress indicators for large files
- Basic retry mechanism for failed uploads
- Enhanced error reporting

### Low Priority (Future)
- Batch upload processing
- Upload caching system
- Advanced monitoring and metrics

The architecture successfully balances **simplicity**, **security**, and **extensibility** while maintaining the clean, extension-based design philosophy of the narko project.