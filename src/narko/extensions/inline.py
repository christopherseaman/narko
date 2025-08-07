"""
Inline-level Marko extensions for Notion features
"""
import re
from marko import inline


class Highlight(inline.InlineElement):
    """Highlighted text using ==text=="""
    
    pattern = re.compile(r'==([^=\n]+)==')
    parse_children = True
    
    def __init__(self, match):
        self.content = match.group(1)


class InlineMath(inline.InlineElement):
    """Inline math using $...$"""
    
    pattern = re.compile(r'\$([^$\n]+)\$')  # Simple pattern
    parse_children = False
    priority = 9  # Very high priority to override everything
    
    def __init__(self, match):
        self.content = match.group(1)