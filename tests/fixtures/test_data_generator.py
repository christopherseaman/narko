"""
Test data generator utilities for creating comprehensive test fixtures.
Provides realistic test data for various file types and scenarios.
"""
import json
import random
import string
from pathlib import Path
from typing import Dict, List, Optional, Any
import base64


class TestDataGenerator:
    """Generate test data for various file types and scenarios."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def create_sample_files(self) -> Dict[str, Path]:
        """Create a comprehensive set of sample files for testing."""
        files = {}
        
        # Text files
        files['simple_text'] = self._create_text_file("simple.txt", "Simple text content for testing.")
        files['large_text'] = self._create_large_text_file()
        files['unicode_text'] = self._create_unicode_text_file()
        
        # Code files
        files['python_code'] = self._create_python_file()
        files['javascript_code'] = self._create_javascript_file()
        files['json_data'] = self._create_json_file()
        
        # Markdown files
        files['simple_markdown'] = self._create_simple_markdown()
        files['complex_markdown'] = self._create_complex_markdown()
        files['markdown_with_files'] = self._create_markdown_with_file_refs(list(files.values()))
        
        # Binary files
        files['small_image'] = self._create_minimal_png()
        files['pdf_placeholder'] = self._create_pdf_placeholder()
        
        # Edge case files
        files['empty_file'] = self._create_empty_file()
        files['very_long_name'] = self._create_long_filename_file()
        files['special_chars'] = self._create_special_chars_file()
        
        return files
    
    def _create_text_file(self, name: str, content: str) -> Path:
        """Create a simple text file."""
        file_path = self.base_dir / name
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    def _create_large_text_file(self) -> Path:
        """Create a large text file for performance testing."""
        content_lines = []
        
        # Generate realistic large text content
        for i in range(1000):
            content_lines.append(f"Line {i}: This is a sample line with content number {i}.")
            if i % 10 == 0:
                content_lines.append(f"\nSection {i//10}:")
                content_lines.append("-" * 40)
            if i % 50 == 0:
                content_lines.append(f"\n\nChapter {i//50}: Advanced Topics")
                content_lines.append("=" * 50)
        
        content = "\n".join(content_lines)
        return self._create_text_file("large_text.txt", content)
    
    def _create_unicode_text_file(self) -> Path:
        """Create text file with Unicode content."""
        content = """Unicode Test File
文本文件测试 (Chinese)
Тестовый текстовый файл (Russian)  
ファイルテスト (Japanese)
اختبار الملف (Arabic)
Δοκιμαστικό αρχείο (Greek)

Emoji content: 🚀 📁 💾 🔥 ⚡ 🌟 🎯 🛠️

Mathematical symbols: ∑ ∫ ∆ ∇ ∞ ≈ ≠ ≤ ≥

Special characters: «» ‚„ ‹› ""'' –—

Currency: $ € £ ¥ ₹ ₽ ₿
"""
        return self._create_text_file("unicode_test.txt", content)
    
    def _create_python_file(self) -> Path:
        """Create a Python code file."""
        content = '''#!/usr/bin/env python3
"""
Sample Python file for testing file upload and embedding generation.
Contains various Python language features.
"""
import json
import re
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestData:
    """Test data class for demonstration."""
    id: int
    name: str
    values: List[float]
    metadata: Optional[Dict[str, str]] = None


class SampleProcessor:
    """Sample class for processing test data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.processed_count = 0
    
    def process_item(self, item: TestData) -> Dict[str, Any]:
        """Process a single test item."""
        result = {
            "id": item.id,
            "processed_name": item.name.upper(),
            "value_sum": sum(item.values),
            "value_avg": sum(item.values) / len(item.values) if item.values else 0
        }
        
        if item.metadata:
            result.update(item.metadata)
        
        self.processed_count += 1
        return result
    
    def process_batch(self, items: List[TestData]) -> List[Dict[str, Any]]:
        """Process multiple items."""
        return [self.process_item(item) for item in items]
    
    @staticmethod
    def validate_config(config: Dict) -> bool:
        """Validate configuration."""
        required_keys = ['input_path', 'output_path', 'format']
        return all(key in config for key in required_keys)


