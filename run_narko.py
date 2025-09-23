#!/usr/bin/env python3
"""
narko v2.0 - Modular Notion extension and uploader for marko

Clean, modular architecture with separation of concerns:
- Marko extensions for parsing
- Notion API client for uploads
- Comprehensive validation and caching
- Full test suite coverage
"""
import sys
import os
import argparse
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

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
            "parent_id": parent_id or self.config.notion_import_root,
            "blocks": blocks,
            "file_path": file_path
        }
    
    def import_to_notion(self, result: dict, mode: str = 'create') -> dict:
        """Import processed result to Notion with multiple modes
        
        Args:
            result: Processed file result
            mode: Import mode - 'create', 'append', 'replace_all', 'replace_content'
        """
        try:
            if mode == 'append':
                # Append blocks to existing page
                response = self.notion_client.append_blocks(
                    result['parent_id'],
                    result['blocks']
                )
                # Add page URL for consistency
                page_id = result['parent_id']
                response['url'] = f"https://www.notion.so/{page_id.replace('-', '')}"
                response['mode'] = 'append'
                
            elif mode == 'replace_all':
                # Replace ALL blocks on the page (including sub-pages)
                response = self.notion_client.replace_all_blocks(
                    result['parent_id'],
                    result['blocks']
                )
                # Add page URL for consistency
                page_id = result['parent_id']
                response['url'] = f"https://www.notion.so/{page_id.replace('-', '')}"
                
            elif mode == 'replace_content':
                # Replace content blocks but preserve sub-pages
                response = self.notion_client.replace_content_blocks(
                    result['parent_id'],
                    result['blocks']
                )
                # Add page URL for consistency
                page_id = result['parent_id']
                response['url'] = f"https://www.notion.so/{page_id.replace('-', '')}"
                
            else:
                # Create new sub-page (default)
                response = self.notion_client.create_page(
                    result['parent_id'], 
                    result['title'], 
                    result['blocks']
                )
                response['mode'] = 'create'
                
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
  narko_v2.py --file document.md --import                      # Create new sub-page
  narko_v2.py --file document.md --import --append             # Append to existing page
  narko_v2.py --file document.md --import --replace-all        # Replace ALL content
  narko_v2.py --file document.md --import --replace-content    # Replace content, keep sub-pages
  narko_v2.py --validate "*.md"                                # Validate files
  narko_v2.py --cache-info                                     # Show cache stats
        '''
    )
    
    # File input options
    parser.add_argument('--file', help='Process and optionally import a specific file')
    parser.add_argument('--parent', help='Parent page ID to import into')
    parser.add_argument('--validate', help='Validate files using glob pattern')
    
    # Processing options
    parser.add_argument('--test', action='store_true', help='Test mode - show processed blocks without importing')
    parser.add_argument('--import', dest='do_import', action='store_true', help='Import to Notion')
    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--append', action='store_true', help='Append content to existing page')
    mode_group.add_argument('--replace-all', action='store_true', help='Replace ALL content on page (including sub-pages)')
    mode_group.add_argument('--replace-content', action='store_true', help='Replace content but preserve sub-pages (append below sub-pages)')
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
            # Determine import mode
            if args.append:
                mode = 'append'
                print(f"\n📤 Appending content to existing page...")
            elif args.replace_all:
                mode = 'replace_all'
                print(f"\n🔄 Replacing ALL content on page (including sub-pages)...")
            elif args.replace_content:
                mode = 'replace_content'
                print(f"\n🔄 Replacing content but preserving sub-pages...")
            else:
                mode = 'create'
                print(f"\n📤 Creating new sub-page...")
            
            response = app.import_to_notion(result, mode=mode)
            
            if 'url' in response:
                # Show operation-specific success message
                if mode == 'append':
                    print(f"✅ Successfully appended to: {response['url']}")
                elif mode == 'replace_all':
                    deleted = response.get('deleted_blocks', 0)
                    added = response.get('added_blocks', 0)
                    print(f"✅ Successfully replaced all content: {response['url']}")
                    print(f"   🗑️  Deleted {deleted} blocks, ➕ Added {added} blocks")
                elif mode == 'replace_content':
                    deleted = response.get('deleted_content_blocks', 0)
                    preserved = response.get('preserved_subpages', 0)
                    added = response.get('added_blocks', 0)
                    print(f"✅ Successfully replaced content: {response['url']}")
                    print(f"   🗑️  Deleted {deleted} content blocks, 📄 Preserved {preserved} sub-pages, ➕ Added {added} blocks")
                else:
                    print(f"✅ Successfully created: {response['url']}")
            else:
                print(f"❌ {mode.title()} failed: {response}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()