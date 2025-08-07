"""
Text processing utilities for narko
"""
import re
import logging
from typing import Dict, List, Optional, Set, Tuple
from ..config import Config

logger = logging.getLogger(__name__)


class TextProcessor:
    """Advanced text processing for content extraction and analysis"""
    
    def __init__(self, config=None):
        self.config = config
        self.max_content_length = 50000  # Reasonable limit for text processing
        
        # Common patterns for text cleaning
        self.markdown_patterns = {
            'headers': re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE),
            'links': re.compile(r'\[([^\]]+)\]\([^)]+\)'),
            'images': re.compile(r'!\[([^\]]*)\]\([^)]+\)'),
            'code_blocks': re.compile(r'```[\s\S]*?```'),
            'inline_code': re.compile(r'`([^`]+)`'),
            'bold': re.compile(r'\*\*([^*]+)\*\*'),
            'italic': re.compile(r'\*([^*]+)\*'),
            'strikethrough': re.compile(r'~~([^~]+)~~'),
        }
        
        # File type specific patterns
        self.code_patterns = {
            'python': re.compile(r'def\s+(\w+)\s*\([^)]*\):'),
            'javascript': re.compile(r'function\s+(\w+)\s*\([^)]*\)\s*{'),
            'java': re.compile(r'(public|private|protected)?\s*\w+\s+(\w+)\s*\([^)]*\)\s*{'),
            'comments': re.compile(r'(//.*$|/\*[\s\S]*?\*/|#.*$)', re.MULTILINE),
        }
    
    def extract_text_content(self, file_path: str) -> Dict[str, any]:
        """Extract and process text content from file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if not content.strip():
                return {
                    'success': False,
                    'error': 'File is empty or contains no readable text',
                    'content': '',
                    'metadata': {}
                }
            
            # Truncate if too large
            if len(content) > self.max_content_length:
                content = content[:self.max_content_length] + "\n\n... (content truncated)"
            
            # Detect file type and process accordingly
            file_ext = file_path.lower().split('.')[-1] if '.' in file_path else ''
            metadata = self._analyze_content(content, file_ext)
            
            return {
                'success': True,
                'content': content,
                'metadata': metadata,
                'file_extension': file_ext,
                'character_count': len(content),
                'word_count': len(content.split())
            }
            
        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': '',
                'metadata': {}
            }
    
    def _analyze_content(self, content: str, file_ext: str) -> Dict[str, any]:
        """Analyze content and extract metadata based on file type"""
        metadata = {
            'file_type': file_ext,
            'line_count': len(content.split('\n')),
            'language_detected': self._detect_language(content, file_ext)
        }
        
        if file_ext in ['md', 'markdown']:
            metadata.update(self._analyze_markdown(content))
        elif file_ext in ['py', 'js', 'java', 'cpp', 'c', 'ts']:
            metadata.update(self._analyze_code(content, file_ext))
        elif file_ext in ['json', 'xml', 'yaml', 'yml']:
            metadata.update(self._analyze_structured_data(content, file_ext))
        else:
            metadata.update(self._analyze_plain_text(content))
        
        return metadata
    
    def _detect_language(self, content: str, file_ext: str) -> str:
        """Simple language detection based on content and extension"""
        # Extension-based detection first
        ext_mapping = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'md': 'markdown',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'xml': 'xml',
            'yaml': 'yaml',
            'yml': 'yaml'
        }
        
        if file_ext in ext_mapping:
            return ext_mapping[file_ext]
        
        # Content-based detection
        content_lower = content.lower()
        if 'def ' in content_lower and 'import ' in content_lower:
            return 'python'
        elif 'function ' in content_lower and '{' in content:
            return 'javascript'
        elif 'public class ' in content_lower:
            return 'java'
        elif content.strip().startswith(('<?xml', '<html', '<!doctype')):
            return 'xml/html'
        
        return 'plain_text'
    
    def _analyze_markdown(self, content: str) -> Dict[str, any]:
        """Analyze markdown content"""
        analysis = {
            'type': 'markdown',
            'headers': [],
            'links': [],
            'images': [],
            'code_blocks': 0,
        }
        
        # Extract headers
        for match in self.markdown_patterns['headers'].finditer(content):
            level = len(match.group(0).split()[0])  # Count # symbols
            analysis['headers'].append({
                'level': level,
                'text': match.group(1).strip()
            })
        
        # Count elements
        analysis['links'] = [m.group(1) for m in self.markdown_patterns['links'].finditer(content)]
        analysis['images'] = [m.group(1) for m in self.markdown_patterns['images'].finditer(content)]
        analysis['code_blocks'] = len(self.markdown_patterns['code_blocks'].findall(content))
        
        return analysis
    
    def _analyze_code(self, content: str, file_ext: str) -> Dict[str, any]:
        """Analyze code content"""
        analysis = {
            'type': 'code',
            'language': file_ext,
            'functions': [],
            'comment_ratio': 0.0,
        }
        
        # Extract functions based on language
        if file_ext == 'py':
            matches = self.code_patterns['python'].findall(content)
            analysis['functions'] = matches
        elif file_ext in ['js', 'ts']:
            matches = self.code_patterns['javascript'].findall(content)
            analysis['functions'] = matches
        elif file_ext == 'java':
            matches = self.code_patterns['java'].findall(content)
            analysis['functions'] = [match[1] if isinstance(match, tuple) else match for match in matches]
        
        # Calculate comment ratio
        comments = self.code_patterns['comments'].findall(content)
        comment_chars = sum(len(comment) for comment in comments)
        total_chars = len(content)
        analysis['comment_ratio'] = comment_chars / total_chars if total_chars > 0 else 0.0
        
        return analysis
    
    def _analyze_structured_data(self, content: str, file_ext: str) -> Dict[str, any]:
        """Analyze structured data files"""
        analysis = {
            'type': 'structured_data',
            'format': file_ext,
            'valid': True,
            'structure_info': {}
        }
        
        try:
            if file_ext == 'json':
                import json
                data = json.loads(content)
                analysis['structure_info'] = {
                    'type': type(data).__name__,
                    'keys': list(data.keys()) if isinstance(data, dict) else None,
                    'length': len(data) if hasattr(data, '__len__') else None
                }
            elif file_ext in ['yaml', 'yml']:
                # Basic YAML structure analysis
                lines = content.split('\n')
                yaml_keys = [line.split(':')[0].strip() for line in lines if ':' in line and not line.strip().startswith('#')]
                analysis['structure_info'] = {
                    'top_level_keys': yaml_keys[:10],  # First 10 keys
                    'total_lines': len(lines)
                }
            elif file_ext == 'xml':
                # Basic XML analysis
                import re
                tags = re.findall(r'<(\w+)', content)
                unique_tags = list(set(tags))
                analysis['structure_info'] = {
                    'unique_tags': unique_tags[:10],  # First 10 unique tags
                    'total_tags': len(tags)
                }
        except Exception as e:
            analysis['valid'] = False
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_plain_text(self, content: str) -> Dict[str, any]:
        """Analyze plain text content"""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        
        return {
            'type': 'plain_text',
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'unique_words': len(set(word.lower() for word in words)),
            'most_common_words': self._get_common_words(words)
        }
    
    def _get_common_words(self, words: List[str], top_n: int = 10) -> List[Tuple[str, int]]:
        """Get most common words (excluding common stop words)"""
        # Simple stop words list
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Count words (case-insensitive, excluding stop words)
        word_count = {}
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word and clean_word not in stop_words and len(clean_word) > 2:
                word_count[clean_word] = word_count.get(clean_word, 0) + 1
        
        # Return top N most common
        return sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def clean_text_for_embedding(self, content: str, file_ext: str = '') -> str:
        """Clean text content for embedding generation"""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        # File-type specific cleaning
        if file_ext in ['md', 'markdown']:
            # Clean markdown syntax but keep content
            content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)  # Remove header markers
            content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)  # Remove bold markers
            content = re.sub(r'\*([^*]+)\*', r'\1', content)  # Remove italic markers
            content = re.sub(r'`([^`]+)`', r'\1', content)  # Remove inline code markers
            content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)  # Keep link text only
        
        elif file_ext in ['py', 'js', 'java', 'cpp', 'c', 'ts']:
            # For code, remove comments and excessive whitespace
            content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)  # Remove // comments
            content = re.sub(r'/\*[\s\S]*?\*/', '', content)  # Remove /* */ comments
            content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)  # Remove # comments
        
        # General cleanup
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Reduce multiple newlines
        content = content[:self.max_content_length]  # Truncate if needed
        
        return content.strip()
    
    def extract_keywords(self, content: str, max_keywords: int = 20) -> List[str]:
        """Extract potential keywords from content"""
        if not content:
            return []
        
        # Simple keyword extraction based on word frequency and length
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        
        # Common stop words to exclude
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one',
            'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see',
            'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use', 'with',
            'have', 'this', 'will', 'your', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some',
            'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such',
            'take', 'than', 'them', 'well', 'were', 'that', 'into', 'would'
        }
        
        # Filter and count words
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) >= 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in keywords[:max_keywords]]
    
    def get_content_summary(self, file_path: str) -> Dict[str, any]:
        """Get comprehensive content summary for a file"""
        text_result = self.extract_text_content(file_path)
        
        if not text_result['success']:
            return text_result
        
        content = text_result['content']
        summary = {
            'file_path': file_path,
            'success': True,
            'basic_stats': {
                'character_count': text_result['character_count'],
                'word_count': text_result['word_count'],
                'line_count': len(content.split('\n'))
            },
            'content_analysis': text_result['metadata'],
            'keywords': self.extract_keywords(content),
            'cleaned_content': self.clean_text_for_embedding(content, text_result['file_extension']),
            'is_embedding_suitable': self.config.is_embedding_enabled(f".{text_result['file_extension']}")
        }
        
        return summary
    
    def clean_text(self, text: str) -> str:
        """Simple text cleaning method for basic usage"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text