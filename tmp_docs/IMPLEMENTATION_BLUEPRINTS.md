# Implementation Blueprints for Enhanced File Upload System

## 1. Asynchronous File Processing Architecture

### Core AsyncFileProcessor Implementation

```python
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
import logging

@dataclass
class ProcessingResult:
    file_path: Path
    success: bool
    file_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None
    processing_time: float = 0.0

class AsyncFileProcessor:
    def __init__(self, max_workers: int = 5, max_queue_size: int = 100):
        self.semaphore = asyncio.Semaphore(max_workers)
        self.processing_queue = asyncio.Queue(maxsize=max_queue_size)
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.progress_callbacks: List[Callable] = []
        self.logger = logging.getLogger(__name__)
    
    async def process_files_batch(self, files: List[Path]) -> List[ProcessingResult]:
        """Process multiple files concurrently with progress tracking"""
        if not files:
            return []
        
        # Create processing tasks
        tasks = []
        for i, file_path in enumerate(files):
            task = self._process_single_file(file_path, i, len(files))
            tasks.append(task)
        
        # Execute with progress monitoring
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions and convert to results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ProcessingResult(
                    file_path=files[i],
                    success=False,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _process_single_file(self, file_path: Path, index: int, total: int) -> ProcessingResult:
        """Process a single file with semaphore control"""
        async with self.semaphore:
            start_time = asyncio.get_event_loop().time()
            
            try:
                # Notify progress callbacks
                await self._notify_progress(index, total, file_path, "processing")
                
                # Extract metadata and content
                metadata = await self._extract_metadata(file_path)
                content_data = await self._extract_content(file_path)
                
                # Upload to Notion
                upload_result = await self._upload_to_notion(file_path, metadata)
                
                # Generate embeddings if applicable
                if content_data and content_data.get('extractable'):
                    embedding_result = await self._generate_embeddings(content_data)
                    metadata['embedding'] = embedding_result
                
                processing_time = asyncio.get_event_loop().time() - start_time
                
                # Notify completion
                await self._notify_progress(index, total, file_path, "completed")
                
                return ProcessingResult(
                    file_path=file_path,
                    success=True,
                    file_id=upload_result.get('file_id'),
                    metadata=metadata,
                    processing_time=processing_time
                )
                
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {str(e)}")
                await self._notify_progress(index, total, file_path, "error", str(e))
                
                return ProcessingResult(
                    file_path=file_path,
                    success=False,
                    error=str(e),
                    processing_time=asyncio.get_event_loop().time() - start_time
                )
    
    async def _extract_metadata(self, file_path: Path) -> Dict:
        """Extract file metadata asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.thread_pool, 
            generate_file_embedding_data, 
            str(file_path)
        )
    
    async def _extract_content(self, file_path: Path) -> Optional[Dict]:
        """Extract content for embedding generation"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.thread_pool,
            self._sync_extract_content,
            file_path
        )
    
    def _sync_extract_content(self, file_path: Path) -> Optional[Dict]:
        """Synchronous content extraction for thread pool"""
        # Enhanced extraction logic here
        return extract_text_content(str(file_path))
    
    async def _upload_to_notion(self, file_path: Path, metadata: Dict) -> Dict:
        """Upload file to Notion with retry logic"""
        return await self._with_retry(
            lambda: upload_file_to_notion(str(file_path)),
            max_attempts=3
        )
    
    async def _generate_embeddings(self, content_data: Dict) -> Dict:
        """Generate embeddings for content"""
        # Placeholder for embedding generation
        return {"status": "pending", "content_hash": content_data.get("file_hash")}
    
    async def _with_retry(self, operation: Callable, max_attempts: int = 3) -> Dict:
        """Execute operation with exponential backoff retry"""
        for attempt in range(max_attempts):
            try:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(self.thread_pool, operation)
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e
                
                wait_time = (2 ** attempt) + (0.1 * attempt)  # Exponential backoff
                await asyncio.sleep(wait_time)
    
    async def _notify_progress(self, index: int, total: int, file_path: Path, 
                             status: str, error: str = None):
        """Notify progress to registered callbacks"""
        progress_data = {
            'index': index,
            'total': total,
            'file_path': str(file_path),
            'status': status,
            'percentage': (index + 1) / total * 100,
            'error': error
        }
        
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(progress_data)
                else:
                    callback(progress_data)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {e}")
    
    def add_progress_callback(self, callback: Callable):
        """Add a progress callback function"""
        self.progress_callbacks.append(callback)
```

