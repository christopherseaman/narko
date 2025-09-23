"""
Upload cache management with TTL and cleanup
"""
import os
import json
import time
import hashlib
import threading
import datetime
import logging
from typing import Dict, Optional
from ..config import Config

logger = logging.getLogger(__name__)


class UploadCache:
    """Advanced cache with TTL and cleanup"""
    
    def __init__(self, config: Config):
        self.config = config
        self.cache_file = config.cache_file
        self.ttl_seconds = config.cache_ttl_hours * 3600
        self.is_enabled = True
        self._lock = threading.Lock()
    
    def get(self, file_hash: str) -> Optional[Dict]:
        """Get cached upload result by file hash"""
        if not self.is_enabled:
            return None
            
        cache = self._load_cache()
        entry = cache.get(file_hash)
        
        if not entry:
            return None
        
        # Check TTL
        upload_time = entry.get('upload_timestamp')
        if upload_time:
            try:
                upload_dt = datetime.datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                if time.time() - upload_dt.timestamp() > self.ttl_seconds:
                    # Expired, remove entry
                    self._remove_entry(file_hash)
                    return None
            except ValueError:
                # Invalid timestamp, remove entry
                self._remove_entry(file_hash) 
                return None
        
        return entry
    
    def set(self, file_hash: str, upload_result: Dict):
        """Cache upload result by file hash"""
        if not self.is_enabled:
            return
            
        with self._lock:
            cache = self._load_cache()
            
            # Create cache entry (remove large metadata to keep cache manageable)
            cache_entry = upload_result.copy()
            if "metadata" in cache_entry and isinstance(cache_entry["metadata"], dict):
                if "text_content" in cache_entry["metadata"]:
                    # Store content length instead of full content
                    cache_entry["metadata"]["text_content_length"] = len(
                        cache_entry["metadata"].get("text_content", "")
                    )
                    del cache_entry["metadata"]["text_content"]
            
            cache[file_hash] = cache_entry
            self._save_cache(cache)
    
    def _load_cache(self) -> Dict:
        """Load cache with TTL validation"""
        if not os.path.exists(self.cache_file):
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return {}
    
    def _save_cache(self, cache: Dict):
        """Save cache with atomic write"""
        try:
            # Write to temporary file first
            temp_file = f"{self.cache_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(cache, f, indent=2)
            
            # Atomic rename
            os.rename(temp_file, self.cache_file)
            
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _remove_entry(self, file_hash: str):
        """Remove expired entry from cache"""
        with self._lock:
            cache = self._load_cache()
            if file_hash in cache:
                del cache[file_hash]
                self._save_cache(cache)
    
    def cleanup(self) -> int:
        """Remove expired entries and optimize cache size"""
        with self._lock:
            cache = self._load_cache()
            original_size = len(cache)
            
            # Remove expired entries
            current_time = time.time()
            valid_cache = {}
            
            for key, entry in cache.items():
                upload_time = entry.get('upload_timestamp')
                if upload_time:
                    try:
                        upload_dt = datetime.datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                        if current_time - upload_dt.timestamp() < self.ttl_seconds:
                            valid_cache[key] = entry
                    except ValueError:
                        continue  # Skip invalid timestamps
            
            # Size-based cleanup: keep max 1000 entries
            if len(valid_cache) > 1000:
                # Sort by timestamp and keep newest entries
                sorted_entries = sorted(
                    valid_cache.items(), 
                    key=lambda x: x[1].get('upload_timestamp', ''), 
                    reverse=True
                )
                valid_cache = dict(sorted_entries[:1000])
            
            self._save_cache(valid_cache)
            logger.info(f"Cache cleanup: {original_size} -> {len(valid_cache)} entries")
            
            return len(valid_cache)
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        cache = self._load_cache()
        total_size = sum(entry.get('size', 0) for entry in cache.values())
        
        return {
            'cached_files': len(cache),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'cache_file': self.cache_file,
            'ttl_hours': self.config.cache_ttl_hours
        }
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculate SHA-256 hash of file for deduplication"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""