def main():
    """Main function for testing."""
    config = {
        'input_path': '/tmp/input.json',
        'output_path': '/tmp/output.json', 
        'format': 'json'
    }
    
    if SampleProcessor.validate_config(config):
        processor = SampleProcessor(config)
        
        # Create sample data
        sample_items = [
            TestData(i, f"item_{i}", [random.random() for _ in range(5)])
            for i in range(10)
        ]
        
        # Process data
        results = processor.process_batch(sample_items)
        
        print(f"Processed {len(results)} items")
        return results
    
    return None


if __name__ == "__main__":
    results = main()
    if results:
        print(json.dumps(results, indent=2))
'''
        return self._create_text_file("sample_code.py", content)
    
    def _create_javascript_file(self) -> Path:
        """Create a JavaScript code file."""
        content = '''/**
 * Sample JavaScript file for testing file upload functionality.
 * Contains modern ES6+ features and common patterns.
 */

class DataProcessor {
    constructor(options = {}) {
        this.options = {
            batchSize: 100,
            timeout: 5000,
            retries: 3,
            ...options
        };
        
        this.processed = new Map();
        this.errors = [];
    }
    
    async processData(data) {
        try {
            const batches = this.createBatches(data);
            const results = [];
            
            for (const batch of batches) {
                const batchResult = await this.processBatch(batch);
                results.push(...batchResult);
            }
            
            return results;
        } catch (error) {
            this.errors.push(error);
            throw error;
        }
    }
    
    createBatches(data) {
        const batches = [];
        const { batchSize } = this.options;
        
        for (let i = 0; i < data.length; i += batchSize) {
            batches.push(data.slice(i, i + batchSize));
        }
        
        return batches;
    }
    
    async processBatch(batch) {
        const promises = batch.map(item => this.processItem(item));
        return Promise.allSettled(promises);
    }
    
    async processItem(item) {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                try {
                    const result = {
                        id: item.id,
                        processed: true,
                        timestamp: Date.now(),
                        value: item.value * 2
                    };
                    
                    this.processed.set(item.id, result);
                    resolve(result);
                } catch (error) {
                    reject(error);
                }
            }, Math.random() * 100);
        });
    }
    
    getStats() {
        return {
            processed: this.processed.size,
            errors: this.errors.length,
            successRate: this.processed.size / (this.processed.size + this.errors.length)
        };
    }
}

// Utility functions
const utils = {
    formatDate: (date) => date.toISOString().split('T')[0],
    
    debounce: (func, wait) => {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    },
    
    chunk: (array, size) => {
        return Array.from({ length: Math.ceil(array.length / size) }, (_, i) =>
            array.slice(i * size, i * size + size)
        );
    }
};

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DataProcessor, utils };
}

// Example usage
const processor = new DataProcessor({ batchSize: 50 });
const sampleData = Array.from({ length: 200 }, (_, i) => ({
    id: i,
    value: Math.random() * 100,
    timestamp: Date.now()
}));

processor.processData(sampleData)
    .then(results => console.log('Processing complete:', results.length))
    .catch(error => console.error('Processing failed:', error));
