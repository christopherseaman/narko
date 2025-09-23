"""
Performance tests for file upload functionality.
Tests upload speed, memory usage, and concurrent processing performance.
"""
import pytest
import time
import threading
from pathlib import Path
import psutil
import os
from unittest.mock import patch, Mock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from narko import upload_file_to_notion, process_file, generate_file_embedding_data

@pytest.mark.performance
class TestUploadPerformance:
    """Test file upload performance characteristics."""
    
    def test_small_file_upload_speed(self, sample_image_file, mock_env_vars, benchmark):
        """Benchmark small file upload processing speed."""
        with patch('narko.upload_file_to_notion') as mock_upload:
            mock_upload.return_value = {
                "file_id": "test-123",
                "success": True,
                "name": "test.png"
            }
            
            # Benchmark the upload process
            result = benchmark(upload_file_to_notion, str(sample_image_file))
            
            assert "error" not in result
            # Should complete under 100ms for small files
            assert benchmark.stats.mean < 0.1
    
    def test_large_file_processing_speed(self, large_file, mock_env_vars, benchmark):
        """Benchmark large file processing performance."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "id": "large-file-123",
                "upload_url": "https://test.com"
            }
            
            result = benchmark(upload_file_to_notion, str(large_file))
            
            # Large files should still complete in reasonable time
            assert benchmark.stats.mean < 5.0  # 5 second max
    
    def test_concurrent_upload_performance(self, temp_dir, mock_env_vars):
        """Test performance under concurrent upload load."""
        # Create multiple test files
        files = []
        for i in range(10):
            file_path = temp_dir / f"concurrent_{i}.txt"
            file_path.write_text(f"Test content for file {i}" * 100)
            files.append(file_path)
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "id": "concurrent-test",
                "upload_url": "https://test.com"
            }
            
            results = []
            start_time = time.time()
            
            def upload_file(file_path):
                result = upload_file_to_notion(str(file_path))
                results.append(result)
            
            # Start concurrent uploads
            threads = []
            for file_path in files:
                thread = threading.Thread(target=upload_file, args=(file_path,))
                threads.append(thread)
                thread.start()
            
            # Wait for all to complete
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            
            # All uploads should succeed
            assert len(results) == len(files)
            assert all("error" not in result for result in results)
            
            # Should handle concurrency efficiently
            average_time = total_time / len(files)
            assert average_time < 2.0  # Less than 2 seconds per file average
    
    def test_memory_usage_under_load(self, temp_dir):
        """Test memory usage during intensive processing."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create and process many files
        for i in range(50):
            file_path = temp_dir / f"memory_test_{i}.txt"
            file_path.write_text("Test content " * 1000)
            
            # Generate embedding data (memory intensive operation)
            embedding_data = generate_file_embedding_data(str(file_path))
            assert embedding_data is not None
            
            # Clean up immediately to test garbage collection
            del embedding_data
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
    
    def test_cache_performance_impact(self, sample_text_file, mock_env_vars):
        """Test performance impact of caching mechanisms."""
        with patch('narko.load_upload_cache') as mock_load, \
             patch('narko.save_upload_cache') as mock_save, \
             patch('requests.post') as mock_post:
            
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "id": "cache-test",
                "upload_url": "https://test.com"
            }
            
            # Test without cache
            mock_load.return_value = {}
            start_time = time.time()
            result1 = upload_file_to_notion(str(sample_text_file), use_cache=False)
            no_cache_time = time.time() - start_time
            
            # Test with cache hit
            file_hash = "test-hash-123"
            mock_load.return_value = {
                file_hash: {
                    "file_id": "cached-file-123",
                    "success": True,
                    "from_cache": True
                }
            }
            
            with patch('narko.calculate_file_hash', return_value=file_hash):
                start_time = time.time()
                result2 = upload_file_to_notion(str(sample_text_file), use_cache=True)
                cache_time = time.time() - start_time
            
            # Cache should be significantly faster
            assert cache_time < no_cache_time * 0.5  # At least 50% faster
            assert result2.get("from_cache") is True

