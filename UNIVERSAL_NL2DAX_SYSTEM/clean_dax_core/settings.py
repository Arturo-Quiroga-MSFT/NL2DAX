"""
Configuration settings for Clean DAX Engine
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class PowerBIConfig:
    """Power BI connection configuration"""
    tenant_id: str
    xmla_endpoint: str
    dataset_name: str
    dataset_id: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'PowerBIConfig':
        """Create configuration from environment variables"""
        return cls(
            tenant_id=os.getenv('PBI_TENANT_ID', ''),
            xmla_endpoint=os.getenv('PBI_XMLA_ENDPOINT', ''),
            dataset_name=os.getenv('PBI_DATASET_NAME', ''),
            dataset_id=os.getenv('PBI_DATASET_ID', None)
        )

@dataclass
class SchemaConfig:
    """Schema management configuration"""
    cache_dir: str = "./cache"
    cache_ttl_hours: int = 24
    
@dataclass
class DAXConfig:
    """DAX generation configuration"""
    max_results: int = 100
    timeout_seconds: int = 60
    enable_validation: bool = True
    
@dataclass
class Settings:
    """Main settings container"""
    powerbi: PowerBIConfig
    schema: SchemaConfig
    dax: DAXConfig
    
    @classmethod
    def load(cls) -> 'Settings':
        """Load settings from environment and defaults"""
        return cls(
            powerbi=PowerBIConfig.from_env(),
            schema=SchemaConfig(),
            dax=DAXConfig()
        )

# Global settings instance
settings = Settings.load()