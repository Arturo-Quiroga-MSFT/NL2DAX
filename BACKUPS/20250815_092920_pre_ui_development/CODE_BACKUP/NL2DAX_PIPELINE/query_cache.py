"""
query_cache.py - Simple LLM Response Caching
==========================================

This module provides simple caching for LLM responses to improve performance
by avoiding repeated calls to Azure OpenAI for identical or similar queries.

Features:
- Hash-based cache keys for exact query matching
- JSON file-based persistence
- Automatic cache expiration
- Safe fallback when cache fails

Cache Location: ./cache/query_cache.json
"""

import json
import hashlib
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any

class QueryCache:
    """Simple file-based cache for LLM responses."""
    
    def __init__(self, cache_dir: str = "./cache", ttl_hours: int = 24):
        """
        Initialize the query cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / "query_cache.json"
        self.ttl_seconds = ttl_hours * 3600
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(exist_ok=True)
        
        # Load existing cache
        self._cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file, return empty dict if file doesn't exist or is invalid."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[DEBUG] Cache load warning: {e}, starting with empty cache")
        return {}
    
    def _save_cache(self) -> None:
        """Save cache to file, ignore errors to avoid breaking the pipeline."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[DEBUG] Cache save warning: {e}")
    
    def _get_cache_key(self, query: str, cache_type: str = "general") -> str:
        """Generate a cache key from query text and type."""
        # Normalize query (lowercase, strip whitespace, remove extra spaces)
        normalized = " ".join(query.lower().strip().split())
        # Create hash with cache type prefix
        key_text = f"{cache_type}:{normalized}"
        return hashlib.md5(key_text.encode('utf-8')).hexdigest()
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cache entry is expired."""
        return (time.time() - timestamp) > self.ttl_seconds
    
    def get(self, query: str, cache_type: str = "general") -> Optional[str]:
        """
        Get cached response for a query.
        
        Args:
            query: The query text to look up
            cache_type: Type of cache (e.g., 'intent', 'sql', 'dax')
            
        Returns:
            Cached response if found and not expired, None otherwise
        """
        try:
            cache_key = self._get_cache_key(query, cache_type)
            
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                
                # Check if entry has expired
                if self._is_expired(entry['timestamp']):
                    # Remove expired entry
                    del self._cache[cache_key]
                    self._save_cache()
                    return None
                
                print(f"[DEBUG] Cache HIT for {cache_type}: {query[:50]}...")
                return entry['response']
            
            print(f"[DEBUG] Cache MISS for {cache_type}: {query[:50]}...")
            return None
            
        except Exception as e:
            print(f"[DEBUG] Cache get error: {e}")
            return None
    
    def set(self, query: str, response: str, cache_type: str = "general") -> None:
        """
        Store a response in the cache.
        
        Args:
            query: The query text used as key
            response: The response to cache
            cache_type: Type of cache (e.g., 'intent', 'sql', 'dax')
        """
        try:
            cache_key = self._get_cache_key(query, cache_type)
            
            self._cache[cache_key] = {
                'query': query,
                'response': response,
                'timestamp': time.time(),
                'cache_type': cache_type
            }
            
            # Clean up expired entries periodically (every 10th write)
            if len(self._cache) % 10 == 0:
                self._cleanup_expired()
            
            self._save_cache()
            print(f"[DEBUG] Cached {cache_type} response for: {query[:50]}...")
            
        except Exception as e:
            print(f"[DEBUG] Cache set error: {e}")
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        try:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry['timestamp'])
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                print(f"[DEBUG] Cleaned up {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            print(f"[DEBUG] Cache cleanup error: {e}")
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache = {}
        self._save_cache()
        print("[DEBUG] Cache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache)
        by_type = {}
        expired_count = 0
        
        for entry in self._cache.values():
            cache_type = entry.get('cache_type', 'unknown')
            by_type[cache_type] = by_type.get(cache_type, 0) + 1
            
            if self._is_expired(entry['timestamp']):
                expired_count += 1
        
        return {
            'total_entries': total_entries,
            'by_type': by_type,
            'expired_entries': expired_count,
            'cache_file': str(self.cache_file)
        }

# Global cache instance
_cache_instance = None

def get_cache() -> QueryCache:
    """Get or create the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = QueryCache()
    return _cache_instance
