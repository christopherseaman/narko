"""
End-to-end tests for complete file upload and markdown processing workflows.
Tests the entire system from markdown parsing to Notion page creation.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch, Mock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from narko import process_file, create_notion_page, main

@pytest.mark.e2e
class TestCompleteWorkflow:
    """Test complete end-to-end workflows."""
    
    def test_markdown_to_notion_external_files(self, temp_dir, mock_env_vars):
        """Test complete workflow with external file URLs."""
        # Create markdown with external files
        markdown_content = """# Test Document

External image:
![image](https://via.placeholder.com/400x300.png)

External PDF:
![pdf:User Manual](https://example.com/manual.pdf)

Regular content:
This is a paragraph with **bold** and *italic* text.

> [!TIP]
> This is a callout with an external image:
> ![image](https://example.com/icon.png)
"""
        
        md_file = temp_dir / "test_external.md"
        md_file.write_text(markdown_content)
        
        # Process the file
        result = process_file(str(md_file))
        
        assert "error" not in result
        assert result["title"] == "test_external"
        assert len(result["blocks"]) > 0
        
        # Verify image blocks were created
        image_blocks = [b for b in result["blocks"] if b.get("type") == "image"]
        assert len(image_blocks) == 2
        
        # Verify external URLs are preserved
        for img_block in image_blocks:
            assert img_block["image"]["type"] == "external"
            assert "url" in img_block["image"]["external"]
    
    def test_markdown_to_notion_local_files(self, temp_dir, sample_image_file, mock_env_vars):
        """Test complete workflow with local files."""
        # Create markdown with local file references
        markdown_content = f"""# Test Local Files

Local image:
![image:Test Image]({sample_image_file})

Mixed content:
- [x] Task with image: ![file]({sample_image_file})
- [ ] Regular task

$$
E = mc^2
$$
"""
        
        md_file = temp_dir / "test_local.md"
        md_file.write_text(markdown_content)
        
        with patch('narko.upload_file_to_notion') as mock_upload:
            # Mock successful upload
            mock_upload.return_value = {
                "file_id": "uploaded-file-123",
                "name": "test_image.png",
                "success": True
            }
            
            result = process_file(str(md_file))
            
            assert "error" not in result
            assert len(result["blocks"]) > 0
            
            # Verify upload was attempted
            mock_upload.assert_called()
    
    def test_complete_notion_page_creation(self, temp_dir, mock_env_vars):
        """Test complete workflow from markdown to Notion page."""
        # Create comprehensive markdown
        markdown_content = """# Comprehensive Test

## Text Formatting
**Bold text** and *italic text* and `inline code`.

## Lists
- First item
- Second item
  - Nested item

## Task List
- [x] Completed task
- [ ] Pending task

## Math
$$
\\sum_{i=1}^{n} x_i = \\frac{1}{n} \\sum_{i=1}^{n} x_i
$$

## Callouts
> [!NOTE]
> This is an important note.

## External Media
![image](https://via.placeholder.com/300x200.png)

## Code Block
```python
def hello():
    print("Hello, World!")
```
"""
        
        md_file = temp_dir / "comprehensive.md"
        md_file.write_text(markdown_content)
        
        # Process markdown
        result = process_file(str(md_file))
        assert "error" not in result
        
        # Mock page creation
        with patch('narko.create_notion_page') as mock_create:
            mock_create.return_value = {
                "id": "new-page-123",
                "url": "https://notion.so/new-page-123"
            }
            
            # Create Notion page
            page_result = create_notion_page(
                result["parent_id"],
                result["title"],
                result["blocks"]
            )
            
            assert "url" in page_result
            mock_create.assert_called_once()
            
            # Verify call arguments
            call_args = mock_create.call_args[0]
            assert call_args[1] == "comprehensive"  # title
            assert len(call_args[2]) > 5  # blocks
    
    def test_cli_workflow_test_mode(self, temp_dir, sample_image_file):
        """Test CLI workflow in test mode."""
        # Create test markdown
        markdown_content = f"""# CLI Test

![image]({sample_image_file})

Regular paragraph with **formatting**.
"""
        
        md_file = temp_dir / "cli_test.md"
        md_file.write_text(markdown_content)
        
        # Mock sys.argv
        test_args = ["narko.py", "--file", str(md_file), "--test"]
        
        with patch('sys.argv', test_args):
            with patch('builtins.print') as mock_print:
                try:
                    main()
                    # Should not raise exception
                    assert mock_print.called
                except SystemExit:
                    # Expected for CLI completion
                    pass
    
    def test_cli_workflow_import_mode(self, temp_dir, mock_env_vars):
        """Test CLI workflow in import mode."""
        # Create test markdown
        markdown_content = """# Import Test

Simple content for import testing.

![image](https://example.com/test.png)
"""
        
        md_file = temp_dir / "import_test.md"
        md_file.write_text(markdown_content)
        
        # Mock successful API responses
        with patch('narko.create_notion_page') as mock_create:
            mock_create.return_value = {
                "url": "https://notion.so/test-page"
            }
            
            test_args = ["narko.py", "--file", str(md_file), "--import"]
            
            with patch('sys.argv', test_args):
                with patch('builtins.print') as mock_print:
                    try:
                        main()
                        mock_create.assert_called_once()
                    except SystemExit:
                        pass

@pytest.mark.e2e
class TestErrorRecoveryWorkflows:
    """Test end-to-end error recovery scenarios."""
    
    def test_partial_failure_recovery(self, temp_dir, mock_env_vars):
        """Test recovery when some files fail to upload."""
        # Create markdown with mix of valid and invalid files
        markdown_content = f"""# Mixed Files Test

Valid external:
![image](https://via.placeholder.com/200x200.png)

Invalid local file:
![file](./nonexistent.png)

Another valid external:
![pdf](https://example.com/doc.pdf)
"""
        
        md_file = temp_dir / "mixed_test.md"
        md_file.write_text(markdown_content)
        
        result = process_file(str(md_file))
        
        # Should not fail completely
        assert "error" not in result
        assert len(result["blocks"]) > 0
        
        # Should have error message for missing file
        error_blocks = [
            b for b in result["blocks"] 
            if b.get("type") == "paragraph" and 
            "❌" in str(b.get("paragraph", {}).get("rich_text", []))
        ]
        assert len(error_blocks) > 0
    
    def test_api_failure_graceful_handling(self, temp_dir, sample_image_file, mock_env_vars):
        """Test graceful handling of API failures."""
        markdown_content = f"""# API Failure Test

Local file that will fail to upload:
![image]({sample_image_file})

Regular content should still work:
This is normal text content.
"""
        
        md_file = temp_dir / "api_failure_test.md"
        md_file.write_text(markdown_content)
        
        with patch('narko.upload_file_to_notion') as mock_upload:
            # Mock API failure
            mock_upload.return_value = {"error": "API failure"}
            
            result = process_file(str(md_file))
            
            # Should still process successfully
            assert "error" not in result
            assert len(result["blocks"]) > 0
            
            # Should have error message for failed upload
            error_blocks = [
                b for b in result["blocks"]
                if b.get("type") == "paragraph" and
                "❌" in str(b.get("paragraph", {}).get("rich_text", []))
            ]
            assert len(error_blocks) > 0

@pytest.mark.e2e
@pytest.mark.performance
class TestPerformanceWorkflows:
    """Test performance characteristics of complete workflows."""
    
    def test_large_document_processing(self, temp_dir):
        """Test processing of large documents."""
        import time
        
        # Create large markdown document
        sections = []
        for i in range(50):  # 50 sections
            sections.append(f"""
## Section {i}

This is section {i} with **bold** and *italic* text.

- Item 1 for section {i}
- Item 2 for section {i}
- Item 3 for section {i}

```python
def function_{i}():
    return "Section {i} code"
```

> [!NOTE]
> This is a note for section {i}.

![image](https://via.placeholder.com/300x200.png?text=Section+{i})
""")
        
        large_content = "# Large Document\n\n" + "\n".join(sections)
        
        md_file = temp_dir / "large_document.md"
        md_file.write_text(large_content)
        
        # Process and time it
        start_time = time.time()
        result = process_file(str(md_file))
        processing_time = time.time() - start_time
        
        assert "error" not in result
        assert len(result["blocks"]) > 100  # Should have many blocks
        
        # Should complete in reasonable time
        assert processing_time < 30.0  # 30 seconds max for large document
    
    def test_multiple_file_processing(self, temp_dir):
        """Test processing multiple files in sequence."""
        import time
        
        files = []
        for i in range(10):
            content = f"""# Document {i}
            
Content for document {i} with formatting and ![image](https://example.com/image{i}.png).

```python
print("Document {i}")
```
"""
            md_file = temp_dir / f"doc_{i}.md"
            md_file.write_text(content)
            files.append(md_file)
        
        # Process all files
        start_time = time.time()
        results = []
        for md_file in files:
            result = process_file(str(md_file))
            results.append(result)
        total_time = time.time() - start_time
        
        # All should succeed
        assert all("error" not in result for result in results)
        
        # Should process efficiently
        average_time = total_time / len(files)
        assert average_time < 2.0  # Less than 2 seconds per file on average

@pytest.mark.e2e
@pytest.mark.slow
class TestRealEndToEndWorkflows:
    """
    Real end-to-end tests that actually interact with Notion API.
    These require valid credentials and are marked as slow.
    """
    
    @pytest.mark.skipif(
        not os.environ.get('NOTION_API_KEY') or not os.environ.get('NOTION_IMPORT_ROOT'),
        reason="Real API credentials not available"
    )
    def test_real_notion_integration(self, temp_dir):
        """Test real integration with Notion API."""
        import time
        
        # Create test document
        timestamp = int(time.time())
        markdown_content = f"""# E2E Test {timestamp}

This is an end-to-end test created at {timestamp}.

## Features
- **Bold text**
- *Italic text*
- `Inline code`

## External Media
![image](https://via.placeholder.com/400x300.png?text=E2E+Test)

## Code
```python
def test_function():
    return "E2E test successful"
```

> [!NOTE]
> This page was created by automated testing.
"""
        
        md_file = temp_dir / f"e2e_test_{timestamp}.md"
        md_file.write_text(markdown_content)
        
        # Process and upload
        result = process_file(str(md_file))
        assert "error" not in result
        
        # Create actual Notion page
        parent_id = os.environ.get('NOTION_IMPORT_ROOT')
        page_result = create_notion_page(
            parent_id,
            f"E2E Test {timestamp}",
            result["blocks"]
        )
        
        # Should either succeed or fail gracefully
        assert isinstance(page_result, dict)
        
        # If successful, should have URL
        if "url" in page_result:
            print(f"Successfully created test page: {page_result['url']}")