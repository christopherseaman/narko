"""
Load tests for concurrent operations and high-throughput scenarios.
Tests system behavior under heavy load and concurrent access patterns.
"""
import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import random
import psutil
import os
from unittest.mock import patch, Mock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from narko import (
    upload_file_to_notion, process_file, generate_file_embedding_data,
    load_upload_cache, save_upload_cache, create_notion_page
)

@pytest.mark.performance
@pytest.mark.slow
class TestConcurrentFileOperations:
    """Test concurrent file processing and upload operations."""
    
    def test_concurrent_file_uploads(self, temp_dir, mock_env_vars):
        """Test multiple simultaneous file uploads."""
        # Create multiple test files
        num_files = 20
        files = []
        for i in range(num_files):
            file_path = temp_dir / f"concurrent_upload_{i}.txt"
            content = f"Content for file {i}\n" * (i + 1)  # Varying sizes
            file_path.write_text(content)
            files.append(file_path)
        
        # Mock API responses
        def mock_api_response(*args, **kwargs):
            # Simulate variable response times
            time.sleep(random.uniform(0.01, 0.1))
            response = Mock()
            response.status_code = 200
            response.json.return_value = {
                "id": f"file-{random.randint(1000, 9999)}",
                "upload_url": "https://test-upload.com"
            }
            return response
        
        with patch('requests.post', side_effect=mock_api_response):
            results = []
            start_time = time.time()
            
            # Use ThreadPoolExecutor for concurrent uploads
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_file = {
                    executor.submit(upload_file_to_notion, str(file_path)): file_path
                    for file_path in files
                }
                
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        result = future.result()
                        results.append((file_path, result))
                    except Exception as e:
                        results.append((file_path, {"error": str(e)}))
            
            total_time = time.time() - start_time
            
            # Verify all uploads completed
            assert len(results) == num_files
            
            # Check success rate
            successful = [r for _, r in results if "error" not in r]
            success_rate = len(successful) / len(results)
            assert success_rate > 0.9  # At least 90% success rate
            
            # Concurrent processing should be faster than sequential
            estimated_sequential_time = num_files * 0.05  # Rough estimate
            assert total_time < estimated_sequential_time
    
    def test_concurrent_markdown_processing(self, temp_dir):
        """Test concurrent processing of multiple markdown files."""
        num_files = 15
        files = []
        
        # Create markdown files with varying complexity
        for i in range(num_files):
            complexity = i % 3  # Low, medium, high complexity
            
            if complexity == 0:  # Simple
                content = f"# Simple Document {i}\n\nBasic content."
            elif complexity == 1:  # Medium
                content = f"""# Medium Document {i}
                
## Features
- **Bold** text
- *Italic* text
- `Code` text

```python
def function_{i}():
    return {i}
```

> [!NOTE]
> This is note {i}
"""
            else:  # Complex
                content = f"""# Complex Document {i}
                
## Math
$$
\\sum_{{j=1}}^{{{i}}} j^2 = \\frac{{{i}({i}+1)(2{i}+1)}}{{6}}
$$

## Table
| Col 1 | Col 2 | Col 3 |
|-------|-------|-------|
""" + "\n".join([f"| Data {j} | Value {j*2} | Result {j**2} |" for j in range(5)]) + f"""

## External Files
![image](https://via.placeholder.com/400x300.png?text=Doc{i})
![pdf](https://example.com/document_{i}.pdf)

## Tasks
""" + "\n".join([f"- [{'x' if j%2==0 else ' '}] Task {j} for document {i}" for j in range(5)])
            
            file_path = temp_dir / f"concurrent_md_{i}.md"
            file_path.write_text(content)
            files.append(file_path)
        
        # Process files concurrently
        results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_file = {
                executor.submit(process_file, str(file_path)): file_path
                for file_path in files
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append((file_path, result))
                except Exception as e:
                    results.append((file_path, {"error": str(e)}))
        
        processing_time = time.time() - start_time
        
        # Verify all files processed
        assert len(results) == num_files
        
        # Check success rate
        successful = [r for _, r in results if "error" not in r[1]]
        assert len(successful) == num_files  # All should succeed
        
        # Verify block counts are reasonable
        total_blocks = sum(len(result["blocks"]) for _, result in successful)
        assert total_blocks > num_files  # Should have multiple blocks per file
        
        # Performance should be reasonable
        assert processing_time < 30.0  # Should complete within 30 seconds
    
    def test_concurrent_cache_operations(self, temp_dir, mock_env_vars):
        """Test concurrent access to upload cache."""
        num_operations = 50
        cache_file = temp_dir / "test_cache.json"
        
        # Patch cache file location
        with patch('narko.UPLOAD_CACHE_FILE', str(cache_file)):
            def cache_operation(op_id):
                """Simulate cache read/write operations."""
                try:
                    # Load cache
                    cache = load_upload_cache()
                    
                    # Simulate processing
                    time.sleep(random.uniform(0.001, 0.01))
                    
                    # Update cache
                    cache[f"hash_{op_id}"] = {
                        "file_id": f"file_{op_id}",
                        "timestamp": time.time(),
                        "size": random.randint(100, 10000)
                    }
                    
                    # Save cache
                    save_upload_cache(cache)
                    
                    return {"success": True, "op_id": op_id}
                except Exception as e:
                    return {"success": False, "op_id": op_id, "error": str(e)}
            
            # Run concurrent cache operations
            results = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(cache_operation, i) for i in range(num_operations)]
                results = [future.result() for future in as_completed(futures)]
            
            # Verify results
            successful = [r for r in results if r["success"]]
            success_rate = len(successful) / len(results)
            
            # Should handle concurrent access reasonably well
            # Some failures are acceptable due to file locking
            assert success_rate > 0.7  # At least 70% success rate
            
            # Verify final cache state
            final_cache = load_upload_cache()
            assert len(final_cache) > 0  # Should have some entries
    
    def test_memory_usage_under_concurrent_load(self, temp_dir):
        """Test memory usage during concurrent operations."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        num_files = 25
        
        def create_and_process_file(file_id):
            """Create and process a file."""
            file_path = temp_dir / f"memory_test_{file_id}.py"
            
            # Create file with substantial content
            content = f'''
"""
File {file_id} for memory testing.
Generated content to test memory usage patterns.
"""

class TestClass{file_id}:
    def __init__(self):
        self.data = {{
            "id": {file_id},
            "values": [i**2 for i in range(100)],
            "metadata": {{
                "created": "2024-01-01",
                "type": "test_data",
                "size": len("test content" * 100)
            }}
        }}
    
    def process_data(self):
        result = []
        for i, value in enumerate(self.data["values"]):
            if value % 2 == 0:
                result.append({{
                    "index": i,
                    "value": value,
                    "processed": True,
                    "timestamp": time.time()
                }})
        return result

def process_test_data_{file_id}():
    """Process test data for file {file_id}."""
    processor = TestClass{file_id}()
    return processor.process_data()
''' * 5  # Repeat to make it larger
            
            file_path.write_text(content)
            
            # Generate embedding data
            embedding_data = generate_file_embedding_data(str(file_path))
            
            # Process as markdown  
            md_content = f"# File {file_id}\n\n![file]({file_path})"
            md_file = temp_dir / f"memory_md_{file_id}.md"
            md_file.write_text(md_content)
            
            result = process_file(str(md_file))
            
            return {
                "file_id": file_id,
                "embedding_ready": embedding_data.get("embedding_ready", False),
                "blocks_count": len(result.get("blocks", []))
            }
        
        # Process files concurrently
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(create_and_process_file, i) for i in range(num_files)]
            results = [future.result() for future in as_completed(futures)]
        
        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Verify processing succeeded
        assert len(results) == num_files
        assert all(r["blocks_count"] > 0 for r in results)
        
        # Memory increase should be reasonable for concurrent processing
        # Allow more memory for concurrent operations
        max_allowed_increase = 200 * 1024 * 1024  # 200MB
        assert memory_increase < max_allowed_increase, \
            f"Memory increase {memory_increase / 1024 / 1024:.1f}MB exceeds limit"

@pytest.mark.performance
@pytest.mark.slow
class TestHighThroughputScenarios:
    """Test high-throughput processing scenarios."""
    
    def test_batch_file_processing(self, temp_dir):
        """Test processing large batches of files."""
        batch_size = 100
        files = []
        
        # Create batch of files
        for i in range(batch_size):
            file_type = ['txt', 'py', 'md', 'json'][i % 4]
            file_path = temp_dir / f"batch_{i}.{file_type}"
            
            if file_type == 'txt':
                content = f"Text file {i} content.\n" * 10
            elif file_type == 'py':
                content = f'def function_{i}():\n    return "File {i}"\n\n' * 5
            elif file_type == 'md':
                content = f"# File {i}\n\nMarkdown content with **bold** text.\n"
            else:  # json
                content = f'{{"file_id": {i}, "data": ["item_{j}" for j in range(10)]}}'
            
            file_path.write_text(content)
            files.append(file_path)
        
        # Process batch
        start_time = time.time()
        
        # Process in smaller concurrent batches to avoid overwhelming system
        batch_size_concurrent = 20
        all_results = []
        
        for i in range(0, len(files), batch_size_concurrent):
            batch = files[i:i + batch_size_concurrent]
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                batch_results = list(executor.map(
                    lambda f: generate_file_embedding_data(str(f)), 
                    batch
                ))
            
            all_results.extend(batch_results)
        
        processing_time = time.time() - start_time
        
        # Verify all files processed
        assert len(all_results) == batch_size
        
        # Check embedding generation success
        embedding_ready_count = sum(1 for r in all_results if r.get("embedding_ready"))
        assert embedding_ready_count > batch_size * 0.8  # At least 80% should be embedding-ready
        
        # Performance should be reasonable
        average_time_per_file = processing_time / batch_size
        assert average_time_per_file < 0.1  # Less than 100ms per file average
    
    def test_large_file_concurrent_processing(self, temp_dir, mock_env_vars):
        """Test concurrent processing of large files."""
        num_large_files = 8
        files = []
        
        # Create large files
        for i in range(num_large_files):
            file_path = temp_dir / f"large_concurrent_{i}.txt"
            # Create files of varying sizes (1-4MB each)
            size_mb = (i % 4) + 1
            content = f"Large file {i} content.\n" * (size_mb * 25000)  # Rough MB equivalent
            file_path.write_text(content)
            files.append(file_path)
        
        def upload_large_file(file_path):
            with patch('requests.post') as mock_post:
                # Simulate longer processing for large files
                time.sleep(random.uniform(0.1, 0.3))
                
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = {
                    "id": f"large-{random.randint(1000, 9999)}",
                    "upload_url": "https://test.com"
                }
                
                return upload_file_to_notion(str(file_path))
        
        # Process large files concurrently
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=4) as executor:  # Fewer workers for large files
            results = list(executor.map(upload_large_file, files))
        
        processing_time = time.time() - start_time
        
        # Verify all uploads completed
        assert len(results) == num_large_files
        
        # Check for size limit violations
        size_errors = [r for r in results if "error" in r and "too large" in r.get("error", "").lower()]
        successful = [r for r in results if "error" not in r]
        
        # Files under 5MB should succeed
        under_limit_files = [f for f in files if os.path.getsize(f) <= 5 * 1024 * 1024]
        expected_successful = len(under_limit_files)
        
        assert len(successful) >= expected_successful * 0.9  # Allow some variance
        
        # Performance should be reasonable even for large files
        assert processing_time < 60.0  # 60 seconds max for large file batch

@pytest.mark.performance
class TestSystemResourceManagement:
    """Test system resource management under load."""
    
    def test_cpu_usage_under_load(self, temp_dir):
        """Test CPU usage during intensive processing."""
        # This test would monitor CPU usage during heavy processing
        # Implementation depends on system monitoring capabilities
        
        num_files = 30
        cpu_percentages = []
        
        def monitor_cpu():
            """Monitor CPU usage in background."""
            for _ in range(20):  # Monitor for ~10 seconds
                cpu_percent = psutil.cpu_percent(interval=0.5)
                cpu_percentages.append(cpu_percent)
        
        # Start CPU monitoring
        import threading
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Create intensive workload
        files = []
        for i in range(num_files):
            file_path = temp_dir / f"cpu_test_{i}.py"
            # Create complex content that requires processing
            content = f'''
"""Complex file {i} for CPU testing."""
import time
import json
from typing import Dict, List, Optional

class ComplexProcessor{i}:
    def __init__(self):
        self.data = {{
            "numbers": list(range(1000)),
            "strings": [f"item_{{j}}" for j in range(500)],
            "nested": {{
                "level1": {{
                    "level2": {{
                        "values": [j**2 for j in range(100)]
                    }}
                }}
            }}
        }}
    
    def process(self) -> Dict:
        result = {{}}
        for i, num in enumerate(self.data["numbers"]):
            if num % 2 == 0:
                result[f"even_{{i}}"] = num * 2
            else:
                result[f"odd_{{i}}"] = num * 3
        return result

def main{i}():
    processor = ComplexProcessor{i}()
    return processor.process()
''' * 3
            
            file_path.write_text(content)
            files.append(file_path)
        
        # Process files and monitor performance
        start_time = time.time()
        
        results = []
        for file_path in files:
            # Generate embedding data (CPU intensive)
            embedding_data = generate_file_embedding_data(str(file_path))
            results.append(embedding_data)
        
        processing_time = time.time() - start_time
        
        # Wait for monitoring to complete
        monitor_thread.join(timeout=5)
        
        # Verify processing succeeded
        assert len(results) == num_files
        assert all(r.get("embedding_ready") for r in results)
        
        # CPU usage should be reasonable (not pegged at 100%)
        if cpu_percentages:
            avg_cpu = sum(cpu_percentages) / len(cpu_percentages)
            max_cpu = max(cpu_percentages)
            
            # Allow high CPU usage but not sustained maximum
            assert avg_cpu < 90.0, f"Average CPU usage too high: {avg_cpu:.1f}%"
            # Allow brief spikes but most readings should be reasonable
            high_cpu_readings = [p for p in cpu_percentages if p > 95]
            assert len(high_cpu_readings) < len(cpu_percentages) * 0.3, "Too many high CPU readings"
    
    def test_file_descriptor_management(self, temp_dir):
        """Test proper file descriptor management."""
        initial_fd_count = len(os.listdir('/proc/self/fd')) if os.path.exists('/proc/self/fd') else None
        
        num_files = 50
        
        # Create and process many files
        for i in range(num_files):
            file_path = temp_dir / f"fd_test_{i}.txt"
            file_path.write_text(f"Content for file descriptor test {i}")
            
            # Process file (involves file I/O)
            embedding_data = generate_file_embedding_data(str(file_path))
            assert embedding_data is not None
            
            # Process as markdown
            md_content = f"# Test {i}\n\n![file]({file_path})"
            md_file = temp_dir / f"fd_md_{i}.md"
            md_file.write_text(md_content)
            
            result = process_file(str(md_file))
            assert "error" not in result
        
        # Check file descriptor count
        if initial_fd_count is not None:
            final_fd_count = len(os.listdir('/proc/self/fd'))
            fd_increase = final_fd_count - initial_fd_count
            
            # Should not leak file descriptors
            assert fd_increase < 10, f"Too many file descriptors leaked: {fd_increase}"