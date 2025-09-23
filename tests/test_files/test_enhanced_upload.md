# Enhanced File Upload and Embedding Test

This document tests the comprehensive file upload and embedding system with metadata extraction and caching.

## External Files (Always Work)

High-resolution image:
![image:Sample Image](https://via.placeholder.com/800x600.png?text=High+Resolution+Sample)

External PDF document:
![pdf:Technical Documentation](https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf)

Video content:
![video:Demo Video](https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4)

Embedded content:
![embed:GitHub Repository](https://github.com/torvalds/linux)

## Local Files with Embedding

### Text Files (Embedding-Ready)
Python script with content extraction:
![file:Sample Python Code](./narko.py)

JSON configuration:
![file:Package Configuration](./package.json)

### Image Files
Company profile image:
![image:Profile Photo](./profile.png)

### Documents (when available)
Markdown documentation:
![file:Test Documentation](./test_file_upload.md)

## Enhanced Features Demo

### File with Custom Caption
![image:Beautiful Landscape Photo](https://picsum.photos/800/400)

### Auto-Detection from Extension
![file](./profile.png)

### Multiple Files in Sequence
![image](https://via.placeholder.com/400x300.png?text=Image+1)
![image](https://via.placeholder.com/400x300.png?text=Image+2)
![image](https://via.placeholder.com/400x300.png?text=Image+3)

## Integration with Other Extensions

> [!TIP] File Upload in Callouts
> You can embed files directly in callouts:
> ![image:Example Image](https://via.placeholder.com/300x200.png?text=Callout+Image)

### Task List with Files
- [x] Upload images ✓
- [x] Upload documents ✓
- [x] Test embedding extraction ✓
- [ ] Upload videos
- [ ] Test caching system

### Code Block with File Reference
```python
# This Python script shows file handling
def process_file(filename):
    with open(filename, 'r') as f:
        return f.read()

# Reference: ![file](./narko.py)
```

### Math with Diagrams
$$
\text{File processing: } f(x) = \sum_{i=1}^{n} \text{embed}(file_i)
$$

Include supporting diagram:
![image:Mathematical Visualization](https://via.placeholder.com/500x300.png?text=Math+Diagram)

## Error Handling Tests

Non-existent file:
![image](./does_not_exist.png)

Empty caption test:
![file:](./profile.png)

Large file simulation (will show size in metadata):
![file:Large File Reference](./narko.py)

## Performance Features

### Caching Test
Upload the same file multiple times (should use cache on subsequent uploads):
![file:Cached Upload Test 1](./package.json)
![file:Cached Upload Test 2](./package.json)
![file:Cached Upload Test 3](./package.json)

### Metadata Extraction
Files with extractable content for embedding:
![file:Python Source](./narko.py)
![file:JSON Data](./package.json)

## Advanced Usage

### Combined Media Types
![image:Visual Element](https://picsum.photos/600/400)
![pdf:Reference Document](https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf)
![video:Instructional Content](https://sample-videos.com/zip/10/mp4/SampleVideo_720x480_1mb.mp4)

### Sequential File Processing
This tests the system's ability to handle multiple files efficiently:

1. ![file:Config](./package.json)
2. ![file:Source](./narko.py) 
3. ![file:Documentation](./README.md)
4. ![image:Image](./profile.png)

---

**Testing Commands:**

```bash
# Basic test mode
uv run --script narko.py --file test_enhanced_upload.md --test

# Test with embedding analysis
uv run --script narko.py --file test_enhanced_upload.md --test --show-embeddings

# Check cache statistics
uv run --script narko.py --cache-info

# Import with caching disabled
uv run --script narko.py --file test_enhanced_upload.md --import --no-cache

# Full import with file upload
uv run --script narko.py --file test_enhanced_upload.md --import --upload-files
```

This test document exercises all enhanced features including embedding extraction, caching, metadata generation, and advanced error handling.