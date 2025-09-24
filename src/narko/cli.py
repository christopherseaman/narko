#!/usr/bin/env python3
"""
narko CLI module - Main command line interface
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add src to path for imports when running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from narko import Config, NotionExtension, NotionClient
from narko.converter import NotionConverter
from narko.notion import FileUploader, ExternalImporter
from narko.utils import UploadCache, FileValidator
from marko import Markdown
from marko.ext import gfm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('narko')


class NarkoApp:
    """Main narko application with modular architecture"""
    
    def __init__(self):
        try:
            self.config = Config.from_env()
        except ValueError as e:
            print(f"Configuration error: {e}")
            print("Please check your .env file for NOTION_API_KEY and NOTION_IMPORT_ROOT")
            sys.exit(1)
        
        # Initialize components
        self.notion_client = NotionClient(self.config)
        self.file_uploader = FileUploader(self.config)
        self.external_importer = ExternalImporter(self.config)
        self.cache = UploadCache(self.config)
        self.validator = FileValidator(self.config)
        self.converter = NotionConverter(self.config, self.file_uploader, self.external_importer)
        
        # Setup markdown parser with extensions
        self.markdown = Markdown(extensions=[NotionExtension, gfm.GFM])
    
    def process_file(self, file_path: str, parent_id: str = None) -> dict:
        """Process a markdown file using modular components"""
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse to AST using Marko extensions
        ast = self.markdown.parse(content)

        # Convert to Notion blocks using converter
        blocks = self.converter.convert(ast)

        title = os.path.splitext(os.path.basename(file_path))[0]

        return {
            "title": title,
            "parent_id": parent_id,  # No fallback - must be explicit
            "blocks": blocks,
            "file_path": file_path
        }
    
    def import_to_notion(self, result: dict) -> dict:
        """Import processed result to Notion"""
        try:
            response = self.notion_client.create_page(
                result['parent_id'], 
                result['title'], 
                result['blocks']
            )
            return response
        except Exception as e:
            return {"error": str(e)}
    
    def show_cache_info(self):
        """Show upload cache information"""
        stats = self.cache.get_stats()
        print(f"📊 Upload Cache Statistics:")
        print(f"   Cached files: {stats['cached_files']}")
        
        if stats['cached_files'] > 0:
            print(f"   Total size: {stats['total_size_bytes']:,} bytes ({stats['total_size_mb']:.1f} MB)")
            print(f"   Cache file: {stats['cache_file']}")
            print(f"   TTL: {stats['ttl_hours']} hours")
        else:
            print("   No cached uploads found")
    
    def cleanup_cache(self) -> int:
        """Clean expired cache entries"""
        return self.cache.cleanup()
    
    def validate_files(self, pattern: str):
        """Validate files matching pattern"""
        from glob import glob
        
        files = glob(pattern)
        if not files:
            print(f"No files found matching: {pattern}")
            return
        
        print(f"🔍 Validating {len(files)} file(s)...")
        valid_count = 0
        
        for file_path in files:
            result = self.validator.validate_file(file_path)
            status = "✅" if result['valid'] else "❌"
            print(f"{status} {file_path}")
            
            if result['errors']:
                for error in result['errors']:
                    print(f"   ❌ {error}")
            
            if result['warnings']:
                for warning in result['warnings']:
                    print(f"   ⚠️  {warning}")
            
            if result['valid']:
                valid_count += 1
        
        print(f"\n📊 Validation Summary: {valid_count}/{len(files)} files valid")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='narko v2.0 - Modular Notion extension and uploader for marko',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Modular Architecture:
  - Clean separation of concerns
  - Comprehensive test coverage  
  - Marko extensions for parsing
  - Notion client for API operations
  - Advanced validation and caching

Examples:
  narko --file document.md --parent PAGE_ID --import   # Import single file (--parent required!)
  narko --validate "*.md"                              # Validate files
  narko --cache-info                                   # Show cache stats
  narko --file doc.md --test --show-embeddings         # Test with analysis
        '''
    )
    
    # File input options
    parser.add_argument('--file', help='Process and optionally import a specific file')
    parser.add_argument('--parent', help='Parent page ID to import into (REQUIRED with --import)')
    parser.add_argument('--validate', help='Validate files using glob pattern')
    
    # Processing options
    parser.add_argument('--test', action='store_true', help='Test mode - show processed blocks without importing')
    parser.add_argument('--import', dest='do_import', action='store_true', help='Import to Notion')
    parser.add_argument('--upload-files', action='store_true', help='Enable file uploads for local files')
    parser.add_argument('--show-embeddings', action='store_true', help='Show embedding analysis')
    
    # Cache and maintenance
    parser.add_argument('--cache-info', action='store_true', help='Show cache statistics')
    parser.add_argument('--cache-cleanup', action='store_true', help='Clean expired cache entries')
    
    # Logging
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Set logging level')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else getattr(logging, args.log_level)
    logging.getLogger().setLevel(log_level)
    
    # Initialize app
    try:
        app = NarkoApp()
    except SystemExit:
        return
    
    # Handle cache operations
    if args.cache_info:
        app.show_cache_info()
        return
    
    if args.cache_cleanup:
        cleaned = app.cleanup_cache()
        print(f"🧹 Cache cleanup completed: {cleaned} entries remaining")
        return
    
    # Handle file validation
    if args.validate:
        app.validate_files(args.validate)
        return
    
    # Handle file processing
    if args.file:
        # Check if --import is used without --parent
        if args.do_import and not args.parent:
            print("❌ Error: --parent is required when using --import")
            print("   Usage: narko --file document.md --parent PAGE_ID --import")
            print("   Where PAGE_ID can be:")
            print("   - A Notion page URL: https://notion.so/My-Page-abc123...")
            print("   - A page ID: abc123def456...")
            return

        parent_id = app.notion_client.extract_page_id(args.parent) if args.parent else None
        result = app.process_file(args.file, parent_id)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"📄 File: {result['file_path']}")
        print(f"📝 Title: {result['title']}")
        print(f"🧱 Blocks: {len(result['blocks'])}")
        
        if args.test:
            print("\n📋 Processed Blocks:")
            for i, block in enumerate(result['blocks'][:10]):  # Show first 10 blocks
                print(f"\n{i+1}. {block['type'].upper()}")
                
                # Show block content preview
                if 'rich_text' in block.get(block['type'], {}):
                    texts = block[block['type']]['rich_text']
                    if texts and 'text' in texts[0]:
                        content = texts[0]['text']['content'][:60]
                        print(f"   📝 {content}{'...' if len(content) == 60 else ''}")
                
                elif block['type'] in ['image', 'video', 'pdf', 'audio', 'file']:
                    file_info = block.get(block['type'], {})
                    if 'external' in file_info:
                        print(f"   🌐 External: {file_info['external']['url'][:50]}...")
                    elif 'file_upload' in file_info:
                        print(f"   📁 Upload ID: {file_info['file_upload']['id']}")
        
        if args.show_embeddings:
            # Show embedding analysis
            file_blocks = [b for b in result['blocks'] if b['type'] in ['file', 'image', 'video', 'pdf', 'audio']]
            print(f"\n🧠 Embedding Analysis:")
            print(f"   📊 File blocks found: {len(file_blocks)}")
            print(f"   🔍 Supported extensions: {', '.join(sorted(app.config.embedding_enabled_types))}")
        
        if args.do_import:
            print(f"\n📤 Importing to Notion...")
            response = app.import_to_notion(result)
            
            if 'url' in response:
                print(f"✅ Successfully created: {response['url']}")
            else:
                print(f"❌ Import failed: {response}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()