## 2. Enhanced Content Extraction System

```python
import pytesseract
from PIL import Image
import PyPDF2
from docx import Document
import ast
import json
from typing import Dict, Optional, Union
import mimetypes

class ContentExtractor:
    def __init__(self):
        self.extractors = {
            '.pdf': self._extract_pdf,
            '.docx': self._extract_docx,
            '.doc': self._extract_doc,
            '.txt': self._extract_text,
            '.md': self._extract_markdown,
            '.py': self._extract_python,
            '.js': self._extract_javascript,
            '.json': self._extract_json,
            '.png': self._extract_image_text,
            '.jpg': self._extract_image_text,
            '.jpeg': self._extract_image_text,
        }
    
    def extract_content(self, file_path: Path) -> Optional[Dict]:
        """Extract content based on file type"""
        suffix = file_path.suffix.lower()
        extractor = self.extractors.get(suffix)
        
        if not extractor:
            return self._extract_basic_metadata(file_path)
        
        try:
            return extractor(file_path)
        except Exception as e:
            return {
                'error': str(e),
                'file_path': str(file_path),
                'extractable': False
            }
    
    def _extract_pdf(self, file_path: Path) -> Dict:
        """Enhanced PDF text extraction"""
        text_content = ""
        metadata = {}
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            metadata = {
                'pages': len(pdf_reader.pages),
                'title': pdf_reader.metadata.get('/Title', ''),
                'author': pdf_reader.metadata.get('/Author', ''),
                'subject': pdf_reader.metadata.get('/Subject', ''),
            }
            
            # Extract text from all pages
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    text_content += f"\\n--- Page {page_num + 1} ---\\n{page_text}"
                except Exception as e:
                    text_content += f"\\n--- Page {page_num + 1} (extraction failed) ---\\n"
        
        return {
            'text_content': text_content[:10000],  # Limit to first 10KB
            'metadata': metadata,
            'extractable': True,
            'content_type': 'pdf_document',
            'language': self._detect_language(text_content[:1000])
        }
    
    def _extract_docx(self, file_path: Path) -> Dict:
        """Extract content from Word documents"""
        doc = Document(file_path)
        
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text_content = '\\n'.join(paragraphs)
        
        # Extract metadata
        props = doc.core_properties
        metadata = {
            'title': props.title or '',
            'author': props.author or '',
            'subject': props.subject or '',
            'created': str(props.created) if props.created else '',
            'modified': str(props.modified) if props.modified else '',
            'paragraphs': len(paragraphs)
        }
        
        return {
            'text_content': text_content[:10000],
            'metadata': metadata,
            'extractable': True,
            'content_type': 'word_document',
            'language': self._detect_language(text_content[:1000])
        }
    
    def _extract_python(self, file_path: Path) -> Dict:
        """Extract structure and documentation from Python files"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        try:
            tree = ast.parse(content)
            analysis = {
                'functions': [],
                'classes': [],
                'imports': [],
                'docstrings': []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis['functions'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node)
                    })
                elif isinstance(node, ast.ClassDef):
                    analysis['classes'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node)
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis['imports'].append(alias.name)
                    else:
                        analysis['imports'].append(f"{node.module}.{alias.name}" 
                                                 for alias in node.names)
            
            return {
                'text_content': content[:10000],
                'code_analysis': analysis,
                'metadata': {
                    'file_type': 'python',
                    'lines': len(content.split('\\n')),
                    'functions': len(analysis['functions']),
                    'classes': len(analysis['classes']),
                    'imports': len(analysis['imports'])
                },
                'extractable': True,
                'content_type': 'source_code'
            }
            
        except SyntaxError:
            return {
                'text_content': content[:10000],
                'metadata': {'file_type': 'python', 'syntax_error': True},
                'extractable': True,
                'content_type': 'source_code'
            }
    
    def _extract_image_text(self, file_path: Path) -> Dict:
        """Extract text from images using OCR"""
        try:
            image = Image.open(file_path)
            text_content = pytesseract.image_to_string(image)
            
            # Get image metadata
            metadata = {
                'dimensions': image.size,
                'format': image.format,
                'mode': image.mode,
                'has_text': len(text_content.strip()) > 0
            }
            
            return {
                'text_content': text_content[:5000],  # Limit OCR text
                'metadata': metadata,
                'extractable': len(text_content.strip()) > 0,
                'content_type': 'image_with_text',
                'ocr_confidence': self._estimate_ocr_confidence(text_content)
            }
            
        except Exception as e:
            return {
                'error': f"OCR extraction failed: {str(e)}",
                'extractable': False,
                'content_type': 'image'
            }
    
    def _extract_json(self, file_path: Path) -> Dict:
        """Extract and analyze JSON structure"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        try:
            data = json.loads(content)
            structure_analysis = self._analyze_json_structure(data)
            
            return {
                'text_content': content[:10000],
                'json_structure': structure_analysis,
                'metadata': {
                    'file_type': 'json',
                    'size_bytes': len(content),
                    'structure_depth': structure_analysis.get('max_depth', 0),
                    'total_keys': structure_analysis.get('total_keys', 0)
                },
                'extractable': True,
                'content_type': 'structured_data'
            }
            
        except json.JSONDecodeError as e:
            return {
                'text_content': content[:10000],
                'metadata': {'file_type': 'json', 'parse_error': str(e)},
                'extractable': True,
                'content_type': 'text_data'
            }
    
    def _analyze_json_structure(self, data, depth=0) -> Dict:
        """Analyze JSON structure recursively"""
        analysis = {
            'max_depth': depth,
            'total_keys': 0,
            'types_found': set(),
            'array_lengths': []
        }
        
        if isinstance(data, dict):
            analysis['total_keys'] += len(data)
            for key, value in data.items():
                analysis['types_found'].add(type(value).__name__)
                if isinstance(value, (dict, list)):
                    sub_analysis = self._analyze_json_structure(value, depth + 1)
                    analysis['max_depth'] = max(analysis['max_depth'], sub_analysis['max_depth'])
                    analysis['total_keys'] += sub_analysis['total_keys']
                    analysis['types_found'].update(sub_analysis['types_found'])
                    analysis['array_lengths'].extend(sub_analysis['array_lengths'])
        
        elif isinstance(data, list):
            analysis['array_lengths'].append(len(data))
            for item in data:
                if isinstance(item, (dict, list)):
                    sub_analysis = self._analyze_json_structure(item, depth + 1)
                    analysis['max_depth'] = max(analysis['max_depth'], sub_analysis['max_depth'])
                    analysis['total_keys'] += sub_analysis['total_keys']
                    analysis['types_found'].update(sub_analysis['types_found'])
                    analysis['array_lengths'].extend(sub_analysis['array_lengths'])
        
        # Convert set to list for JSON serialization
        analysis['types_found'] = list(analysis['types_found'])
        return analysis
    
    def _detect_language(self, text_sample: str) -> str:
        """Simple language detection based on common words"""
        # Simplified language detection - in production use langdetect library
        english_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = set(text_sample.lower().split())
        english_score = len(words.intersection(english_words))
        
        return 'en' if english_score > 2 else 'unknown'
    
    def _estimate_ocr_confidence(self, text: str) -> float:
        """Estimate OCR confidence based on text characteristics"""
        if not text.strip():
            return 0.0
        
        # Simple heuristic based on word ratio and special characters
        words = text.split()
        if not words:
            return 0.0
        
        valid_words = sum(1 for word in words if word.isalnum() and len(word) > 1)
        word_ratio = valid_words / len(words)
        
        return min(word_ratio, 1.0)
    
    def _extract_basic_metadata(self, file_path: Path) -> Dict:
        """Extract basic metadata for unsupported file types"""
        stat = file_path.stat()
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        return {
            'metadata': {
                'file_name': file_path.name,
                'file_size': stat.st_size,
                'mime_type': mime_type,
                'modified_time': stat.st_mtime,
                'file_extension': file_path.suffix.lower()
            },
            'extractable': False,
            'content_type': 'binary_file'
        }
```

