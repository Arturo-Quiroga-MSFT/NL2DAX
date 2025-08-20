"""
Fabric Configuration Management
Handles authentication and workspace configuration for Power BI/Fabric
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from azure.identity import ClientSecretCredential, DefaultAzureCredential

logger = logging.getLogger(__name__)

# Compute repo root based on this file's location for .env default
_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))

@dataclass
class FabricConfig:
    """Configuration for Fabric workspace and authentication"""
    tenant_id: str
    client_id: str
    client_secret: str
    workspace_id: str
    dataset_id: str
    dataset_name: str
    xmla_endpoint: str
    use_xmla: bool = True

    @classmethod
    def from_env(cls, env_file_path: Optional[str] = None) -> 'FabricConfig':
        """
        Load configuration from environment variables or .env file
        
        Args:
            env_file_path: Optional path to .env file (defaults to parent directory)
        """
        if env_file_path:
            cls._load_env_file(env_file_path)
        elif os.path.exists('../.env'):
            cls._load_env_file('../.env')
        elif os.path.exists(os.path.join(_REPO_ROOT, '.env')):
            cls._load_env_file(os.path.join(_REPO_ROOT, '.env'))
        
        # Get required values from environment
        tenant_id = os.getenv('PBI_TENANT_ID') or os.getenv('TENANT_ID')
        client_id = os.getenv('PBI_CLIENT_ID') or os.getenv('CLIENT_ID')
        client_secret = os.getenv('PBI_CLIENT_SECRET') or os.getenv('CLIENT_SECRET')
        workspace_id = os.getenv('PBI_WORKSPACE_ID') or os.getenv('POWERBI_WORKSPACE_ID')
        dataset_id = os.getenv('PBI_DATASET_ID')
        dataset_name = os.getenv('PBI_DATASET_NAME')
        xmla_endpoint = os.getenv('PBI_XMLA_ENDPOINT')
        use_xmla = os.getenv('USE_XMLA_HTTP', 'True').lower() == 'true'
        
        # Validate required fields
        missing_fields = []
        if not tenant_id:
            missing_fields.append('PBI_TENANT_ID or TENANT_ID')
        if not client_id:
            missing_fields.append('PBI_CLIENT_ID or CLIENT_ID')
        if not client_secret:
            missing_fields.append('PBI_CLIENT_SECRET or CLIENT_SECRET')
        if not workspace_id:
            missing_fields.append('PBI_WORKSPACE_ID or POWERBI_WORKSPACE_ID')
        if not dataset_id:
            missing_fields.append('PBI_DATASET_ID')
        if not dataset_name:
            missing_fields.append('PBI_DATASET_NAME')
        if not xmla_endpoint:
            missing_fields.append('PBI_XMLA_ENDPOINT')
        
        if missing_fields:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")
        
        logger.info(f"Loaded Fabric configuration for workspace: {workspace_id}")
        logger.info(f"Dataset: {dataset_name} ({dataset_id})")
        
        return cls(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            xmla_endpoint=xmla_endpoint,
            use_xmla=use_xmla
        )
    
    @staticmethod
    def _load_env_file(file_path: str):
        """Load environment variables from .env file"""
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            logger.info(f"Loaded environment variables from {file_path}")
        except Exception as e:
            logger.warning(f"Could not load .env file {file_path}: {e}")
    
    def get_azure_credential(self) -> ClientSecretCredential:
        """Get Azure credential for authentication"""
        return ClientSecretCredential(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret
        )
    
    def get_workspace_name(self) -> str:
        """Extract workspace name from XMLA endpoint"""
        # Extract from powerbi://api.powerbi.com/v1.0/myorg/FIS
        if '/myorg/' in self.xmla_endpoint:
            return self.xmla_endpoint.split('/myorg/')[-1]
        return "Unknown Workspace"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'tenant_id': self.tenant_id,
            'workspace_id': self.workspace_id,
            'workspace_name': self.get_workspace_name(),
            'dataset_id': self.dataset_id,
            'dataset_name': self.dataset_name,
            'xmla_endpoint': self.xmla_endpoint,
            'use_xmla': self.use_xmla
        }

class FabricAuthProvider:
    """Authentication provider for Fabric/Power BI services"""
    
    def __init__(self, config: FabricConfig):
        self.config = config
        self._credential = None
        self._token_cache = {}
    
    def get_credential(self) -> ClientSecretCredential:
        """Get or create Azure credential"""
        if not self._credential:
            self._credential = self.config.get_azure_credential()
            logger.info("Created Azure Service Principal credential")
        return self._credential
    
    def get_access_token(self, scope: str = "https://analysis.windows.net/powerbi/api/.default") -> str:
        """
        Get access token for specified scope
        
        Args:
            scope: Azure scope for token (default: Power BI API)
        """
        if scope not in self._token_cache:
            credential = self.get_credential()
            token = credential.get_token(scope)
            self._token_cache[scope] = token.token
            logger.info(f"Acquired access token for scope: {scope}")
        
        return self._token_cache[scope]
    
    def clear_token_cache(self):
        """Clear cached tokens"""
        self._token_cache.clear()
        logger.info("Cleared token cache")

def load_fabric_config() -> FabricConfig:
    """
    Convenience function to load Fabric configuration from environment
    """
    try:
        return FabricConfig.from_env()
    except Exception as e:
        logger.error(f"Failed to load Fabric configuration: {e}")
        raise