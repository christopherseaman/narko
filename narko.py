#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "marko",
#     "requests", 
#     "python-dotenv",
# ]
# ///
"""
narko - Notion extension and uploader for marko
A clean, extension-based markdown to Notion converter using proper marko extensions
"""
import os
import re
import json
import argparse
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv
from marko import Markdown, block, inline
from marko.helpers import MarkoExtension

# Load environment variables
load_dotenv()
NOTION_API_KEY = os.getenv('NOTION_API_KEY')

# Load PAGE_MAP
PAGE_MAP_FILE = "page_map.json"
if os.path.exists(PAGE_MAP_FILE):
    with open(PAGE_MAP_FILE, 'r') as f:
        PAGE_MAP = json.load(f)
else:
    PAGE_MAP = {".": "23ad9fdd-1a1a-809c-b1c0-c842794d9176"}


def chunk_text(text: str, limit: int = 2000) -> List[str]:
    """Split text into chunks while preserving word boundaries"""
    if len(text) <= limit:
        return [text]
    
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        
        split_pos = text.rfind(' ', 0, limit)
        if split_pos == -1:
            split_pos = limit
        
        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip()
    
    return chunks


def create_rich_text(text: str, annotations: Optional[Dict] = None, link: str = None) -> List[Dict]:
    """Create Notion rich text with chunking support"""
    if annotations is None:
        annotations = {
            "bold": False,
            "italic": False,
            "strikethrough": False,
            "underline": False,
            "code": False,
            "color": "default"
        }
    
    chunks = chunk_text(text)
    rich_text = []
    for chunk in chunks:
        text_obj = {"content": chunk}
        if link:
            text_obj["link"] = {"url": link}
        
        rich_text.append({
            "type": "text",
            "text": text_obj,
            "annotations": annotations
        })
    
    return rich_text


# === MARKO EXTENSIONS ===

# Math Block Extension
class MathBlock(block.BlockElement):
    """Block-level math equation using $$...$$"""
    
    pattern = re.compile(r'^( {0,3})\$\$[ \t]*$', re.M)
    override = False
    priority = 7
    
    def __init__(self, match):
        self.tight = True
        self.children = []
        self.content = ""
    
    @classmethod
    def match(cls, source):
        return source.expect_re(cls.pattern)
    
    @classmethod
    def parse(cls, source):
        m = source.match
        source.consume()
        content_lines = []
        
        while not source.exhausted:
            line = source.next_line()
            if line.strip() == '$$':
                source.consume()
                break
            content_lines.append(line.rstrip())
            source.consume()
        
        instance = cls(m)
        instance.content = '\n'.join(content_lines).strip()
        return instance


# Task List Item Extension
class TaskListItem(block.BlockElement):
    """Task list item with checkbox"""
    
    pattern = re.compile(r'^( {0,3})- \[([ xX])\] (.*)$', re.M)
    override = False
    priority = 7
    
    def __init__(self, match):
        self.tight = True
        self.checked = match.group(2).lower() == 'x'
        self.content = match.group(3)
        self.children = []
    
    @classmethod
    def match(cls, source):
        return source.expect_re(cls.pattern)
    
    @classmethod
    def parse(cls, source):
        m = source.match
        source.consume()
        return cls(m)


# Highlight Inline Extension
class Highlight(inline.InlineElement):
    """Highlighted text using ==text=="""
    
    pattern = re.compile(r'==([^=\n]+)==')
    parse_children = True
    
    def __init__(self, match):
        self.content = match.group(1)


# Inline Math Extension
class InlineMath(inline.InlineElement):
    """Inline math using $...$"""
    
    pattern = re.compile(r'\$([^$\n]+)\$')
    parse_children = False
    
    def __init__(self, match):
        self.content = match.group(1)


# === NOTION CONVERTER ===

