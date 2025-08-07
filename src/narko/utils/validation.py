"""
File validation utilities
"""
import os
import json
import mimetypes
import logging
from typing import Dict, Any
from ..config import Config

logger = logging.getLogger(__name__)


class FileValidator:
    """Comprehensive file validation for upload"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Comprehensive file validation for upload"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        try:
            # Check file exists
            if not os.path.exists(file_path):
                validation_result['valid'] = False
                validation_result['errors'].append(f"File not found: {file_path}")
                return validation_result
            
            # Get file stats
            stat = os.stat(file_path)
            file_size = stat.st_size
            ext = os.path.splitext(file_path)[1].lower()
            
            from .cache import UploadCache
            file_hash = UploadCache.calculate_file_hash(file_path)
            
            validation_result['metadata'] = {
                'size': file_size,
                'extension': ext,
                'hash': file_hash,
                'modified_time': stat.st_mtime,
                'is_readable': os.access(file_path, os.R_OK)
            }
            
            # Size validation
            if file_size == 0:
                validation_result['valid'] = False
                validation_result['errors'].append("File is empty")
            elif file_size > self.config.max_file_size:
                validation_result['valid'] = False
                validation_result['errors'].append(
                    f"File too large: {file_size:,} bytes (max: {self.config.max_file_size:,} bytes)"
                )
            elif file_size > self.config.max_file_size * 0.8:
                validation_result['warnings'].append(
                    f"File is large: {file_size:,} bytes (approaching {self.config.max_file_size:,} byte limit)"
                )
            
            # File type validation
            if not self.config.is_supported_file_type(ext):
                validation_result['warnings'].append(f"Unsupported file type: {ext}. Upload may fail.")
            
            # Readability check
            if not validation_result['metadata']['is_readable']:
                validation_result['valid'] = False
                validation_result['errors'].append("File is not readable (permission denied)")
            
            # Additional checks for specific file types
            if ext in {'.json', '.xml'}:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(1024)  # Read first KB to check validity
                    if ext == '.json':
                        json.loads(content if len(content) < 1024 else content + '}')  # Basic JSON check
                    validation_result['metadata']['content_preview'] = content[:200]
                except Exception as e:
                    validation_result['warnings'].append(f"File content may be malformed: {str(e)[:100]}")
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def validate_url(self, url: str) -> Dict[str, Any]:
        """Validate external URL for import"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        if not url:
            validation_result['valid'] = False
            validation_result['errors'].append("URL is empty")
            return validation_result
        
        if not url.startswith(('http://', 'https://')):
            validation_result['valid'] = False
            validation_result['errors'].append("URL must start with http:// or https://")
            return validation_result
        
        if not url.startswith('https://'):
            validation_result['warnings'].append("Non-HTTPS URLs may not work with Notion import")
        
        validation_result['metadata'] = {
            'url': url,
            'is_https': url.startswith('https://'),
            'domain': url.split('/')[2] if len(url.split('/')) > 2 else 'unknown'
        }
        
        return validation_result