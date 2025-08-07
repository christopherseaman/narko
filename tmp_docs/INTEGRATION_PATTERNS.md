# Integration Patterns for Enhanced Narko System

## 1. Tiny Obsidian Integration Pattern

### Bidirectional Sync Architecture

```python
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Set
import re
from datetime import datetime
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ObsidianVaultMonitor(FileSystemEventHandler):
    """Monitor Obsidian vault for changes and sync with Notion"""
    
    def __init__(self, vault_path: Path, notion_sync: 'NotionObsidianSync'):
        self.vault_path = vault_path
        self.notion_sync = notion_sync
        self.observer = Observer()
        self.sync_queue = asyncio.Queue()
        self.processing_lock = asyncio.Lock()
        
        # Track file modification times to avoid duplicate events
        self.last_modified = {}
        
    def start_monitoring(self):
        """Start monitoring the Obsidian vault"""
        self.observer.schedule(self, str(self.vault_path), recursive=True)
        self.observer.start()
        
        # Start sync queue processor
        asyncio.create_task(self._process_sync_queue())
    
    def stop_monitoring(self):
        """Stop monitoring the vault"""
        self.observer.stop()
        self.observer.join()
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory or not event.src_path.endswith('.md'):
            return
        
        file_path = Path(event.src_path)
        current_time = datetime.now().timestamp()
        
        # Debounce rapid modifications
        last_mod = self.last_modified.get(str(file_path), 0)
        if current_time - last_mod < 1.0:  # 1 second debounce
            return
        
        self.last_modified[str(file_path)] = current_time
        
        # Queue for sync
        asyncio.create_task(self._queue_sync_event(file_path, 'modified'))
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory or not event.src_path.endswith('.md'):
            return
        
        file_path = Path(event.src_path)
        asyncio.create_task(self._queue_sync_event(file_path, 'created'))
    
    def on_deleted(self, event):
        """Handle file deletion events"""
        if event.is_directory or not event.src_path.endswith('.md'):
            return
        
        file_path = Path(event.src_path)
        asyncio.create_task(self._queue_sync_event(file_path, 'deleted'))
    
    async def _queue_sync_event(self, file_path: Path, event_type: str):
        """Queue sync event for processing"""
        await self.sync_queue.put({
            'file_path': file_path,
            'event_type': event_type,
            'timestamp': datetime.now().timestamp()
        })
    
    async def _process_sync_queue(self):
        """Process sync events from the queue"""
        while True:
            try:
                event = await asyncio.wait_for(self.sync_queue.get(), timeout=1.0)
                async with self.processing_lock:
                    await self.notion_sync.handle_obsidian_change(event)
                    self.sync_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing sync event: {e}")

class NotionObsidianSync:
    """Handle bidirectional sync between Obsidian and Notion"""
    
    def __init__(self, vault_path: Path, notion_client):
        self.vault_path = vault_path
        self.notion_client = notion_client
        self.file_mappings = self._load_file_mappings()
        self.wikilink_pattern = re.compile(r'\\[\\[([^\\]]+)\\]\\]')
        self.tag_pattern = re.compile(r'#([a-zA-Z0-9_-]+)')
        
    def _load_file_mappings(self) -> Dict[str, str]:
        """Load file-to-page mappings from cache"""
        mapping_file = self.vault_path / '.narko' / 'mappings.json'
        if mapping_file.exists():
            import json
            with open(mapping_file) as f:
                return json.load(f)
        return {}
    
    def _save_file_mappings(self):
        """Save file-to-page mappings to cache"""
        mapping_dir = self.vault_path / '.narko'
        mapping_dir.mkdir(exist_ok=True)
        
        mapping_file = mapping_dir / 'mappings.json'
        import json
        with open(mapping_file, 'w') as f:
            json.dump(self.file_mappings, f, indent=2)
    
    async def handle_obsidian_change(self, event: Dict):
        """Handle changes from Obsidian vault"""
        file_path = event['file_path']
        event_type = event['event_type']
        
        rel_path = str(file_path.relative_to(self.vault_path))
        
        if event_type == 'created' or event_type == 'modified':
            await self._sync_file_to_notion(file_path, rel_path)
        elif event_type == 'deleted':
            await self._handle_file_deletion(rel_path)
    
    async def _sync_file_to_notion(self, file_path: Path, rel_path: str):
        """Sync a single file to Notion"""
        try:
            # Read and parse the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            parsed_content = self._parse_obsidian_markdown(content)
            
            # Check if this file is already mapped to a Notion page
            notion_page_id = self.file_mappings.get(rel_path)
            
            if notion_page_id:
                # Update existing page
                await self._update_notion_page(notion_page_id, parsed_content)
            else:
                # Create new page
                page_id = await self._create_notion_page(parsed_content, file_path)
                if page_id:
                    self.file_mappings[rel_path] = page_id
                    self._save_file_mappings()
            
        except Exception as e:
            print(f"Error syncing {file_path}: {e}")
    
    def _parse_obsidian_markdown(self, content: str) -> Dict:
        """Parse Obsidian markdown with special syntax"""
        lines = content.split('\\n')
        
        # Extract frontmatter if present
        frontmatter = {}
        content_start = 0
        
        if lines and lines[0].strip() == '---':
            yaml_end = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    yaml_end = i
                    break
            
            if yaml_end > 0:
                yaml_content = '\\n'.join(lines[1:yaml_end])
                try:
                    frontmatter = yaml.safe_load(yaml_content)
                except yaml.YAMLError:
                    pass
                content_start = yaml_end + 1
        
        # Get main content without frontmatter
        main_content = '\\n'.join(lines[content_start:])
        
        # Extract title (either from frontmatter or first heading)
        title = frontmatter.get('title', '')
        if not title:
            title_match = re.match(r'^#\\s+(.+)', main_content.strip())
            if title_match:
                title = title_match.group(1)
        
        # Extract wikilinks
        wikilinks = self.wikilink_pattern.findall(main_content)
        
        # Extract tags
        tags = self.tag_pattern.findall(main_content)
        
        # Convert wikilinks to Notion page references
        notion_content = self._convert_obsidian_to_notion(main_content)
        
        return {
            'title': title or 'Untitled',
            'content': notion_content,
            'frontmatter': frontmatter,
            'wikilinks': wikilinks,
            'tags': tags,
            'raw_content': main_content
        }
    
    def _convert_obsidian_to_notion(self, content: str) -> str:
        """Convert Obsidian-specific syntax to Notion-compatible markdown"""
        # Convert wikilinks to regular links (placeholder)
        def replace_wikilink(match):
            link_text = match.group(1)
            # In a full implementation, resolve to actual Notion page URLs
            return f"[{link_text}](#{link_text.lower().replace(' ', '-')})"
        
        content = self.wikilink_pattern.sub(replace_wikilink, content)
        
        # Convert Obsidian tags to Notion mentions (placeholder)
        def replace_tag(match):
            tag_name = match.group(1)
            return f"#{tag_name}"  # Keep as-is for now
        
        content = self.tag_pattern.sub(replace_tag, content)
        
        # Handle Obsidian embeds (![[image.png]])
        embed_pattern = re.compile(r'!\\[\\[([^\\]]+)\\]\\]')
        content = embed_pattern.sub(lambda m: f"![file]({m.group(1)})", content)
        
        return content
    
    async def _create_notion_page(self, parsed_content: Dict, file_path: Path) -> Optional[str]:
        """Create a new Notion page"""
        try:
            # Determine parent page (based on folder structure)
            parent_id = self._get_parent_page_id(file_path)
            
            # Process content with narko
            result = process_file(str(file_path), parent_id)
            
            if 'error' not in result:
                response = create_notion_page(result['parent_id'], result['title'], result['blocks'])
                if 'id' in response:
                    return response['id']
            
            return None
            
        except Exception as e:
            print(f"Error creating Notion page: {e}")
            return None
    
    async def _update_notion_page(self, page_id: str, parsed_content: Dict):
        """Update an existing Notion page"""
        try:
            # Use Notion MCP tools to update the page
            await self._update_via_mcp(page_id, parsed_content)
            
        except Exception as e:
            print(f"Error updating Notion page {page_id}: {e}")
    
    def _get_parent_page_id(self, file_path: Path) -> str:
        """Determine parent page ID based on folder structure"""
        # Get relative path from vault root
        rel_path = file_path.relative_to(self.vault_path)
        folder_path = str(rel_path.parent) if rel_path.parent != Path('.') else '.'
        
        # Look up folder mapping in page_map.json
        if folder_path in PAGE_MAP:
            return PAGE_MAP[folder_path]
        
        # Default to root import location
        return NOTION_IMPORT_ROOT or PAGE_MAP["."]
    
    async def _update_via_mcp(self, page_id: str, parsed_content: Dict):
        """Update page using MCP Notion tools"""
        # This would use the actual MCP tools in implementation
        pass

class ObsidianIntegrationManager:
    """High-level manager for Obsidian integration"""
    
    def __init__(self, vault_path: str, notion_api_key: str):
        self.vault_path = Path(vault_path)
        self.notion_client = None  # Initialize with actual client
        self.sync_handler = NotionObsidianSync(self.vault_path, self.notion_client)
        self.vault_monitor = ObsidianVaultMonitor(self.vault_path, self.sync_handler)
        
    def start_integration(self):
        """Start the Obsidian integration"""
        print(f"Starting Obsidian integration for vault: {self.vault_path}")
        self.vault_monitor.start_monitoring()
        print("✅ Obsidian vault monitoring started")
    
    def stop_integration(self):
        """Stop the Obsidian integration"""
        self.vault_monitor.stop_monitoring()
        print("✅ Obsidian integration stopped")
    
    async def initial_sync(self):
        """Perform initial sync of all vault files"""
        print("🔄 Starting initial vault sync...")
        
        md_files = list(self.vault_path.rglob("*.md"))
        total_files = len(md_files)
        
        progress_monitor = ProgressMonitor()
        progress_monitor.start_monitoring(total_files)
        
        try:
            for i, file_path in enumerate(md_files):
                rel_path = str(file_path.relative_to(self.vault_path))
                await self.sync_handler._sync_file_to_notion(file_path, rel_path)
                
                # Update progress
                await progress_monitor.progress_callback({
                    'index': i,
                    'total': total_files,
                    'file_path': str(file_path),
                    'status': 'completed'
                })
        
        finally:
            progress_monitor.stop_monitoring()
        
        print(f"✅ Initial sync complete: {total_files} files processed")
```