class NotionConverter:
    """Convert marko AST to Notion blocks"""
    
    def __init__(self):
        self.blocks = []
    
    def convert(self, ast) -> List[Dict]:
        """Convert AST to Notion blocks"""
        self.blocks = []
        
        for child in ast.children:
            result = self.process_node(child)
            if result:
                if isinstance(result, list):
                    self.blocks.extend(result)
                else:
                    self.blocks.append(result)
        
        return self.blocks
    
    def process_node(self, node) -> Optional[Dict]:
        """Process a single AST node"""
        node_type = type(node).__name__
        
        # Handle our custom extensions
        if isinstance(node, MathBlock):
            return {
                "type": "equation",
                "equation": {"expression": node.content}
            }
        
        elif isinstance(node, TaskListItem):
            return {
                "type": "to_do",
                "to_do": {
                    "rich_text": create_rich_text(node.content),
                    "checked": node.checked
                }
            }
        
        # Handle standard marko elements
        elif node_type == 'Heading':
            level = min(node.level, 3)  # Notion supports max 3 levels
            block_type = f"heading_{level}"
            rich_text = self.extract_rich_text(node.children)
            
            return {
                "type": block_type,
                block_type: {"rich_text": rich_text}
            }
        
        elif node_type == 'Paragraph':
            # Check for callout post-processing (minimal)
            if (node.children and hasattr(node.children[0], 'children') and 
                isinstance(node.children[0].children, str) and
                node.children[0].children.startswith('[!')):
                # This is handled by Quote processing for callouts
                return None
            
            rich_text = self.extract_rich_text(node.children)
            return {
                "type": "paragraph", 
                "paragraph": {"rich_text": rich_text}
            }
        
        elif node_type in ['CodeBlock', 'FencedCode']:
            code_text = ""
            if node.children:
                code_text = node.children[0].children if hasattr(node.children[0], 'children') else str(node.children[0])
            
            if not isinstance(code_text, str):
                code_text = str(code_text) if code_text else ""
            
            # Extract language
            language = "plain text"
            if hasattr(node, 'lang') and node.lang:
                language = self.map_language(node.lang.strip())
            
            # Apply chunking
            code_chunks = chunk_text(code_text)
            rich_text_blocks = []
            for chunk in code_chunks:
                rich_text_blocks.append({
                    "type": "text",
                    "text": {"content": chunk}
                })
            
            return {
                "type": "code",
                "code": {
                    "rich_text": rich_text_blocks,
                    "language": language
                }
            }
        
        elif node_type == 'Quote':
            # Check for callout (simple post-processing)
            if (node.children and node.children[0].children and 
                hasattr(node.children[0].children[0], 'children')):
                first_text = node.children[0].children[0].children
                if isinstance(first_text, str):
                    callout_match = re.match(r'\[!(\w+)\]\s*(.*)', first_text)
                    if callout_match:
                        return self.create_callout(node, callout_match.group(1), callout_match.group(2))
            
            # Regular quote
            quote_blocks = []
            for child in node.children:
                if child.__class__.__name__ == 'Paragraph':
                    quote_blocks.extend(self.extract_rich_text(child.children))
            
            return {
                "type": "quote",
                "quote": {"rich_text": quote_blocks}
            }
        
        elif node_type == 'List':
            list_blocks = []
            list_type = 'bulleted' if not node.ordered else 'numbered'
            
            for item in node.children:
                if item.__class__.__name__ == 'ListItem':
                    block_type = f"{list_type}_list_item"
                    
                    item_content = []
                    for child in item.children:
                        if child.__class__.__name__ == 'Paragraph':
                            item_content.extend(self.extract_rich_text(child.children))
                    
                    list_blocks.append({
                        "type": block_type,
                        block_type: {"rich_text": item_content}
                    })
            
            return list_blocks
        
        elif node_type == 'ThematicBreak':
            return {"type": "divider", "divider": {}}
        
        elif node_type == 'BlankLine':
            return None  # Skip blank lines
        
        return None
    
    def create_callout(self, quote_node, callout_type: str, title: str) -> Dict:
        """Create a callout block from a quote"""
        emoji_map = {
            'NOTE': 'ℹ️', 'TIP': '💡', 'WARNING': '⚠️', 'DANGER': '🚨',
            'INFO': 'ℹ️', 'IMPORTANT': '❗', 'EXAMPLE': '📝', 'QUOTE': '💬'
        }
        emoji = emoji_map.get(callout_type.upper(), '📌')
        
        # Extract all content from the quote
        callout_content = []
        
        for i, child in enumerate(quote_node.children):
            if child.__class__.__name__ == 'Paragraph':
                if i == 0:
                    # First paragraph - remove [!TYPE] part
                    modified_children = []
                    for j, subchild in enumerate(child.children):
                        if j == 0 and hasattr(subchild, 'children') and isinstance(subchild.children, str):
                            remaining_text = re.sub(r'^\[!\w+\]\s*', '', subchild.children)
                            if remaining_text:
                                # Create a new text node with remaining content
                                modified_children.append(type(subchild)(remaining_text))
                        else:
                            modified_children.append(subchild)
                    
                    if modified_children:
                        callout_content.extend(self.extract_rich_text(modified_children))
                else:
                    callout_content.extend(self.extract_rich_text(child.children))
        
        return {
            "type": "callout",
            "callout": {
                "rich_text": callout_content,
                "icon": {"type": "emoji", "emoji": emoji},
                "color": "gray_background"
            }
        }
    
    def extract_rich_text(self, children) -> List[Dict]:
        """Extract rich text from inline elements"""
        rich_text = []
        
        for element in children:
            element_type = type(element).__name__
            
            if element_type == 'RawText':
                rich_text.extend(create_rich_text(element.children))
            
            elif isinstance(element, Highlight):
                rich_text.extend(create_rich_text(
                    element.content,
                    annotations={"color": "yellow_background"}
                ))
            
            elif isinstance(element, InlineMath):
                rich_text.extend(create_rich_text(
                    f"${element.content}$",
                    annotations={"code": True}
                ))
            
            elif element_type == 'Emphasis':
                text = self.extract_text(element)
                rich_text.extend(create_rich_text(text, annotations={"italic": True}))
            
            elif element_type == 'StrongEmphasis':
                text = self.extract_text(element)
                rich_text.extend(create_rich_text(text, annotations={"bold": True}))
            
            elif element_type == 'CodeSpan':
                rich_text.extend(create_rich_text(element.children, annotations={"code": True}))
            
            elif element_type == 'Link':
                text = self.extract_text(element)
                rich_text.extend(create_rich_text(text, link=element.dest))
            
            elif element_type == 'LineBreak':
                rich_text.extend(create_rich_text('\n'))
            
            else:
                # Fallback: extract any text content
                text = self.extract_text(element)
                if text:
                    rich_text.extend(create_rich_text(text))
        
        return rich_text if rich_text else [{"type": "text", "text": {"content": ""}}]
    
    def extract_text(self, element) -> str:
        """Extract plain text from an element"""
        if hasattr(element, 'children'):
            if isinstance(element.children, str):
                return element.children
            elif isinstance(element.children, list):
                return ''.join(self.extract_text(child) for child in element.children)
        return str(element) if element else ""
    
    def map_language(self, lang: str) -> str:
        """Map language to Notion's supported languages"""
        if not lang:
            return "plain text"
            
        supported = {
            "python", "javascript", "typescript", "java", "c", "cpp", "c++",
            "csharp", "c#", "ruby", "go", "rust", "kotlin", "swift",
            "objectivec", "objective-c", "scala", "shell", "bash", "powershell",
            "sql", "html", "css", "scss", "sass", "less", "xml", "json",
            "yaml", "toml", "markdown", "latex", "plaintext", "plain text",
            "dart", "elixir", "elm", "erlang", "f#", "fsharp", "haskell", 
            "julia", "lua", "perl", "php", "r", "solidity", "mermaid",
            "graphql", "docker", "makefile", "diff", "protobuf", "webassembly",
            "notion formula", "clojure", "coffeescript", "lisp", "matlab",
            "mathematica", "nix", "ocaml", "racket", "reason", "scheme",
            "smalltalk", "vb.net", "verilog", "vhdl", "visual basic"
        }
        
        lang_lower = lang.lower()
        if lang_lower in supported:
            return lang_lower
        
        mappings = {
            "py": "python", "js": "javascript", "ts": "typescript",
            "sh": "shell", "yml": "yaml", "md": "markdown",
            "dockerfile": "docker", "makefile": "makefile", "make": "makefile",
            "proto": "protobuf", "wasm": "webassembly", "fs": "f#",
            "ex": "elixir", "erl": "erlang", "hs": "haskell", "jl": "julia",
            "ml": "ocaml", "rkt": "racket", "scm": "scheme", "sol": "solidity"
        }
        
        return mappings.get(lang_lower, "plain text")