'''
        return self._create_text_file("sample_code.js", content)
    
    def _create_json_file(self) -> Path:
        """Create a JSON data file."""
        data = {
            "config": {
                "version": "1.0.0",
                "environment": "test",
                "features": {
                    "file_upload": True,
                    "caching": True,
                    "compression": False
                }
            },
            "test_data": [
                {
                    "id": i,
                    "name": f"Test Item {i}",
                    "values": [random.randint(1, 100) for _ in range(5)],
                    "metadata": {
                        "created": "2024-01-01T00:00:00Z",
                        "type": "test",
                        "tags": [f"tag_{j}" for j in range(i % 3 + 1)]
                    }
                }
                for i in range(20)
            ],
            "api_endpoints": {
                "upload": "/api/v1/upload",
                "status": "/api/v1/status", 
                "download": "/api/v1/download/{id}"
            },
            "supported_formats": [
                "json", "xml", "yaml", "csv", "txt", "md",
                "png", "jpg", "gif", "pdf", "doc", "docx"
            ]
        }
        
        content = json.dumps(data, indent=2)
        return self._create_text_file("test_data.json", content)
    
    def _create_simple_markdown(self) -> Path:
        """Create a simple markdown file."""
        content = """# Simple Test Document

This is a simple markdown document for testing purposes.

## Features

- **Bold text**
- *Italic text*  
- `Inline code`
- [Links](https://example.com)

## Code Block

```python
def hello():
    print("Hello, World!")
```

## List

1. First item
2. Second item
3. Third item

That's all for this simple test!
"""
        return self._create_text_file("simple_test.md", content)
    
    def _create_complex_markdown(self) -> Path:
        """Create a complex markdown file with advanced features."""
        content = """# Complex Test Document

This document tests various advanced markdown features.

## Mathematical Equations

Block equation:
$$
\\sum_{i=1}^{n} \\frac{1}{i^2} = \\frac{\\pi^2}{6}
$$

Inline equation: $E = mc^2$ and $\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$

## Task Lists

- [x] Completed task
- [x] Another completed task
- [ ] Pending task  
- [ ] Future task

## Callouts

> [!NOTE]
> This is an informational note with important details.

> [!WARNING]  
> This is a warning about potential issues.

> [!TIP]
> Here's a helpful tip for users.

## Tables

| Feature | Status | Priority |
|---------|--------|----------|
| File Upload | ✅ Done | High |
| Caching | 🔄 In Progress | Medium |
| Security | ⏳ Planned | High |
| Analytics | ❌ Not Started | Low |

## Code Blocks with Languages

Python code:
```python
class TestRunner:
    def __init__(self, config):
        self.config = config
    
    def run_tests(self):
        return "Tests completed"
```

JavaScript code:
```javascript
const testRunner = {
    config: {},
    async runTests() {
        return "Tests completed";
    }
};
```

JSON data:
```json
{
    "test": true,
    "count": 42,
    "items": ["one", "two", "three"]
}
```

## Nested Lists

1. First level
   - Sub item 1
   - Sub item 2
     - Sub-sub item
     - Another sub-sub item
   - Sub item 3
2. Second level
   1. Numbered sub item
   2. Another numbered sub item
3. Third level

## Highlighting

This text has ==highlighted== portions for emphasis.

## Mixed Content

Here's a paragraph with **bold**, *italic*, `code`, and [link](https://example.com) elements.

> Block quote with **formatting** and `code` inside.

Final paragraph to wrap up this complex document.
"""
        return self._create_text_file("complex_test.md", content)
    
    def _create_markdown_with_file_refs(self, existing_files: List[Path]) -> Path:
        """Create markdown with file upload references."""
        content = """# Document with File References

This document contains references to various file types.

## Local Files

"""
        
        # Add references to existing test files
        for file_path in existing_files[:5]:  # Limit to first 5 files
            relative_path = file_path.relative_to(self.base_dir)
            file_ext = file_path.suffix.lower()
            
            if file_ext in ['.png', '.jpg', '.gif']:
                content += f"![image:Sample Image]({relative_path})\n\n"
            elif file_ext == '.pdf':
                content += f"![pdf:Sample PDF]({relative_path})\n\n"
            elif file_ext in ['.mp4', '.mov']:
                content += f"![video:Sample Video]({relative_path})\n\n"
            else:
                content += f"![file:Sample File]({relative_path})\n\n"
        
        content += """## External Files

![image](https://via.placeholder.com/400x300.png?text=External+Image)
![pdf](https://example.com/sample_document.pdf)
![video](https://example.com/sample_video.mp4)

## Mixed Content with Files

Here's a callout with a file reference:

> [!TIP]
> Check out this diagram: ![image](https://via.placeholder.com/300x200.png?text=Diagram)

Task list with files:
- [x] Review document: ![file](./simple.txt)
- [ ] Process data: ![file](./test_data.json)
- [ ] Generate report

## Code with File References

```python
# Load configuration
with open('./test_data.json', 'r') as f:
    config = json.load(f)

# Process image
image_path = './sample_image.png'
if os.path.exists(image_path):
    process_image(image_path)
```

End of document with file references.
"""
        return self._create_text_file("markdown_with_files.md", content)
    
    def _create_minimal_png(self) -> Path:
        """Create a minimal PNG file."""
        # Minimal PNG data (1x1 transparent pixel)
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13'
            b'\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```'
            b'\x00\x00\x00\x02\x00\x01H\xafDe\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        file_path = self.base_dir / "sample_image.png"
        file_path.write_bytes(png_data)
        return file_path
    
    def _create_pdf_placeholder(self) -> Path:
        """Create a PDF placeholder file."""
        # This creates a text file that represents a PDF for testing
        # In real scenarios, you'd use a PDF library to create actual PDFs
        content = """%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
50 700 Td
(Test PDF Document) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000189 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
285
%%EOF"""
        
        file_path = self.base_dir / "sample_document.pdf"
        file_path.write_text(content)
        return file_path
    
    def _create_empty_file(self) -> Path:
        """Create an empty file for edge case testing."""
        file_path = self.base_dir / "empty_file.txt"
        file_path.touch()
        return file_path
    
    def _create_long_filename_file(self) -> Path:
        """Create file with very long filename."""
        # Create a long but valid filename
        long_name = "very_long_filename_" + "x" * 100 + ".txt"
        file_path = self.base_dir / long_name
        
        try:
            file_path.write_text("Content of file with very long name")
            return file_path
        except OSError:
            # Fallback if filename too long for filesystem
            fallback_path = self.base_dir / "long_filename_test.txt"
            fallback_path.write_text("Content of file with long name (fallback)")
            return fallback_path
    
    def _create_special_chars_file(self) -> Path:
        """Create file with special characters in name and content."""
        filename = "special_chars_测试_🚀.txt"
        content = """File with special characters test.

Unicode content:
- Chinese: 你好世界
- Russian: Привет мир  
- Arabic: مرحبا بالعالم
- Emoji: 🚀 📁 💾 ⚡ 🌟

Special symbols: ≈ ≠ ≤ ≥ ∞ ∑ ∫ ∆

Quotes: "double" 'single' «guillemets» 'curly' "curly"

Mathematical: α β γ δ ε π θ λ μ σ φ ω
"""
        
        file_path = self.base_dir / filename
        try:
            file_path.write_text(content, encoding='utf-8')
            return file_path
        except (OSError, UnicodeError):
            # Fallback if special characters not supported
            fallback_path = self.base_dir / "special_chars_test.txt"
            fallback_path.write_text(content, encoding='utf-8')
            return fallback_path
    
    def create_test_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Create test scenarios with expected outcomes."""
        return {
            "valid_small_file": {
                "file": self._create_text_file("valid_small.txt", "Small valid content"),
                "expected": {
                    "should_upload": True,
                    "embedding_ready": True,
                    "file_type": "text"
                }
            },
            "valid_large_file": {
                "file": self._create_text_file("valid_large.txt", "x" * (4 * 1024 * 1024)),  # 4MB
                "expected": {
                    "should_upload": True,
                    "embedding_ready": True,
                    "file_type": "text",
                    "size_warning": False
                }
            },
            "oversized_file": {
                "file": self._create_text_file("oversized.txt", "x" * (6 * 1024 * 1024)),  # 6MB
                "expected": {
                    "should_upload": False,
                    "error_type": "size_limit",
                    "embedding_ready": False
                }
            },
            "empty_file": {
                "file": self._create_empty_file(),
                "expected": {
                    "should_upload": True,
                    "embedding_ready": False,
                    "size": 0
                }
            },
            "binary_file": {
                "file": self._create_minimal_png(),
                "expected": {
                    "should_upload": True,
                    "embedding_ready": False,
                    "file_type": "image"
                }
            }
        }


# Utility function for tests
def setup_comprehensive_test_data(temp_dir: Path) -> Dict[str, Any]:
    """Set up comprehensive test data for testing."""
    generator = TestDataGenerator(temp_dir)
    
    files = generator.create_sample_files()
    scenarios = generator.create_test_scenarios()
    
    return {
        "files": files,
        "scenarios": scenarios,
        "generator": generator
    }