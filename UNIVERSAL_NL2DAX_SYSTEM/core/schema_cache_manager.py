"""
schema_cache_manager.py - Database Schema Caching System
=======================================================

This module provides caching functionality for discovered database schemas to accelerate
subsequent executions of the universal NL2DAX system. It stores schema information
including tables, columns, relationships, and metadata for quick retrieval.

Key Features:
- Persistent schema caching to disk (JSON format)
- Cache invalidation based on schema changes
- Fast schema loading for repeated executions
- Metadata tracking (discovery time, table counts, etc.)
- Cache versioning for compatibility

Author: NL2DAX Pipeline Development Team
Last Updated: August 18, 2025
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class CachedSchema:
    """Represents a cached database schema"""
    connection_hash: str
    discovery_time: str
    schema_version: str
    total_tables: int
    fact_tables: List[str]
    dimension_tables: List[str]
    schema_type: str  # 'star', 'snowflake', 'generic'
    tables: Dict[str, Any]
    relationships: List[Dict[str, Any]]
    business_areas: List[str]
    suggested_patterns: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CachedSchema':
        """Create instance from dictionary"""
        return cls(**data)


class SchemaCacheManager:
    """Manages database schema caching for the universal NL2DAX system"""
    
    def __init__(self, cache_dir: str = None):
        """
        Initialize the schema cache manager
        
        Args:
            cache_dir: Directory to store cache files (default: ./cache)
        """
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), '..', 'cache')
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.schema_version = "1.0"  # Increment when schema format changes
        
    def _generate_connection_hash(self, connection_params: Dict[str, str]) -> str:
        """
        Generate a unique hash for database connection parameters
        
        Args:
            connection_params: Database connection details
            
        Returns:
            SHA256 hash of connection parameters
        """
        # Sort parameters for consistent hashing
        sorted_params = sorted(connection_params.items())
        param_string = "|".join([f"{k}={v}" for k, v in sorted_params])
        
        return hashlib.sha256(param_string.encode()).hexdigest()[:16]
    
    def _get_cache_file_path(self, connection_hash: str) -> Path:
        """Get the cache file path for a given connection hash"""
        return self.cache_dir / f"schema_cache_{connection_hash}.json"
    
    def is_cache_valid(self, connection_params: Dict[str, str], 
                      max_age_hours: int = 24) -> bool:
        """
        Check if cached schema exists and is still valid
        
        Args:
            connection_params: Database connection parameters
            max_age_hours: Maximum age of cache in hours (default: 24)
            
        Returns:
            True if valid cache exists, False otherwise
        """
        connection_hash = self._generate_connection_hash(connection_params)
        cache_file = self._get_cache_file_path(connection_hash)
        
        if not cache_file.exists():
            return False
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check schema version compatibility
            if cache_data.get('schema_version') != self.schema_version:
                print(f"[INFO] Cache version mismatch, will refresh schema")
                return False
            
            # Check cache age
            discovery_time = datetime.fromisoformat(cache_data['discovery_time'])
            age = datetime.now() - discovery_time
            
            if age > timedelta(hours=max_age_hours):
                print(f"[INFO] Cache expired ({age.total_seconds()/3600:.1f}h old), will refresh schema")
                return False
            
            print(f"[INFO] Valid schema cache found ({age.total_seconds()/3600:.1f}h old)")
            return True
            
        except Exception as e:
            print(f"[WARN] Error reading cache file: {e}")
            return False
    
    def save_schema_to_cache(self, connection_params: Dict[str, str], 
                           schema_analyzer_result: Any) -> str:
        """
        Save discovered schema to cache
        
        Args:
            connection_params: Database connection parameters
            schema_analyzer_result: Result from SchemaAgnosticAnalyzer
            
        Returns:
            Connection hash for the cached schema
        """
        connection_hash = self._generate_connection_hash(connection_params)
        cache_file = self._get_cache_file_path(connection_hash)
        
        try:
            # Extract relevant information from schema analyzer result
            cached_schema = CachedSchema(
                connection_hash=connection_hash,
                discovery_time=datetime.now().isoformat(),
                schema_version=self.schema_version,
                total_tables=len(schema_analyzer_result.tables),
                fact_tables=schema_analyzer_result.fact_tables,
                dimension_tables=schema_analyzer_result.dimension_tables,
                schema_type=schema_analyzer_result.schema_type,
                tables=schema_analyzer_result.tables,
                relationships=schema_analyzer_result.relationships,
                business_areas=schema_analyzer_result.business_areas,
                suggested_patterns=schema_analyzer_result.suggested_patterns
            )
            
            # Save to JSON file
            with open(cache_file, 'w') as f:
                json.dump(cached_schema.to_dict(), f, indent=2)
            
            print(f"[INFO] Schema cached with {len(schema_analyzer_result.tables)} tables")
            print(f"[INFO] Cache file: {cache_file}")
            
            return connection_hash
            
        except Exception as e:
            print(f"[ERROR] Failed to save schema to cache: {e}")
            return connection_hash
    
    def load_schema_from_cache(self, connection_params: Dict[str, str]) -> Optional[CachedSchema]:
        """
        Load schema from cache
        
        Args:
            connection_params: Database connection parameters
            
        Returns:
            CachedSchema object if found and valid, None otherwise
        """
        connection_hash = self._generate_connection_hash(connection_params)
        cache_file = self._get_cache_file_path(connection_hash)
        
        if not self.is_cache_valid(connection_params):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            cached_schema = CachedSchema.from_dict(cache_data)
            
            print(f"[SUCCESS] Loaded schema from cache:")
            print(f"  • Total Tables: {cached_schema.total_tables}")
            print(f"  • Fact Tables: {len(cached_schema.fact_tables)}")
            print(f"  • Dimension Tables: {len(cached_schema.dimension_tables)}")
            print(f"  • Schema Type: {cached_schema.schema_type}")
            print(f"  • Discovery Time: {cached_schema.discovery_time}")
            
            return cached_schema
            
        except Exception as e:
            print(f"[ERROR] Failed to load schema from cache: {e}")
            return None
    
    def clear_cache(self, connection_params: Dict[str, str] = None) -> bool:
        """
        Clear cached schema(s)
        
        Args:
            connection_params: Specific connection to clear, or None to clear all
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if connection_params:
                # Clear specific cache
                connection_hash = self._generate_connection_hash(connection_params)
                cache_file = self._get_cache_file_path(connection_hash)
                
                if cache_file.exists():
                    cache_file.unlink()
                    print(f"[INFO] Cleared cache for connection {connection_hash}")
                else:
                    print(f"[INFO] No cache found for connection {connection_hash}")
            else:
                # Clear all cache files
                cache_files = list(self.cache_dir.glob("schema_cache_*.json"))
                for cache_file in cache_files:
                    cache_file.unlink()
                print(f"[INFO] Cleared {len(cache_files)} cache files")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to clear cache: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about all cached schemas
        
        Returns:
            Dictionary with cache information
        """
        cache_files = list(self.cache_dir.glob("schema_cache_*.json"))
        cache_info = {
            "cache_directory": str(self.cache_dir),
            "total_cached_schemas": len(cache_files),
            "schemas": []
        }
        
        for cache_file in cache_files:
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                schema_info = {
                    "connection_hash": cache_data.get('connection_hash'),
                    "discovery_time": cache_data.get('discovery_time'),
                    "total_tables": cache_data.get('total_tables'),
                    "schema_type": cache_data.get('schema_type'),
                    "age_hours": (datetime.now() - datetime.fromisoformat(cache_data['discovery_time'])).total_seconds() / 3600
                }
                cache_info["schemas"].append(schema_info)
                
            except Exception as e:
                print(f"[WARN] Error reading cache file {cache_file}: {e}")
        
        return cache_info


# Utility functions for easy integration
def get_connection_params_from_env() -> Dict[str, str]:
    """Extract database connection parameters from environment variables"""
    return {
        "server": os.getenv('AZURE_SQL_SERVER', ''),
        "database": os.getenv('AZURE_SQL_DB', ''),
        "username": os.getenv('AZURE_SQL_USER', ''),
        # Note: Don't include password in hash for security
        "driver": os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    }


def create_cache_manager() -> SchemaCacheManager:
    """Create a schema cache manager with default configuration"""
    return SchemaCacheManager()


# Example usage and testing
if __name__ == "__main__":
    print("Schema Cache Manager Test")
    print("=" * 40)
    
    # Create cache manager
    cache_manager = create_cache_manager()
    
    # Get cache info
    info = cache_manager.get_cache_info()
    print(f"Cache directory: {info['cache_directory']}")
    print(f"Total cached schemas: {info['total_cached_schemas']}")
    
    for schema in info['schemas']:
        print(f"  • {schema['connection_hash']}: {schema['total_tables']} tables, {schema['age_hours']:.1f}h old")