# === NOTION API ===

def create_notion_page(parent_id: str, title: str, blocks: List[Dict]) -> Dict:
    """Create a page in Notion"""
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Validate all blocks
    for block in blocks[:100]:
        block_type = block.get('type')
        if block_type in block and 'rich_text' in block[block_type]:
            rich_text = block[block_type]['rich_text']
            for rt_item in rich_text:
                if 'text' in rt_item and 'content' in rt_item['text']:
                    content = rt_item['text']['content']
                    if not isinstance(content, str):
                        rt_item['text']['content'] = str(content) if content else ""
    
    data = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": {"title": [{"text": {"content": title}}]}
        },
        "children": blocks[:100]
    }
    
    response = requests.post("https://api.notion.com/v1/pages", 
                           headers=headers, json=data)
    return response.json()


def clean_obsidian_syntax(content: str) -> str:
    """Clean Obsidian-specific syntax (minimal processing)"""
    # Remove YAML frontmatter
    content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
    
    # Convert wiki links to plain text
    content = re.sub(r'\[\[([^\|]+)\|([^\]]+)\]\]', r'\2', content)
    content = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)
    
    # Convert embeds to placeholder
    content = re.sub(r'!\[\[([^\]]+)\]\]', r'[Embedded: \1]', content)
    
    # Remove Obsidian tags (preserve headers)
    content = re.sub(r'(?<!\n)(?<!^)(?<!#)#(\w+)', r'\1', content)
    
    # Remove Dataview queries
    content = re.sub(r'```dataview.*?```', '[Dataview query removed]', content, flags=re.DOTALL)
    
    # Remove hidden comments
    content = re.sub(r'%%.*?%%', '', content, flags=re.DOTALL)
    
    return content