## 3. Vector Database Integration

```python
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Optional, Tuple
import sqlite3
import json
from datetime import datetime

class EmbeddingStore:
    def __init__(self, collection_name: str = "narko_embeddings", 
                 persist_directory: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Narko file embeddings and metadata"}
            )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize metadata database
        self.metadata_db_path = f"{persist_directory}/metadata.db"
        self._init_metadata_db()
    
    def _init_metadata_db(self):
        """Initialize SQLite database for file metadata"""
        conn = sqlite3.connect(self.metadata_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_metadata (
                file_hash TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                content_type TEXT,
                embedding_id TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                extraction_metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_file_path ON file_metadata(file_path);
            CREATE INDEX IF NOT EXISTS idx_content_type ON file_metadata(content_type);
            CREATE INDEX IF NOT EXISTS idx_created_at ON file_metadata(created_at);
        ''')
        
        conn.commit()
        conn.close()
    
    async def store_file_embedding(self, file_path: Path, content_data: Dict) -> str:
        """Store file content embedding and metadata"""
        text_content = content_data.get('text_content', '')
        if not text_content:
            return None
        
        # Generate embedding
        embedding = self.embedding_model.encode(text_content)
        
        # Create unique ID for this embedding
        file_hash = content_data.get('metadata', {}).get('file_hash') or str(hash(str(file_path)))
        embedding_id = f"file_{file_hash}_{datetime.now().timestamp()}"
        
        # Prepare metadata for ChromaDB
        chroma_metadata = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'content_type': content_data.get('content_type', 'unknown'),
            'file_hash': file_hash,
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        # Add specific metadata based on content type
        if content_data.get('metadata'):
            chroma_metadata.update(content_data['metadata'])
        
        # Store in ChromaDB
        self.collection.add(
            embeddings=[embedding.tolist()],
            documents=[text_content[:8000]],  # Limit document size
            metadatas=[chroma_metadata],
            ids=[embedding_id]
        )
        
        # Store detailed metadata in SQLite
        await self._store_metadata(file_hash, file_path, content_data, embedding_id)
        
        return embedding_id
    
    async def _store_metadata(self, file_hash: str, file_path: Path, 
                            content_data: Dict, embedding_id: str):
        """Store detailed metadata in SQLite"""
        conn = sqlite3.connect(self.metadata_db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO file_metadata 
                (file_hash, file_path, file_name, file_size, file_type, content_type, 
                 embedding_id, created_at, updated_at, extraction_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_hash,
                str(file_path),
                file_path.name,
                file_path.stat().st_size,
                file_path.suffix.lower(),
                content_data.get('content_type', 'unknown'),
                embedding_id,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                json.dumps(content_data.get('metadata', {}))
            ))
            conn.commit()
        finally:
            conn.close()
    
    def search_similar_content(self, query: str, limit: int = 10, 
                             content_type_filter: Optional[str] = None) -> List[Dict]:
        """Search for similar content using semantic search"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)
        
        # Prepare where clause for filtering
        where_clause = {}
        if content_type_filter:
            where_clause["content_type"] = content_type_filter
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=limit,
            where=where_clause if where_clause else None
        )
        
        # Enrich results with detailed metadata
        enriched_results = []
        for i, (distance, metadata, document, embedding_id) in enumerate(zip(
            results['distances'][0],
            results['metadatas'][0], 
            results['documents'][0],
            results['ids'][0]
        )):
            
            # Get detailed metadata from SQLite
            detailed_metadata = self._get_detailed_metadata(metadata.get('file_hash'))
            
            enriched_results.append({
                'similarity_score': 1 - distance,  # Convert distance to similarity
                'file_path': metadata.get('file_path'),
                'file_name': metadata.get('file_name'),
                'content_type': metadata.get('content_type'),
                'snippet': document[:200] + "..." if len(document) > 200 else document,
                'metadata': detailed_metadata,
                'embedding_id': embedding_id
            })
        
        return enriched_results
    
    def _get_detailed_metadata(self, file_hash: str) -> Optional[Dict]:
        """Get detailed metadata from SQLite"""
        conn = sqlite3.connect(self.metadata_db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT extraction_metadata FROM file_metadata WHERE file_hash = ?
            ''', (file_hash,))
            
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return None
        except Exception:
            return None
        finally:
            conn.close()
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the embedding collection"""
        collection_count = self.collection.count()
        
        # Get content type distribution
        conn = sqlite3.connect(self.metadata_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT content_type, COUNT(*) as count 
            FROM file_metadata 
            GROUP BY content_type
        ''')
        
        content_type_distribution = dict(cursor.fetchall())
        conn.close()
        
        return {
            'total_embeddings': collection_count,
            'content_type_distribution': content_type_distribution,
            'collection_name': self.collection.name,
            'last_updated': datetime.now().isoformat()
        }
```

