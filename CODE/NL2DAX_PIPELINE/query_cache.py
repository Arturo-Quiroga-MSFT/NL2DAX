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
from typing import Optional, Dict, Any, Union

class QueryCache:
    """Simple file-based cache for LLM responses."""
    
    def __init__(self, cache_dir: str = "./cache", ttl_hours: int = 24):
        """
        Initialize the QueryCache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "query_cache.json"
        self.ttl_seconds = ttl_hours * 3600
        self._cache = self._load_cache()
        
        # Cache statistics tracking
        self.stats_tracking = {
            'intent_hits': 0,
            'intent_misses': 0,
            'sql_hits': 0,
            'sql_misses': 0,
            'dax_hits': 0,
            'dax_misses': 0,
            'general_hits': 0,
            'general_misses': 0
        }
    
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
    
    def _get_cache_key(self, query: Union[str, Dict], cache_type: str = "general") -> str:
        """Generate a cache key from query text and type."""
        # Handle both string and dict inputs
        if isinstance(query, dict):
            # Convert dict to string for hashing
            query_str = json.dumps(query, sort_keys=True)
        else:
            query_str = str(query)
            
        # Normalize query (lowercase, strip whitespace, remove extra spaces)
        normalized = " ".join(query_str.lower().strip().split())
        # Create hash with cache type prefix
        key_text = f"{cache_type}:{normalized}"
        return hashlib.md5(key_text.encode('utf-8')).hexdigest()
    
    def _safe_preview(self, query: Union[str, Dict], max_length: int = 50) -> str:
        """Create a safe string preview for logging, handling both str and dict inputs."""
        if isinstance(query, dict):
            # Convert dict to string and truncate
            query_str = json.dumps(query, sort_keys=True)
            return query_str[:max_length] if len(query_str) > max_length else query_str
        else:
            # Handle string input
            query_str = str(query)
            return query_str[:max_length] if len(query_str) > max_length else query_str
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cache entry is expired."""
        return (time.time() - timestamp) > self.ttl_seconds
    
    def get(self, query: Union[str, Dict], cache_type: str = "general") -> Optional[str]:
        """
        Retrieve a cached response for the given query and cache type.
        
        Args:
            query: The query key (string or dict)
            cache_type: Type of cache entry
            
        Returns:
            Cached response string, or None if not found
        """
        try:
            cache_key = self._get_cache_key(query, cache_type)
            
            if cache_key in self._cache:
                cached_item = self._cache[cache_key]
                preview = self._safe_preview(cached_item['response'])
                print(f"[DEBUG] Cache hit for {cache_type}: {preview}")
                
                # Track cache hit statistics
                self._track_cache_hit(cache_type)
                
                return cached_item['response']
            else:
                print(f"[DEBUG] Cache miss for {cache_type}")
                
                # Track cache miss statistics
                self._track_cache_miss(cache_type)
                
                return None
        except Exception as e:
            print(f"[DEBUG] Cache get error: {e}")
            return None
    
    def set(self, query: Union[str, Dict], response: str, cache_type: str = "general") -> None:
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
            print(f"[DEBUG] Cached {cache_type} response for: {self._safe_preview(query)}...")
            
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
    
    def _track_cache_hit(self, cache_type: str) -> None:
        """Track cache hit for statistics."""
        stat_key = f"{cache_type}_hits"
        self.stats_tracking[stat_key] = self.stats_tracking.get(stat_key, 0) + 1
    
    def _track_cache_miss(self, cache_type: str) -> None:
        """Track cache miss for statistics."""
        stat_key = f"{cache_type}_misses"
        self.stats_tracking[stat_key] = self.stats_tracking.get(stat_key, 0) + 1
    
    def get_stats_for_report(self) -> Dict[str, Any]:
        """Get formatted cache statistics for report generation."""
        stats = self.stats()
        total_hits = stats.get('total_hits', 0)
        total_misses = stats.get('total_misses', 0)
        total_requests = total_hits + total_misses
        
        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'cache_hits': total_hits,
            'cache_misses': total_misses,
            'hit_rate_percentage': round(hit_rate, 2),
            'total_entries': stats.get('total_entries', 0),
            'expired_entries': stats.get('expired_entries', 0),
            'detailed_stats': stats.get('hit_miss_stats', {}),
            'by_type': stats.get('by_type', {})
        }
    
    def reset_stats(self) -> None:
        """Reset cache statistics tracking."""
        for key in self.stats_tracking:
            self.stats_tracking[key] = 0
    
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
            'cache_file': str(self.cache_file),
            'hit_miss_stats': self.stats_tracking,
            'total_hits': sum(v for k, v in self.stats_tracking.items() if k.endswith('_hits')),
            'total_misses': sum(v for k, v in self.stats_tracking.items() if k.endswith('_misses'))
        }

# Global cache instance
_cache_instance = None

def get_cache() -> QueryCache:
    """Get or create the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = QueryCache()
    return _cache_instance