# === MAIN CONVERTER ===

# Create the Notion Extension
NotionExtension = MarkoExtension(
    elements=[MathBlock, TaskListItem, Highlight, InlineMath]
)


def process_file(file_path: str, parent_id: str = None) -> Dict:
    """Process a markdown file using extension-based parsing"""
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Clean Obsidian syntax
    content = clean_obsidian_syntax(content)
    
    # Create markdown parser with extensions
    md = Markdown(extensions=[NotionExtension])
    
    # Parse to AST
    ast = md.parse(content)
    
    # Convert to Notion blocks
    converter = NotionConverter()
    blocks = converter.convert(ast)
    
    title = os.path.splitext(os.path.basename(file_path))[0]
    
    return {
        "title": title,
        "parent_id": parent_id or PAGE_MAP["."],
        "blocks": blocks,
        "file_path": file_path
    }


def main():
    parser = argparse.ArgumentParser(description='narko - Notion extension and uploader for marko')
    parser.add_argument('--file', help='Import a specific file')
    parser.add_argument('--parent', help='Parent page ID to import into (overrides page_map.json)')
    parser.add_argument('--test', action='store_true', help='Test mode')
    parser.add_argument('--import', dest='do_import', action='store_true', help='Import to Notion')
    
    args = parser.parse_args()
    
    if args.do_import and not NOTION_API_KEY:
        print("Error: NOTION_API_KEY not found in .env file")
        return
    
    if args.file:
        parent_id = args.parent if args.parent else None
        result = process_file(args.file, parent_id)
        
        if "error" in result:
            print(f"Error: {result['error']}")
            return
        
        print(f"File: {result['file_path']}")
        print(f"Title: {result['title']}")
        print(f"Blocks: {len(result['blocks'])}")
        
        if args.test:
            print("\nAll blocks:")
            for i, block in enumerate(result['blocks']):
                print(f"\n{i+1}. {block['type']}")
                block_type = block['type']
                if 'rich_text' in block.get(block_type, {}):
                    texts = block[block_type]['rich_text']
                    if texts and 'text' in texts[0]:
                        content = texts[0]['text']['content'][:80]
                        print(f"   Content: {content}...")
                elif block_type == 'code':
                    lang = block['code'].get('language', 'plain text')
                    content = block['code']['rich_text'][0]['text']['content'][:80]
                    print(f"   Language: {lang}")
                    print(f"   Content: {content}...")
                elif block_type == 'equation':
                    expr = block['equation']['expression'][:80]
                    print(f"   Expression: {expr}...")
        
        if args.do_import:
            print("\nImporting to Notion...")
            response = create_notion_page(result['parent_id'], result['title'], result['blocks'])
            if 'url' in response:
                print(f"✅ Created: {response['url']}")
            else:
                print(f"❌ Error: {response}")

if __name__ == "__main__":
    main()