## 4. Progress Monitoring and User Interface

```python
import asyncio
from typing import Callable, Dict, Any
import time
from rich.console import Console
from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table

class ProgressMonitor:
    def __init__(self):
        self.console = Console()
        self.progress = None
        self.tasks = {}
        self.start_time = None
        self.completed_files = 0
        self.failed_files = 0
        self.total_files = 0
        self.current_status = "Initializing..."
    
    def start_monitoring(self, total_files: int):
        """Start progress monitoring for batch processing"""
        self.total_files = total_files
        self.start_time = time.time()
        self.completed_files = 0
        self.failed_files = 0
        
        self.progress = Progress(
            TextColumn("[bold blue]{task.fields[filename]}", justify="left"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            TextColumn("{task.fields[status]}", style="bold green"),
            TimeRemainingColumn(),
            console=self.console
        )
        
        self.progress.start()
        
        # Create main task
        self.main_task = self.progress.add_task(
            "Overall Progress",
            total=total_files,
            filename="Batch Processing",
            status="Starting..."
        )
    
    def stop_monitoring(self):
        """Stop progress monitoring and show summary"""
        if self.progress:
            self.progress.stop()
            self._show_completion_summary()
    
    async def progress_callback(self, progress_data: Dict[str, Any]):
        """Callback function for file processing progress"""
        index = progress_data.get('index', 0)
        total = progress_data.get('total', self.total_files)
        file_path = progress_data.get('file_path', 'Unknown')
        status = progress_data.get('status', 'Processing')
        error = progress_data.get('error')
        
        if status == "completed":
            self.completed_files += 1
        elif status == "error":
            self.failed_files += 1
        
        # Update main progress
        if self.progress:
            filename = file_path.split('/')[-1] if '/' in file_path else file_path
            
            self.progress.update(
                self.main_task,
                completed=index + 1,
                filename=f"Processing files ({self.completed_files} done, {self.failed_files} failed)",
                status=f"{status.title()}: {filename}"
            )
    
    def _show_completion_summary(self):
        """Show completion summary with statistics"""
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        # Create summary table
        summary_table = Table(title="Processing Summary")
        summary_table.add_column("Metric", style="cyan", no_wrap=True)
        summary_table.add_column("Value", style="magenta")
        
        summary_table.add_row("Total Files", str(self.total_files))
        summary_table.add_row("Completed", str(self.completed_files))
        summary_table.add_row("Failed", str(self.failed_files))
        summary_table.add_row("Success Rate", f"{(self.completed_files/max(self.total_files,1)*100):.1f}%")
        summary_table.add_row("Total Time", f"{elapsed_time:.1f}s")
        summary_table.add_row("Avg Time per File", f"{elapsed_time/max(self.total_files,1):.2f}s")
        
        self.console.print(Panel(summary_table, title="✅ Batch Processing Complete"))

# Usage example combining all components
async def enhanced_file_processing_demo():
    """Demonstration of the enhanced file processing system"""
    
    # Initialize components
    processor = AsyncFileProcessor(max_workers=3)
    content_extractor = ContentExtractor()
    embedding_store = EmbeddingStore()
    progress_monitor = ProgressMonitor()
    
    # Add progress callback
    processor.add_progress_callback(progress_monitor.progress_callback)
    
    # Sample files to process
    files = [
        Path("sample.pdf"),
        Path("document.docx"), 
        Path("code.py"),
        Path("data.json"),
        Path("image.png")
    ]
    
    # Start monitoring
    progress_monitor.start_monitoring(len(files))
    
    try:
        # Process files
        results = await processor.process_files_batch(files)
        
        # Store embeddings for successful extractions
        for result in results:
            if result.success and result.metadata:
                embedding_id = await embedding_store.store_file_embedding(
                    result.file_path, result.metadata
                )
                print(f"Stored embedding: {embedding_id}")
        
        # Show collection stats
        stats = embedding_store.get_collection_stats()
        print(f"Collection stats: {stats}")
        
    finally:
        progress_monitor.stop_monitoring()

# Run the demo
if __name__ == "__main__":
    asyncio.run(enhanced_file_processing_demo())
```

This implementation blueprint provides:

1. **Asynchronous Processing**: Full async/await pattern with semaphore control
2. **Enhanced Content Extraction**: Specialized extractors for different file types
3. **Vector Database Integration**: ChromaDB with SQLite metadata storage
4. **Rich Progress Monitoring**: Real-time progress with detailed statistics
5. **Error Handling**: Comprehensive retry logic and exception handling
6. **Extensible Architecture**: Easy to add new file types and processing capabilities

The system is designed to handle the current narko use cases while providing a foundation for future enhancements like distributed processing and advanced AI features.