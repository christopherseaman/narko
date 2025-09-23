"""
Embedding generation utilities for narko
"""
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any
from ..config import Config

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings and semantic analysis for content"""
    
    def __init__(self, config=None):
        self.config = config
        self.embedding_cache = {}  # Simple in-memory cache
        self.max_embedding_length = 8000  # Reasonable limit for embedding APIs
        
        # Configuration for different embedding approaches
        self.embedding_config = {
            'dimension': 384,  # Common embedding dimension
            'model': 'sentence-transformers/all-MiniLM-L6-v2',  # Example model
            'batch_size': 32,
            'normalize': True
        }
    
    def generate_embedding(self, content: str, content_type: str = 'text') -> Dict[str, Any]:
        """Generate embedding for content (mock implementation)"""
        if not content or not content.strip():
            return {
                'success': False,
                'error': 'Empty content provided',
                'embedding': None,
                'metadata': {}
            }
        
        try:
            # Create content hash for caching
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Check cache first
            if content_hash in self.embedding_cache:
                logger.debug(f"Using cached embedding for content hash: {content_hash[:8]}")
                return self.embedding_cache[content_hash]
            
            # Truncate content if too long
            if len(content) > self.max_embedding_length:
                content = content[:self.max_embedding_length]
                truncated = True
            else:
                truncated = False
            
            # Mock embedding generation (in real implementation, this would call an embedding API/model)
            embedding_vector = self._generate_mock_embedding(content)
            
            result = {
                'success': True,
                'embedding': embedding_vector,
                'metadata': {
                    'content_hash': content_hash,
                    'content_length': len(content),
                    'content_type': content_type,
                    'model': self.embedding_config['model'],
                    'dimension': len(embedding_vector),
                    'truncated': truncated,
                    'normalized': self.embedding_config['normalize']
                }
            }
            
            # Cache the result
            self.embedding_cache[content_hash] = result
            return result
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'embedding': None,
                'metadata': {}
            }
    
    def _generate_mock_embedding(self, content: str) -> List[float]:
        """Generate a mock embedding vector based on content"""
        # This is a placeholder implementation
        # In a real implementation, you would:
        # 1. Use a proper embedding model (OpenAI, Hugging Face, etc.)
        # 2. Send content to the model API
        # 3. Return the actual embedding vector
        
        # For now, create a deterministic "embedding" based on content characteristics
        import math
        
        # Simple hash-based mock embedding
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Convert hash to numbers and normalize
        embedding = []
        for i in range(0, min(len(content_hash), self.embedding_config['dimension'] * 2), 2):
            hex_pair = content_hash[i:i+2]
            value = int(hex_pair, 16) / 255.0  # Normalize to 0-1
            # Convert to approximate normal distribution
            value = (value - 0.5) * 2  # Scale to -1 to 1
            embedding.append(value)
        
        # Pad or trim to desired dimension
        while len(embedding) < self.embedding_config['dimension']:
            embedding.append(0.0)
        embedding = embedding[:self.embedding_config['dimension']]
        
        # Normalize vector if configured
        if self.embedding_config['normalize']:
            magnitude = math.sqrt(sum(x*x for x in embedding))
            if magnitude > 0:
                embedding = [x/magnitude for x in embedding]
        
        return embedding
    
    def generate_file_embedding(self, file_path: str, text_content: str = None) -> Dict[str, Any]:
        """Generate embedding for a file"""
        try:
            # Get file extension
            file_ext = file_path.lower().split('.')[-1] if '.' in file_path else ''
            
            # Check if embedding is supported for this file type
            if not self.config.is_embedding_enabled(f'.{file_ext}'):
                return {
                    'success': False,
                    'error': f'Embedding not supported for file type: {file_ext}',
                    'embedding': None,
                    'metadata': {'file_type': file_ext, 'supported': False}
                }
            
            # Use provided content or extract from file
            if text_content is None:
                from .text import TextProcessor
                text_processor = TextProcessor(self.config)
                text_result = text_processor.extract_text_content(file_path)
                
                if not text_result['success']:
                    return {
                        'success': False,
                        'error': f'Failed to extract text: {text_result.get("error", "Unknown error")}',
                        'embedding': None,
                        'metadata': {'file_path': file_path}
                    }
                
                text_content = text_result['content']
            
            # Generate embedding
            embedding_result = self.generate_embedding(text_content, content_type='file')
            
            if embedding_result['success']:
                # Add file-specific metadata
                embedding_result['metadata'].update({
                    'file_path': file_path,
                    'file_type': file_ext,
                    'source': 'file_extraction'
                })
            
            return embedding_result
            
        except Exception as e:
            logger.error(f"File embedding generation failed for {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'embedding': None,
                'metadata': {'file_path': file_path}
            }
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        if not embedding1 or not embedding2:
            return 0.0
        
        if len(embedding1) != len(embedding2):
            logger.warning("Embeddings have different dimensions")
            return 0.0
        
        try:
            # Cosine similarity calculation
            import math
            
            dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
            magnitude1 = math.sqrt(sum(a * a for a in embedding1))
            magnitude2 = math.sqrt(sum(b * b for b in embedding2))
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            similarity = dot_product / (magnitude1 * magnitude2)
            return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def find_similar_content(self, query_embedding: List[float], 
                           candidate_embeddings: List[Dict[str, Any]], 
                           threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find similar content based on embeddings"""
        if not query_embedding or not candidate_embeddings:
            return []
        
        similar_items = []
        
        for candidate in candidate_embeddings:
            if 'embedding' not in candidate or not candidate['embedding']:
                continue
            
            similarity = self.calculate_similarity(query_embedding, candidate['embedding'])
            
            if similarity >= threshold:
                similar_items.append({
                    'similarity': similarity,
                    'metadata': candidate.get('metadata', {}),
                    'content_id': candidate.get('content_id', 'unknown')
                })
        
        # Sort by similarity (highest first)
        similar_items.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_items
    
    def create_content_clusters(self, embeddings: List[Dict[str, Any]], 
                               similarity_threshold: float = 0.8) -> List[List[Dict[str, Any]]]:
        """Group similar content into clusters"""
        if not embeddings:
            return []
        
        clusters = []
        processed = set()
        
        for i, item in enumerate(embeddings):
            if i in processed or 'embedding' not in item:
                continue
            
            # Start new cluster
            cluster = [item]
            processed.add(i)
            
            # Find similar items
            for j, other_item in enumerate(embeddings):
                if j in processed or j <= i or 'embedding' not in other_item:
                    continue
                
                similarity = self.calculate_similarity(item['embedding'], other_item['embedding'])
                
                if similarity >= similarity_threshold:
                    cluster.append(other_item)
                    processed.add(j)
            
            if cluster:  # Only add non-empty clusters
                clusters.append(cluster)
        
        return clusters
    
    def generate_content_summary(self, embeddings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for a collection of embeddings"""
        if not embeddings:
            return {
                'total_items': 0,
                'success_rate': 0.0,
                'average_dimension': 0,
                'content_types': {},
                'clusters': []
            }
        
        successful_embeddings = [e for e in embeddings if e.get('success', False)]
        total_items = len(embeddings)
        success_rate = len(successful_embeddings) / total_items if total_items > 0 else 0.0
        
        # Calculate average dimension
        dimensions = [len(e['embedding']) for e in successful_embeddings if 'embedding' in e and e['embedding']]
        avg_dimension = sum(dimensions) / len(dimensions) if dimensions else 0
        
        # Count content types
        content_types = {}
        for embedding in successful_embeddings:
            content_type = embedding.get('metadata', {}).get('content_type', 'unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        # Generate clusters
        clusters = self.create_content_clusters(successful_embeddings)
        
        return {
            'total_items': total_items,
            'successful_items': len(successful_embeddings),
            'success_rate': success_rate,
            'average_dimension': int(avg_dimension),
            'content_types': content_types,
            'cluster_count': len(clusters),
            'largest_cluster_size': max(len(cluster) for cluster in clusters) if clusters else 0,
            'embedding_model': self.embedding_config['model']
        }
    
    def export_embeddings(self, embeddings: List[Dict[str, Any]], 
                         output_file: str, format: str = 'json') -> bool:
        """Export embeddings to file"""
        try:
            if format.lower() == 'json':
                with open(output_file, 'w') as f:
                    json.dump(embeddings, f, indent=2, default=str)
                return True
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to export embeddings: {e}")
            return False
    
    def load_embeddings(self, input_file: str) -> List[Dict[str, Any]]:
        """Load embeddings from file"""
        try:
            with open(input_file, 'r') as f:
                embeddings = json.load(f)
            
            # Validate loaded embeddings
            valid_embeddings = []
            for embedding in embeddings:
                if isinstance(embedding, dict) and 'embedding' in embedding:
                    valid_embeddings.append(embedding)
            
            logger.info(f"Loaded {len(valid_embeddings)} valid embeddings from {input_file}")
            return valid_embeddings
            
        except Exception as e:
            logger.error(f"Failed to load embeddings from {input_file}: {e}")
            return []
    
    def clear_cache(self):
        """Clear the embedding cache"""
        self.embedding_cache.clear()
        logger.info("Embedding cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get embedding cache statistics"""
        return {
            'cached_items': len(self.embedding_cache),
            'cache_size_bytes': sum(len(str(item)) for item in self.embedding_cache.values()),
            'model': self.embedding_config['model'],
            'dimension': self.embedding_config['dimension']
        }
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from file for compatibility with test"""
        from pathlib import Path
        
        try:
            path = Path(file_path)
            
            metadata = {
                'filename': path.name,
                'extension': path.suffix,
                'size_bytes': 0,
                'hash': '',
                'supported': path.suffix.lower() in getattr(self.config, 'embedding_enabled_types', set()) if self.config else False
            }
            
            if path.exists():
                stat = path.stat()
                metadata['size_bytes'] = stat.st_size
                metadata['modified_time'] = stat.st_mtime
                
                if metadata['supported']:
                    # Generate simple hash
                    content_hash = hashlib.md5(file_path.encode()).hexdigest()
                    metadata['hash'] = content_hash
            else:
                metadata['error'] = 'File does not exist'
            
            return metadata
            
        except Exception as e:
            return {
                'filename': file_path,
                'extension': '',
                'size_bytes': 0,
                'hash': '',
                'supported': False,
                'error': str(e)
            }