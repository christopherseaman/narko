"""
Block-level Marko extensions for Notion features
"""
import os
import re
from marko import block
from typing import Optional


class MathBlock(block.BlockElement):
    """Block-level math equation using $$...$$"""
    
    pattern = re.compile(r'^( {0,3})\$\$[ \t]*$', re.M)
    override = False
    priority = 8  # Higher priority
    
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


class CalloutBlock(block.BlockElement):
    """Callout block starting with > [!TYPE]"""
    
    pattern = re.compile(r'^( {0,3})> \[!(\w+)\](.*)$', re.M)
    override = True  # Override regular quotes
    priority = 8  # Higher than regular quotes
    
    def __init__(self, match):
        self.tight = True
        self.callout_type = match.group(2).upper()
        self.title = match.group(3).strip()
        self.children = []
        self.content_lines = []
    
    @classmethod
    def match(cls, source):
        return source.expect_re(cls.pattern)
    
    @classmethod  
    def parse(cls, source):
        m = source.match
        instance = cls(m)
        source.consume()
        
        # Collect content lines that start with >
        while not source.exhausted:
            line = source.next_line()
            if line.startswith('> '):
                instance.content_lines.append(line[2:])  # Remove "> "
                source.consume()
            elif line.strip() == '>':
                instance.content_lines.append('')  # Empty line in quote
                source.consume()
            else:
                break
        
        # Join content
        instance.content = '\n'.join(instance.content_lines) if instance.content_lines else ""
        
        return instance


class TaskListItem(block.BlockElement):
    """Task list item with checkbox"""
    
    pattern = re.compile(r'^( {0,3})- \[([ xX])\] (.*)$', re.M)
    override = False
    priority = 8  # Higher priority than regular list items
    
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


class FileUploadBlock(block.BlockElement):
    """File upload block using ![file](path/to/file) or ![file](url) syntax"""
    
    # Enhanced pattern to match ![file](path) or ![type:title](path)
    pattern = re.compile(r'^( {0,3})!\[(file|image|video|pdf|audio|embed)(?::([^\]]*))?\]\(([^)]+)\)[ \t]*$', re.M)
    override = False
    priority = 9  # Higher than regular images
    
    def __init__(self, match):
        self.tight = True
        self.file_type = match.group(2).lower()  # file, image, video, pdf, audio, embed
        self.title = match.group(3) or ""  # Optional title after :
        self.file_path = match.group(4).strip()  # Path or URL
        self.children = []
        
        # Determine if it's a URL or local file
        self.is_url = self.file_path.startswith(('http://', 'https://'))
        
        # Map file extensions to types if not explicitly specified
        if self.file_type == 'file':
            self.file_type = self._infer_file_type()
    
    def _infer_file_type(self) -> str:
        """Infer file type from extension"""
        ext = os.path.splitext(self.file_path)[1].lower()
        
        # Image extensions
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']:
            return 'image'
        # Video extensions  
        elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v']:
            return 'video'
        # Audio extensions
        elif ext in ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac']:
            return 'audio'
        # PDF
        elif ext == '.pdf':
            return 'pdf'
        # Default to file
        else:
            return 'file'
    
    @classmethod
    def match(cls, source):
        return source.expect_re(cls.pattern)
    
    @classmethod
    def parse(cls, source):
        m = source.match
        source.consume()
        return cls(m)