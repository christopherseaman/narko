# External Import Test 🌐

Testing the new external import functionality with proper indirect import method.

## External Image Import
This should use the indirect import method:

![image](https://httpbin.org/image/jpeg)

## Local File for Comparison
Local file upload for comparison:

![file](test_data.json)

## Test Results Expected
1. **External image**: Should be imported via indirect method with polling
2. **Local file**: Should use direct upload from cache
3. **Both**: Should create proper file blocks with metadata

## Import Details
- **Method**: Notion indirect import API
- **Polling**: Automatic status checking
- **Fallback**: Direct external reference if import fails
- **Metadata**: Import source and file information

---
*Testing external import with indirect method*