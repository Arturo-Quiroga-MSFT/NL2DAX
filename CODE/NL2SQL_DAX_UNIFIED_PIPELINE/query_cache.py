#!/usr/bin/env python3
"""
query_cache.py - Query Caching System
====================================

This module provides caching capabilities for SQL and DAX queries
to improve performance and reduce redundant database calls.

Author: Unified Pipeline Team
Date: August 2025
"""

import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import logging

class QueryCache:
    """Cache system for SQL and DAX queries"""
    
    def __init__(self, cache_dir: str = None, default_ttl: int = 3600):
        """
        Initialize the query cache
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), "cache")
        self.default_ttl = default_ttl
        self.logger = logging.getLogger(__name__)
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "cleanups": 0
        }
    
    def _generate_cache_key(self, query: str, query_type: str, 
                           schema_hash: str = None) -> str:
        """
        Generate a unique cache key for a query
        
        Args:
            query: The query text
            query_type: Type of query (SQL or DAX)
            schema_hash: Hash of database schema (for invalidation)
            
        Returns:
            Cache key string
        """
        # Normalize query (remove extra whitespace, convert to lowercase)
        normalized_query = " ".join(query.strip().lower().split())
        
        # Create hash input
        hash_input = f"{query_type}:{normalized_query}"
        if schema_hash:
            hash_input += f":{schema_hash}"
        
        # Generate MD5 hash
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> str:
        """Get the file path for a cache key"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _is_cache_valid(self, cache_data: Dict[str, Any]) -> bool:
        """Check if cached data is still valid (not expired)"""
        if not cache_data.get("expires_at"):
            return False
        
        expires_at = datetime.fromisoformat(cache_data["expires_at"])
        return datetime.now() < expires_at
    
    def get(self, query: str, query_type: str, schema_hash: str = None) -> Optional[Dict[str, Any]]:
        """
        Get cached result for a query
        
        Args:
            query: The query text
            query_type: Type of query (SQL or DAX)
            schema_hash: Hash of database schema
            
        Returns:
            Cached result or None if not found/expired
        """
        try:
            cache_key = self._generate_cache_key(query, query_type, schema_hash)
            cache_file = self._get_cache_file_path(cache_key)
            
            if not os.path.exists(cache_file):
                self.stats["misses"] += 1
                return None
            
            # Load cache data
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if still valid
            if not self._is_cache_valid(cache_data):
                # Remove expired cache
                os.remove(cache_file)
                self.stats["misses"] += 1
                return None
            
            # Cache hit
            self.stats["hits"] += 1
            self.logger.debug(f"Cache hit for {query_type} query: {cache_key}")
            
            # Return the cached result
            result = cache_data["result"].copy()
            result["from_cache"] = True
            result["cache_timestamp"] = cache_data["created_at"]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error reading cache: {e}")
            self.stats["misses"] += 1
            return None
    
    def set(self, query: str, query_type: str, result: Dict[str, Any], 
            ttl: int = None, schema_hash: str = None) -> bool:
        """
        Cache a query result
        
        Args:
            query: The query text
            query_type: Type of query (SQL or DAX)
            result: Query result to cache
            ttl: Time-to-live in seconds (uses default if None)
            schema_hash: Hash of database schema
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(query, query_type, schema_hash)
            cache_file = self._get_cache_file_path(cache_key)
            
            # Don't cache failed queries
            if not result.get("success", False):
                return False
            
            # Prepare cache data
            ttl = ttl or self.default_ttl
            now = datetime.now()
            expires_at = now + timedelta(seconds=ttl)
            
            cache_data = {
                "cache_key": cache_key,
                "query": query,
                "query_type": query_type,
                "schema_hash": schema_hash,
                "result": result,
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "ttl": ttl
            }
            
            # Write to cache file
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, default=str)
            
            self.logger.debug(f"Cached {query_type} query result: {cache_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing cache: {e}")
            return False
    
    def invalidate(self, query: str = None, query_type: str = None, 
                   pattern: str = None) -> int:
        """
        Invalidate cached entries
        
        Args:
            query: Specific query to invalidate
            query_type: Type of queries to invalidate (SQL or DAX)
            pattern: Pattern to match in cache keys
            
        Returns:
            Number of entries invalidated
        """
        invalidated = 0
        
        try:
            if query and query_type:
                # Invalidate specific query
                cache_key = self._generate_cache_key(query, query_type)
                cache_file = self._get_cache_file_path(cache_key)
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    invalidated = 1
            else:
                # Invalidate by pattern or type
                for filename in os.listdir(self.cache_dir):
                    if not filename.endswith('.json'):
                        continue
                    
                    cache_file = os.path.join(self.cache_dir, filename)
                    
                    # Check if we should invalidate this file
                    should_invalidate = False
                    
                    if pattern and pattern in filename:
                        should_invalidate = True
                    elif query_type:
                        # Load file to check query type
                        try:
                            with open(cache_file, 'r', encoding='utf-8') as f:
                                cache_data = json.load(f)
                            if cache_data.get("query_type") == query_type:
                                should_invalidate = True
                        except:
                            pass
                    
                    if should_invalidate:
                        os.remove(cache_file)
                        invalidated += 1
            
            self.stats["invalidations"] += invalidated
            self.logger.info(f"Invalidated {invalidated} cache entries")
            
        except Exception as e:
            self.logger.error(f"Error invalidating cache: {e}")
        
        return invalidated
    
    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries
        
        Returns:
            Number of expired entries removed
        """
        cleaned = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.json'):
                    continue
                
                cache_file = os.path.join(self.cache_dir, filename)
                
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    if not self._is_cache_valid(cache_data):
                        os.remove(cache_file)
                        cleaned += 1
                        
                except Exception as e:
                    # Remove corrupted cache files
                    self.logger.warning(f"Removing corrupted cache file {filename}: {e}")
                    os.remove(cache_file)
                    cleaned += 1
            
            self.stats["cleanups"] += cleaned
            if cleaned > 0:
                self.logger.info(f"Cleaned up {cleaned} expired cache entries")
                
        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {e}")
        
        return cleaned
    
    def clear_all(self) -> int:
        """
        Clear all cache entries
        
        Returns:
            Number of entries removed
        """
        cleared = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    os.remove(cache_file)
                    cleared += 1
            
            self.logger.info(f"Cleared all cache entries ({cleared} files)")
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
        
        return cleared
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = self.stats.copy()
        
        # Calculate hit rate
        total_requests = stats["hits"] + stats["misses"]
        stats["hit_rate"] = stats["hits"] / total_requests if total_requests > 0 else 0
        
        # Get cache size info
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
            stats["cache_size"] = len(cache_files)
            
            # Calculate total cache disk usage
            total_size = 0
            for filename in cache_files:
                file_path = os.path.join(self.cache_dir, filename)
                total_size += os.path.getsize(file_path)
            stats["disk_usage_bytes"] = total_size
            stats["disk_usage_mb"] = total_size / (1024 * 1024)
            
        except Exception as e:
            self.logger.error(f"Error calculating cache stats: {e}")
            stats["cache_size"] = -1
            stats["disk_usage_bytes"] = -1
            stats["disk_usage_mb"] = -1
        
        return stats
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        info = {
            "cache_dir": self.cache_dir,
            "default_ttl": self.default_ttl,
            "stats": self.get_stats(),
            "entries": []
        }
        
        try:
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.json'):
                    continue
                
                cache_file = os.path.join(self.cache_dir, filename)
                
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    entry_info = {
                        "cache_key": cache_data.get("cache_key", "unknown"),
                        "query_type": cache_data.get("query_type", "unknown"),
                        "created_at": cache_data.get("created_at"),
                        "expires_at": cache_data.get("expires_at"),
                        "is_valid": self._is_cache_valid(cache_data),
                        "file_size": os.path.getsize(cache_file)
                    }
                    info["entries"].append(entry_info)
                    
                except Exception as e:
                    self.logger.warning(f"Error reading cache file {filename}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error getting cache info: {e}")
        
        return info