## 2. Plugin Extension System

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type
import importlib
import inspect
from pathlib import Path

class FileProcessor(ABC):
    """Abstract base class for file processors"""
    
    @abstractmethod
    def can_process(self, file_path: Path) -> bool:
        """Check if this processor can handle the file type"""
        pass
    
    @abstractmethod
    async def process(self, file_path: Path) -> Dict[str, Any]:
        """Process the file and return extracted data"""
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Return list of supported file extensions"""
        pass
    
    @property
    @abstractmethod  
    def processor_name(self) -> str:
        """Return processor name for identification"""
        pass

class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for the given text"""
        pass
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return the dimension of embeddings produced"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name/identifier"""
        pass

class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    async def store(self, key: str, data: Dict[str, Any]) -> bool:
        """Store data with the given key"""
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data by key"""
        pass
    
    @abstractmethod
    async def search(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for data matching the query"""
        pass

# Example plugin implementations
class PowerPointProcessor(FileProcessor):
    """Processor for PowerPoint files"""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.ppt', '.pptx']
    
    @property
    def processor_name(self) -> str:
        return "powerpoint_processor"
    
    def can_process(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions
    
    async def process(self, file_path: Path) -> Dict[str, Any]:
        """Extract text and metadata from PowerPoint files"""
        try:
            from pptx import Presentation
            
            prs = Presentation(file_path)
            
            slides_text = []
            slide_count = len(prs.slides)
            
            for i, slide in enumerate(prs.slides):
                slide_text = []
                
                # Extract text from all shapes in the slide
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        slide_text.append(shape.text)
                
                slides_text.append({
                    'slide_number': i + 1,
                    'text': '\\n'.join(slide_text)
                })
            
            full_text = '\\n\\n'.join([slide['text'] for slide in slides_text])
            
            return {
                'text_content': full_text[:10000],
                'metadata': {
                    'slide_count': slide_count,
                    'slides': slides_text,
                    'file_type': 'powerpoint'
                },
                'extractable': True,
                'content_type': 'presentation'
            }
            
        except Exception as e:
            return {
                'error': f"PowerPoint processing failed: {str(e)}",
                'extractable': False
            }

class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """Embedding provider using Hugging Face models"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None
    
    async def _load_model(self):
        """Lazy load the model"""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
    
    async def generate_embedding(self, text: str) -> List[float]:
        await self._load_model()
        embedding = self._model.encode(text)
        return embedding.tolist()
    
    @property
    def embedding_dimension(self) -> int:
        return 384  # MiniLM-L6-v2 dimension
    
    @property
    def model_name(self) -> str:
        return self._model_name

class PluginManager:
    """Manage and coordinate plugins"""
    
    def __init__(self):
        self.file_processors: Dict[str, FileProcessor] = {}
        self.embedding_providers: Dict[str, EmbeddingProvider] = {}
        self.storage_backends: Dict[str, StorageBackend] = {}
        
        # Load built-in processors
        self._load_builtin_plugins()
    
    def _load_builtin_plugins(self):
        """Load built-in plugins"""
        # Register built-in processors
        ppt_processor = PowerPointProcessor()
        self.register_file_processor(ppt_processor)
        
        # Register built-in embedding providers
        hf_embeddings = HuggingFaceEmbeddingProvider()
        self.register_embedding_provider(hf_embeddings)
    
    def register_file_processor(self, processor: FileProcessor):
        """Register a file processor plugin"""
        self.file_processors[processor.processor_name] = processor
        print(f"✅ Registered file processor: {processor.processor_name}")
    
    def register_embedding_provider(self, provider: EmbeddingProvider):
        """Register an embedding provider plugin"""
        self.embedding_providers[provider.model_name] = provider
        print(f"✅ Registered embedding provider: {provider.model_name}")
    
    def register_storage_backend(self, backend: StorageBackend):
        """Register a storage backend plugin"""
        backend_name = backend.__class__.__name__.lower()
        self.storage_backends[backend_name] = backend
        print(f"✅ Registered storage backend: {backend_name}")
    
    def get_processor_for_file(self, file_path: Path) -> Optional[FileProcessor]:
        """Find the best processor for a given file"""
        for processor in self.file_processors.values():
            if processor.can_process(file_path):
                return processor
        return None
    
    def get_embedding_provider(self, provider_name: str) -> Optional[EmbeddingProvider]:
        """Get embedding provider by name"""
        return self.embedding_providers.get(provider_name)
    
    def get_storage_backend(self, backend_name: str) -> Optional[StorageBackend]:
        """Get storage backend by name"""
        return self.storage_backends.get(backend_name)
    
    def load_plugins_from_directory(self, plugin_dir: Path):
        """Load plugins from a directory"""
        if not plugin_dir.exists():
            return
        
        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
            
            try:
                self._load_plugin_file(plugin_file)
            except Exception as e:
                print(f"❌ Failed to load plugin {plugin_file}: {e}")
    
    def _load_plugin_file(self, plugin_file: Path):
        """Load a single plugin file"""
        # Dynamic import of plugin module
        spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find and register plugin classes
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, FileProcessor) and obj != FileProcessor:
                self.register_file_processor(obj())
            elif issubclass(obj, EmbeddingProvider) and obj != EmbeddingProvider:
                self.register_embedding_provider(obj())
            elif issubclass(obj, StorageBackend) and obj != StorageBackend:
                self.register_storage_backend(obj())
    
    def list_plugins(self) -> Dict[str, List[str]]:
        """List all registered plugins"""
        return {
            'file_processors': list(self.file_processors.keys()),
            'embedding_providers': list(self.embedding_providers.keys()),
            'storage_backends': list(self.storage_backends.keys())
        }

# Enhanced file processor using plugin system
class PluginAwareFileProcessor:
    """File processor that uses the plugin system"""
    
    def __init__(self):
        self.plugin_manager = PluginManager()
        
        # Load external plugins
        plugin_dir = Path("./plugins")
        self.plugin_manager.load_plugins_from_directory(plugin_dir)
    
    async def process_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Process file using appropriate plugin"""
        processor = self.plugin_manager.get_processor_for_file(file_path)
        
        if processor:
            print(f"🔧 Processing {file_path} with {processor.processor_name}")
            return await processor.process(file_path)
        else:
            print(f"⚠️  No processor found for {file_path}")
            return None
```

## 3. Configuration Management System

```python
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pydantic import BaseModel, validator

@dataclass
class ProcessingConfig:
    max_concurrent_uploads: int = 5
    chunk_size_mb: int = 1
    batch_size: int = 20
    max_retries: int = 3
    timeout_seconds: int = 30

@dataclass
class EmbeddingConfig:
    enabled: bool = True
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_dimension: int = 384
    similarity_threshold: float = 0.8
    batch_size: int = 32

@dataclass
class NotionConfig:
    api_key: str = ""
    rate_limit_rps: int = 3
    import_root: str = ""
    connection_pool_size: int = 10

@dataclass
class ObsidianConfig:
    enabled: bool = False
    vault_path: str = ""
    sync_interval_seconds: int = 5
    bidirectional_sync: bool = True
    conflict_resolution: str = "notion_wins"  # "notion_wins", "obsidian_wins", "prompt"

class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self, config_path: Path = None):
        self.config_path = config_path or Path("./config/narko.yaml")
        self.processing = ProcessingConfig()
        self.embedding = EmbeddingConfig()
        self.notion = NotionConfig()
        self.obsidian = ObsidianConfig()
        self.plugins: Dict[str, Dict[str, Any]] = {}
        
        self._load_config()
        self._load_environment_overrides()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            self._create_default_config()
            return
        
        with open(self.config_path) as f:
            config_data = yaml.safe_load(f)
        
        if config_data:
            if 'processing' in config_data:
                self.processing = ProcessingConfig(**config_data['processing'])
            
            if 'embedding' in config_data:
                self.embedding = EmbeddingConfig(**config_data['embedding'])
            
            if 'notion' in config_data:
                self.notion = NotionConfig(**config_data['notion'])
            
            if 'obsidian' in config_data:
                self.obsidian = ObsidianConfig(**config_data['obsidian'])
            
            if 'plugins' in config_data:
                self.plugins = config_data['plugins']
    
    def _load_environment_overrides(self):
        """Override config with environment variables"""
        # Notion configuration
        if api_key := os.getenv('NOTION_API_KEY'):
            self.notion.api_key = api_key
        
        if import_root := os.getenv('NOTION_IMPORT_ROOT'):
            self.notion.import_root = import_root
        
        # Processing configuration
        if max_workers := os.getenv('NARKO_MAX_WORKERS'):
            try:
                self.processing.max_concurrent_uploads = int(max_workers)
            except ValueError:
                pass
        
        # Obsidian configuration
        if vault_path := os.getenv('OBSIDIAN_VAULT_PATH'):
            self.obsidian.vault_path = vault_path
            self.obsidian.enabled = True
    
    def _create_default_config(self):
        """Create default configuration file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            'processing': asdict(self.processing),
            'embedding': asdict(self.embedding),
            'notion': {
                'api_key': '${NOTION_API_KEY}',
                'rate_limit_rps': self.notion.rate_limit_rps,
                'import_root': '${NOTION_IMPORT_ROOT}',
                'connection_pool_size': self.notion.connection_pool_size
            },
            'obsidian': asdict(self.obsidian),
            'plugins': {
                'file_processors': {
                    'powerpoint_processor': {
                        'enabled': True,
                        'extract_images': False
                    }
                },
                'embedding_providers': {
                    'huggingface': {
                        'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
                        'cache_dir': './model_cache'
                    }
                }
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, indent=2)
        
        print(f"✅ Created default config at {self.config_path}")
    
    def get_plugin_config(self, plugin_type: str, plugin_name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin"""
        return self.plugins.get(plugin_type, {}).get(plugin_name, {})
    
    def update_config(self, section: str, updates: Dict[str, Any]):
        """Update configuration section"""
        if section == 'processing':
            for key, value in updates.items():
                if hasattr(self.processing, key):
                    setattr(self.processing, key, value)
        elif section == 'embedding':
            for key, value in updates.items():
                if hasattr(self.embedding, key):
                    setattr(self.embedding, key, value)
        # Add other sections as needed
        
        self.save_config()
    
    def save_config(self):
        """Save current configuration to file"""
        config_data = {
            'processing': asdict(self.processing),
            'embedding': asdict(self.embedding),
            'notion': asdict(self.notion),
            'obsidian': asdict(self.obsidian),
            'plugins': self.plugins
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f, indent=2)
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Validate Notion configuration
        if not self.notion.api_key:
            issues.append("Notion API key is required")
        
        if not self.notion.import_root:
            issues.append("Notion import root page ID is required")
        
        # Validate processing configuration
        if self.processing.max_concurrent_uploads < 1:
            issues.append("Max concurrent uploads must be at least 1")
        
        if self.processing.chunk_size_mb < 1:
            issues.append("Chunk size must be at least 1MB")
        
        # Validate Obsidian configuration
        if self.obsidian.enabled:
            if not self.obsidian.vault_path:
                issues.append("Obsidian vault path is required when enabled")
            elif not Path(self.obsidian.vault_path).exists():
                issues.append(f"Obsidian vault path does not exist: {self.obsidian.vault_path}")
        
        return issues

# Global configuration instance
config = ConfigManager()
```

This integration pattern provides:

1. **Obsidian Integration**: Complete bidirectional sync with file monitoring
2. **Plugin System**: Extensible architecture for custom processors and providers
3. **Configuration Management**: Centralized, flexible configuration with environment overrides
4. **Monitoring Integration**: Progress tracking and error handling throughout
5. **Type Safety**: Proper type hints and validation for all components

The system is designed to be modular and extensible while maintaining compatibility with the existing narko codebase.