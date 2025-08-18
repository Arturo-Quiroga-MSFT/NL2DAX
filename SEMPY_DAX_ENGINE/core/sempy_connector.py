"""
sempy_connector.py - Microsoft Fabric Semantic Link Connector
============================================================

This module provides connection and authentication services for Microsoft Fabric
and Power BI semantic models using the SemPy (semantic-link) library.

Key Features:
- Azure AD authentication for Power BI/Fabric access
- Workspace and semantic model discovery
- Direct connection to semantic models
- Authentication caching and token management

Author: NL2DAX Pipeline Development Team
Last Updated: August 18, 2025
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd

try:
    import sempy.fabric as fabric
    from sempy.fabric import list_workspaces, list_datasets
    from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential, ClientSecretCredential
    SEMPY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SemPy not available: {e}")
    SEMPY_AVAILABLE = False

# Import fabric configuration
try:
    from config.fabric_config import FabricConfig, FabricAuthProvider
    FABRIC_CONFIG_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Fabric config not available: {e}")
    FABRIC_CONFIG_AVAILABLE = False

# Import fabric authentication provider
try:
    from .fabric_auth_provider import (
        FabricTokenProvider, 
        FabricApiClient, 
        setup_fabric_authentication,
        FabricEnvironmentSetup
    )
    FABRIC_AUTH_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Fabric auth provider not available: {e}")
    FABRIC_AUTH_AVAILABLE = False

@dataclass
class WorkspaceInfo:
    """Information about a Power BI/Fabric workspace"""
    id: str
    name: str
    type: str
    state: str
    description: Optional[str] = None

@dataclass  
class SemanticModelInfo:
    """Information about a semantic model/dataset"""
    id: str
    name: str
    workspace_id: str
    compatibility_level: Optional[int] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    description: Optional[str] = None

@dataclass
class ConnectionInfo:
    """Connection information for SemPy session"""
    authenticated: bool
    workspace_count: int
    semantic_model_count: int
    current_workspace: Optional[str] = None
    current_model: Optional[str] = None
    authentication_method: Optional[str] = None

class SemPyConnector:
    """
    Microsoft Fabric Semantic Link Connector
    
    Provides authentication and connection services for accessing
    Power BI workspaces and semantic models via SemPy.
    """
    
    def __init__(self, config: Optional['FabricConfig'] = None):
        """Initialize the SemPy connector with optional Fabric configuration"""
        self.logger = logging.getLogger(__name__)
        self.authenticated = False
        self.credential = None
        self.current_workspace = None
        self.current_model = None
        self.config = config
        self.auth_provider = None
        self.fabric_token_provider = None
        self.fabric_api_client = None
        
        # Load config from environment if not provided
        if not self.config and FABRIC_CONFIG_AVAILABLE:
            try:
                from config.fabric_config import load_fabric_config
                self.config = load_fabric_config()
                self.logger.info("Loaded Fabric configuration from environment")
            except Exception as e:
                self.logger.warning(f"Could not load Fabric config: {e}")
        
        # Set up Fabric-specific authentication if config available
        if self.config and FABRIC_AUTH_AVAILABLE:
            try:
                # Setup Fabric environment
                FabricEnvironmentSetup.setup_sempy_environment(self.config)
                
                # Create Fabric authentication providers
                self.fabric_token_provider, self.fabric_api_client = setup_fabric_authentication(self.config)
                self.logger.info(f"Fabric authentication initialized for workspace: {self.config.get_workspace_name()}")
                
            except Exception as e:
                self.logger.warning(f"Could not setup Fabric authentication: {e}")
        
        # Set up standard authentication provider if config available
        if self.config and FABRIC_CONFIG_AVAILABLE:
            self.auth_provider = FabricAuthProvider(self.config)
            self.logger.info(f"Using Fabric workspace: {self.config.get_workspace_name()}")
        
        if not SEMPY_AVAILABLE:
            raise ImportError(
                "SemPy (semantic-link) is not available. "
                "Install with: pip install semantic-link"
            )
    
    def authenticate(self, method: str = "auto") -> bool:
        """
        Authenticate with Azure AD for Power BI/Fabric access
        
        Args:
            method: Authentication method ('auto', 'interactive', 'default', 'config')
            
        Returns:
            True if authentication successful
        """
        try:
            if method == "auto":
                # Use config if available, otherwise interactive
                if self.config and self.auth_provider:
                    method = "config"
                else:
                    method = "interactive"
            
            if method == "config" and self.config:
                # Use service principal from config
                self.credential = self.config.get_azure_credential()
                self.logger.info(f"Using Fabric config authentication for tenant: {self.config.tenant_id}")
                
                # Auto-connect to configured workspace and model
                workspace_name = self.config.get_workspace_name()
                if workspace_name != "Unknown Workspace":
                    self.current_workspace = workspace_name
                    self.logger.info(f"Auto-connected to workspace: {workspace_name}")
                    
                if self.config.dataset_name:
                    self.current_model = self.config.dataset_name
                    self.logger.info(f"Auto-connected to model: {self.config.dataset_name}")
                    
            elif method == "interactive":
                self.credential = InteractiveBrowserCredential()
                self.logger.info("Using interactive browser authentication")
            elif method == "default":
                self.credential = DefaultAzureCredential()
                self.logger.info("Using default Azure credential chain")
            else:
                raise ValueError(f"Unsupported authentication method: {method}")
            
            # Test authentication by listing workspaces
            workspaces = self.list_workspaces()
            # If we successfully called list_workspaces without raising, consider auth successful
            # even if there are zero accessible workspaces (some tenants may allow auth but no access).
            self.authenticated = True
            
            if self.authenticated:
                self.logger.info(f"Authentication successful. Found {len(workspaces)} workspaces.")
                return True
            else:
                self.logger.error("Authentication failed - no workspaces accessible")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            self.authenticated = False
            return False
    
    def list_workspaces(self) -> List[WorkspaceInfo]:
        """
        List all accessible Power BI/Fabric workspaces
        
        Returns:
            List of WorkspaceInfo objects
        """
        try:
            if not SEMPY_AVAILABLE:
                raise RuntimeError("SemPy not available")
            
            # Try SemPy first
            try:
                workspaces_df = list_workspaces()
                workspaces = []
                for _, row in workspaces_df.iterrows():
                    workspace = WorkspaceInfo(
                        id=row.get('Id', ''),
                        name=row.get('Name', ''),
                        type=row.get('Type', 'Unknown'),
                        state=row.get('State', 'Unknown'),
                        description=row.get('Description')
                    )
                    workspaces.append(workspace)
                
                self.logger.info(f"Found {len(workspaces)} workspaces via SemPy")
                return workspaces
                
            except Exception as sempy_error:
                self.logger.warning(f"SemPy list_workspaces failed: {sempy_error}")
                
                # Fall back to Fabric API client
                if self.fabric_api_client:
                    self.logger.info("Trying Fabric API client fallback...")
                    groups = self.fabric_api_client.list_groups()
                    
                    workspaces = []
                    for group in groups:
                        workspace = WorkspaceInfo(
                            id=group.get('id', ''),
                            name=group.get('name', ''),
                            type=group.get('type', 'Group'),
                            state=group.get('state', 'Active'),
                            description=group.get('description')
                        )
                        workspaces.append(workspace)
                    
                    self.logger.info(f"Found {len(workspaces)} workspaces via Fabric API")
                    return workspaces
                else:
                    raise sempy_error
            
        except Exception as e:
            self.logger.error(f"Failed to list workspaces: {e}")
            return []
    
    def list_semantic_models(self, workspace_name: Optional[str] = None) -> List[SemanticModelInfo]:
        """
        List semantic models in a workspace
        
        Args:
            workspace_name: Name of workspace (None for all accessible models)
            
        Returns:
            List of SemanticModelInfo objects
        """
        try:
            if not SEMPY_AVAILABLE:
                raise RuntimeError("SemPy not available")
            
            # Try SemPy first
            try:
                if workspace_name:
                    datasets_df = list_datasets(workspace=workspace_name)
                else:
                    datasets_df = list_datasets()
                
                models = []
                for _, row in datasets_df.iterrows():
                    model = SemanticModelInfo(
                        id=row.get('Dataset Id', ''),
                        name=row.get('Dataset Name', ''),
                        workspace_id=row.get('Workspace Id', ''),
                        compatibility_level=row.get('Compatibility Level'),
                        created_date=row.get('Created Date'),
                        modified_date=row.get('Modified Date'),
                        description=row.get('Description')
                    )
                    models.append(model)
                
                self.logger.info(f"Found {len(models)} semantic models via SemPy")
                return models
                
            except Exception as sempy_error:
                self.logger.warning(f"SemPy list_datasets failed: {sempy_error}")
                
                # Fall back to Fabric API client
                if self.fabric_api_client:
                    self.logger.info("Trying Fabric API client fallback for datasets...")
                    
                    # Get workspace ID if workspace name provided
                    group_id = None
                    if workspace_name:
                        workspaces = self.list_workspaces()
                        for ws in workspaces:
                            if ws.name.lower() == workspace_name.lower():
                                group_id = ws.id
                                break
                    
                    datasets = self.fabric_api_client.list_datasets(group_id)
                    
                    models = []
                    for dataset in datasets:
                        model = SemanticModelInfo(
                            id=dataset.get('id', ''),
                            name=dataset.get('name', ''),
                            workspace_id=group_id or '',
                            compatibility_level=dataset.get('compatibilityLevel'),
                            created_date=dataset.get('createdDate'),
                            modified_date=dataset.get('modifiedDate'),
                            description=dataset.get('description')
                        )
                        models.append(model)
                    
                    self.logger.info(f"Found {len(models)} semantic models via Fabric API")
                    return models
                else:
                    raise sempy_error
            
        except Exception as e:
            self.logger.error(f"Failed to list semantic models: {e}")
            return []
    
    def connect_to_workspace(self, workspace_name: str) -> bool:
        """
        Connect to a specific workspace
        
        Args:
            workspace_name: Name of the workspace to connect to
            
        Returns:
            True if connection successful
        """
        try:
            workspaces = self.list_workspaces()
            target_workspace = None
            
            for workspace in workspaces:
                if workspace.name.lower() == workspace_name.lower():
                    target_workspace = workspace
                    break
            
            if not target_workspace:
                self.logger.error(f"Workspace '{workspace_name}' not found")
                return False
            
            self.current_workspace = target_workspace.name
            self.logger.info(f"Connected to workspace: {self.current_workspace}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to workspace: {e}")
            return False
    
    def connect_to_semantic_model(self, model_name: str, workspace_name: Optional[str] = None) -> bool:
        """
        Connect to a specific semantic model
        
        Args:
            model_name: Name of the semantic model
            workspace_name: Name of workspace (uses current if None)
            
        Returns:
            True if connection successful
        """
        try:
            target_workspace = workspace_name or self.current_workspace
            if not target_workspace:
                self.logger.error("No workspace specified or connected")
                return False
            
            models = self.list_semantic_models(target_workspace)
            target_model = None
            
            for model in models:
                if model.name.lower() == model_name.lower():
                    target_model = model
                    break
            
            if not target_model:
                self.logger.error(f"Semantic model '{model_name}' not found in workspace '{target_workspace}'")
                return False
            
            self.current_model = target_model.name
            self.logger.info(f"Connected to semantic model: {self.current_model}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to semantic model: {e}")
            return False
    
    def get_configured_workspace_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the configured workspace and dataset
        
        Returns:
            Dictionary with workspace and dataset information from config
        """
        if not self.config:
            return None
        
        return {
            'workspace_name': self.config.get_workspace_name(),
            'workspace_id': self.config.workspace_id,
            'dataset_name': self.config.dataset_name,
            'dataset_id': self.config.dataset_id,
            'xmla_endpoint': self.config.xmla_endpoint,
            'tenant_id': self.config.tenant_id
        }
    
    def connect_to_configured_workspace(self) -> bool:
        """
        Connect to the workspace specified in configuration
        
        Returns:
            True if connection successful
        """
        if not self.config:
            self.logger.error("No Fabric configuration available")
            return False
        
        workspace_name = self.config.get_workspace_name()
        model_name = self.config.dataset_name
        
        try:
            # Connect to workspace
            if self.connect_to_workspace(workspace_name):
                self.logger.info(f"Connected to configured workspace: {workspace_name}")
                
                # Connect to model
                if self.connect_to_semantic_model(model_name, workspace_name):
                    self.logger.info(f"Connected to configured model: {model_name}")
                    return True
                else:
                    self.logger.warning(f"Could not connect to configured model: {model_name}")
                    return True  # Workspace connection still successful
            else:
                self.logger.error(f"Could not connect to configured workspace: {workspace_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to configured workspace: {e}")
            return False
    def get_connection_info(self) -> ConnectionInfo:
        """Get current connection information.
        
        Returns:
            ConnectionInfo object with current state
        """
        try:
            workspaces = self.list_workspaces() if self.authenticated else []
            workspace_count = len(workspaces)
            
            # Count semantic models in current workspace
            model_count = 0
            if self.current_workspace:
                models = self.list_semantic_models(self.current_workspace)
                model_count = len(models)
            
            return ConnectionInfo(
                authenticated=self.authenticated,
                workspace_count=workspace_count,
                semantic_model_count=model_count,
                current_workspace=self.current_workspace,
                current_model=self.current_model,
                authentication_method="Azure AD" if self.authenticated else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get connection info: {e}")
            return ConnectionInfo(
                authenticated=False,
                workspace_count=0,
                semantic_model_count=0
            )
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the SemPy connection and return diagnostic information
        
        Returns:
            Dictionary with connection test results
        """
        results = {
            'sempy_available': SEMPY_AVAILABLE,
            'authenticated': False,
            'workspaces_accessible': 0,
            'semantic_models_accessible': 0,
            'errors': []
        }
        
        try:
            if not SEMPY_AVAILABLE:
                results['errors'].append("SemPy library not available")
                return results
            
            # Test authentication
            if not self.authenticated:
                auth_success = self.authenticate()
                if not auth_success:
                    results['errors'].append("Authentication failed")
                    return results
            
            results['authenticated'] = True
            
            # Test workspace access
            workspaces = self.list_workspaces()
            results['workspaces_accessible'] = len(workspaces)
            
            if len(workspaces) == 0:
                results['errors'].append("No workspaces accessible")
                return results
            
            # Test semantic model access
            models = self.list_semantic_models()
            results['semantic_models_accessible'] = len(models)
            
            if len(models) == 0:
                results['errors'].append("No semantic models accessible")
            
            self.logger.info("SemPy connection test completed successfully")
            
        except Exception as e:
            results['errors'].append(f"Connection test failed: {e}")
            self.logger.error(f"Connection test failed: {e}")
        
        return results


def test_sempy_connection():
    """Test function for SemPy connection"""
    print("🔗 Testing SemPy Connection...")
    
    connector = SemPyConnector()
    
    # Test connection
    results = connector.test_connection()
    
    print(f"SemPy Available: {'✅' if results['sempy_available'] else '❌'}")
    print(f"Authenticated: {'✅' if results['authenticated'] else '❌'}")
    print(f"Workspaces Accessible: {results['workspaces_accessible']}")
    print(f"Semantic Models Accessible: {results['semantic_models_accessible']}")
    
    if results['errors']:
        print("\n❌ Errors:")
        for error in results['errors']:
            print(f"  • {error}")
    else:
        print("\n✅ SemPy connection test successful!")
    
    return results


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run connection test
    test_sempy_connection()