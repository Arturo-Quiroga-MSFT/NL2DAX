"""
Fabric Authentication Provider
Provides Azure AD authentication specifically optimized for Microsoft Fabric environments
"""

import logging
import os
from typing import Optional, Dict, Any, List
from azure.identity import ClientSecretCredential
from azure.core.credentials import AccessToken
import requests
import json

logger = logging.getLogger(__name__)

class FabricTokenProvider:
    """
    Custom token provider for SemPy that works with Azure AD Service Principal
    authentication in Fabric environments
    """
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        self._token_cache = {}
        
    def get_token(self, *scopes, **kwargs) -> AccessToken:
        """
        Get access token for the specified scopes
        
        Args:
            scopes: Token scopes (e.g., 'https://analysis.windows.net/powerbi/api/.default')
            
        Returns:
            AccessToken object
        """
        # Default scope for Power BI API
        if not scopes:
            scopes = ['https://analysis.windows.net/powerbi/api/.default']
        
        scope_key = '|'.join(scopes)
        
        # Check cache
        if scope_key in self._token_cache:
            cached_token = self._token_cache[scope_key]
            # Simple expiry check (tokens typically last 1 hour)
            import time
            if time.time() < (cached_token.expires_on - 300):  # 5 min buffer
                return cached_token
        
        # Get new token
        try:
            token = self.credential.get_token(*scopes, **kwargs)
            self._token_cache[scope_key] = token
            logger.info(f"Acquired token for scopes: {scopes}")
            return token
        except Exception as e:
            logger.error(f"Failed to acquire token: {e}")
            raise

class FabricApiClient:
    """
    Direct Power BI REST API client for Fabric operations
    """
    
    def __init__(self, token_provider: FabricTokenProvider):
        self.token_provider = token_provider
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers with access token"""
        token = self.token_provider.get_token('https://analysis.windows.net/powerbi/api/.default')
        return {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json'
        }
    
    def list_groups(self) -> List[Dict]:
        """List all accessible workspaces/groups"""
        try:
            headers = self._get_headers()
            response = requests.get(f"{self.base_url}/groups", headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get('value', [])
            
        except Exception as e:
            logger.error(f"Failed to list groups: {e}")
            return []
    
    def list_datasets(self, group_id: Optional[str] = None) -> List[Dict]:
        """List datasets in a workspace"""
        try:
            headers = self._get_headers()
            
            if group_id:
                url = f"{self.base_url}/groups/{group_id}/datasets"
            else:
                url = f"{self.base_url}/datasets"
                
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get('value', [])
            
        except Exception as e:
            logger.error(f"Failed to list datasets: {e}")
            return []
    
    def execute_dax(self, dataset_id: str, dax_query: str, group_id: Optional[str] = None) -> Dict:
        """Execute DAX query against a dataset"""
        try:
            headers = self._get_headers()
            
            if group_id:
                url = f"{self.base_url}/groups/{group_id}/datasets/{dataset_id}/executeQueries"
            else:
                url = f"{self.base_url}/datasets/{dataset_id}/executeQueries"
            
            payload = {
                "queries": [
                    {
                        "query": dax_query
                    }
                ],
                "serializerSettings": {
                    "includeNulls": True
                }
            }
            
            logger.info(f"Executing DAX query at: {url}")
            logger.debug(f"Payload: {payload}")
            
            response = requests.post(url, headers=headers, json=payload)
            
            # Log response details for debugging
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                # Try to get detailed error message
                try:
                    error_details = response.json()
                    logger.error(f"API Error Details: {error_details}")
                    return {"error": f"API Error ({response.status_code}): {error_details}"}
                except:
                    logger.error(f"API Error: {response.status_code} - {response.text}")
                    return {"error": f"API Error ({response.status_code}): {response.text}"}
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to execute DAX query: {e}")
            return {"error": str(e)}

class FabricEnvironmentSetup:
    """
    Sets up the environment variables needed for SemPy to work in Fabric mode
    """
    
    @staticmethod
    def configure_for_fabric(workspace_id: str, tenant_id: str):
        """
        Configure environment variables for Fabric/SemPy integration
        
        Args:
            workspace_id: Power BI workspace ID
            tenant_id: Azure tenant ID
        """
        # Set Fabric environment variables
        os.environ['FABRIC_WORKSPACE_ID'] = workspace_id
        os.environ['FABRIC_TENANT_ID'] = tenant_id
        
        # Set Power BI specific environment variables
        os.environ['PBI_WORKSPACE_ID'] = workspace_id
        os.environ['PBI_TENANT_ID'] = tenant_id
        
        # Enable Fabric mode
        os.environ['FABRIC_ENABLED'] = 'true'
        
        logger.info(f"Configured Fabric environment for workspace: {workspace_id}")
    
    @staticmethod
    def setup_sempy_environment(config):
        """
        Setup environment specifically for SemPy with Fabric configuration
        
        Args:
            config: FabricConfig object with workspace details
        """
        # Configure Fabric environment
        FabricEnvironmentSetup.configure_for_fabric(
            workspace_id=config.workspace_id,
            tenant_id=config.tenant_id
        )
        
        # Set additional SemPy environment variables
        os.environ['SEMPY_WORKSPACE_ID'] = config.workspace_id
        os.environ['SEMPY_DATASET_ID'] = config.dataset_id
        os.environ['SEMPY_TENANT_ID'] = config.tenant_id
        
        logger.info("SemPy environment configured for Fabric")

def create_fabric_token_provider(config) -> FabricTokenProvider:
    """
    Create a Fabric-optimized token provider from configuration
    
    Args:
        config: FabricConfig object
        
    Returns:
        FabricTokenProvider instance
    """
    return FabricTokenProvider(
        tenant_id=config.tenant_id,
        client_id=config.client_id,
        client_secret=config.client_secret
    )

def setup_fabric_authentication(config):
    """
    Complete setup for Fabric authentication
    
    Args:
        config: FabricConfig object
        
    Returns:
        Tuple of (token_provider, api_client)
    """
    # Setup environment
    FabricEnvironmentSetup.setup_sempy_environment(config)
    
    # Create token provider
    token_provider = create_fabric_token_provider(config)
    
    # Create API client
    api_client = FabricApiClient(token_provider)
    
    logger.info("Fabric authentication setup complete")
    
    return token_provider, api_client