def main():
    """Test the query cache"""
    print("🧪 Testing Query Cache")
    print("=" * 40)
    
    # Initialize cache
    cache = QueryCache(cache_dir="test_cache", default_ttl=10)  # 10 seconds for testing
    
    # Test data
    test_query = "SELECT * FROM customers WHERE status = 'active'"
    test_result = {
        "success": True,
        "columns": ["id", "name", "status"],
        "data": [
            {"id": 1, "name": "Alice", "status": "active"},
            {"id": 2, "name": "Bob", "status": "active"}
        ],
        "execution_time": 0.125
    }
    
    print("📝 Testing cache operations...")
    
    # Test cache miss
    print("\\n1. Testing cache miss:")
    result = cache.get(test_query, "SQL")
    print(f"   Result: {'Cache miss' if result is None else 'Cache hit'}")
    
    # Test cache set
    print("\\n2. Testing cache set:")
    success = cache.set(test_query, "SQL", test_result)
    print(f"   Success: {success}")
    
    # Test cache hit
    print("\\n3. Testing cache hit:")
    result = cache.get(test_query, "SQL")
    print(f"   Result: {'Cache hit' if result and result.get('from_cache') else 'Cache miss'}")
    if result:
        print(f"   Data rows: {len(result.get('data', []))}")
    
    # Test cache stats
    print("\\n4. Cache statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test cache info
    print("\\n5. Cache information:")
    info = cache.get_cache_info()
    print(f"   Cache directory: {info['cache_dir']}")
    print(f"   Default TTL: {info['default_ttl']}s")
    print(f"   Cache entries: {len(info['entries'])}")
    
    # Test invalidation
    print("\\n6. Testing invalidation:")
    invalidated = cache.invalidate(query_type="SQL")
    print(f"   Invalidated: {invalidated} entries")
    
    # Test cache miss after invalidation
    print("\\n7. Testing cache miss after invalidation:")
    result = cache.get(test_query, "SQL")
    print(f"   Result: {'Cache miss' if result is None else 'Cache hit'}")
    
    # Cleanup
    print("\\n8. Cleaning up test cache:")
    cleared = cache.clear_all()
    print(f"   Cleared: {cleared} entries")
    
    print("\\n🏁 Testing completed!")
    return 0

if __name__ == "__main__":
    exit(main())