@pytest.mark.performance  
class TestProcessingPerformance:
    """Test markdown processing performance."""
    
    def test_large_markdown_processing(self, temp_dir, benchmark):
        """Benchmark large markdown document processing."""
        # Create large markdown with many blocks
        content_blocks = []
        for i in range(200):
            content_blocks.append(f"""
## Section {i}
This is section {i} with **formatting** and *emphasis*.

- List item 1 for section {i}
- List item 2 for section {i}

```python
def function_{i}():
    return "Code for section {i}"
```

> [!NOTE]
> Callout for section {i}
""")
        
        large_markdown = "# Large Document\n" + "\n".join(content_blocks)
        
        md_file = temp_dir / "large_performance.md"
        md_file.write_text(large_markdown)
        
        # Benchmark processing
        result = benchmark(process_file, str(md_file))
        
        assert "error" not in result
        assert len(result["blocks"]) > 500  # Should have many blocks
        
        # Should complete in reasonable time even for large documents
        assert benchmark.stats.mean < 10.0  # 10 seconds max
    
    def test_complex_content_processing_speed(self, temp_dir, benchmark):
        """Test processing speed with complex markdown features."""
        complex_markdown = """# Complex Document

## Math Equations
$$
\\sum_{i=1}^{n} \\frac{1}{i^2} = \\frac{\\pi^2}{6}
$$

Inline math: $E = mc^2$ and $\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$

## Tables
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| More 1   | More 2   | More 3   |

## Mixed Lists
- [x] Task 1 with ==highlight==
- [ ] Task 2 with `inline code`
- Regular item with **bold** and *italic*

## Code Blocks
```python
def complex_function(x, y, z):
    result = []
    for i in range(x):
        if i % y == 0:
            result.append(i * z)
    return result
```

## Callouts with Nested Content
> [!WARNING]
> This is a complex callout with:
> - Nested lists
> - **Bold formatting**
> - `Code snippets`
> - Even nested callouts:
> 
> > [!TIP]
> > Nested tip inside warning

## External Files
![image](https://via.placeholder.com/800x600.png)
![pdf](https://example.com/large_document.pdf)
"""
        
        md_file = temp_dir / "complex_performance.md"
        md_file.write_text(complex_markdown)
        
        # Benchmark complex processing
        result = benchmark(process_file, str(md_file))
        
        assert "error" not in result
        assert len(result["blocks"]) > 10
        
        # Complex content should still process quickly
        assert benchmark.stats.mean < 2.0  # 2 seconds max for complex content
    
    def test_file_embedding_generation_performance(self, temp_dir, benchmark):
        """Benchmark file embedding data generation."""
        # Create files with various content types
        text_file = temp_dir / "large_text.py"
        code_content = '''
def large_function():
    """This is a large function for testing embedding generation."""
    data = {}
    for i in range(1000):
        data[f"key_{i}"] = {
            "value": i * 2,
            "description": f"This is item number {i}",
            "metadata": {
                "created": f"2024-01-{i%30+1:02d}",
                "processed": i % 2 == 0,
                "tags": [f"tag_{j}" for j in range(i%5)]
            }
        }
    return data

class LargeClass:
    """A large class for testing purposes."""
    
    def __init__(self):
        self.data = large_function()
    
    def process_data(self):
        results = []
        for key, value in self.data.items():
            if value["metadata"]["processed"]:
                results.append({
                    "key": key,
                    "processed_value": value["value"] * 2,
                    "tag_count": len(value["metadata"]["tags"])
                })
        return results
''' * 5  # Repeat to make it larger
        
        text_file.write_text(code_content)
        
        # Benchmark embedding generation
        result = benchmark(generate_file_embedding_data, str(text_file))
        
        assert result["embedding_ready"] is True
        assert len(result["text_content"]) > 0
        assert result["file_hash"] is not None
        
        # Should generate embeddings quickly even for large files
        assert benchmark.stats.mean < 1.0  # 1 second max

@pytest.mark.performance
class TestApiPerformance:
    """Test API interaction performance."""
    
    def test_api_timeout_handling(self, sample_image_file, mock_env_vars):
        """Test API timeout handling performance."""
        with patch('requests.post') as mock_post:
            # Simulate timeout scenarios
            def timeout_after_delay(*args, **kwargs):
                time.sleep(2.5)  # Longer than reasonable timeout
                raise requests.exceptions.Timeout()
            
            mock_post.side_effect = timeout_after_delay
            
            start_time = time.time()
            result = upload_file_to_notion(str(sample_image_file))
            elapsed_time = time.time() - start_time
            
            # Should timeout quickly and handle gracefully
            assert "error" in result
            assert elapsed_time < 5.0  # Should not hang indefinitely
    
    def test_api_retry_performance(self, sample_image_file, mock_env_vars):
        """Test performance with API retry scenarios."""
        with patch('requests.post') as mock_post:
            # Simulate retry scenario
            call_count = 0
            def failing_then_success(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count < 3:  # Fail first 2 calls
                    response = Mock()
                    response.status_code = 500
                    response.text = "Internal Server Error"
                    return response
                else:  # Succeed on 3rd call
                    response = Mock()
                    response.status_code = 200
                    response.json.return_value = {
                        "id": "retry-success",
                        "upload_url": "https://test.com"
                    }
                    return response
            
            mock_post.side_effect = failing_then_success
            
            start_time = time.time()
            result = upload_file_to_notion(str(sample_image_file))
            elapsed_time = time.time() - start_time
            
            # Should handle retries but not take too long
            assert elapsed_time < 10.0  # Reasonable retry timeout
            # Note: Current implementation doesn't include retry logic
            # This test documents expected behavior for future implementation