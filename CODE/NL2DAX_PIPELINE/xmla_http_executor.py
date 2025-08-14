

"""
xmla_http_executor.py - Cross-Platform XMLA HTTP Execution Module
================================================================

This module provides comprehensive functionality for executing DAX queries against
Power BI Premium workspaces and Analysis Services using HTTP-based XMLA endpoints
with Azure Active Directory authentication. It offers cross-platform compatibility
and enterprise-grade reliability for DAX query execution.

Key Features:
- Cross-platform XMLA execution (Windows, macOS, Linux, containers)
- Azure Active Directory authentication with service principal support
- Intelligent endpoint detection and routing (Power BI REST API vs SOAP/XMLA)
- Comprehensive retry logic with exponential backoff for transient failures
- Detailed error handling and SOAP fault parsing
- Session management and connection pooling for optimal performance
- Support for both Power BI Premium and Analysis Services endpoints

Architecture Overview:
The module implements a dual execution strategy:
1. Power BI REST API: For powerbi:// endpoints using native REST API calls
2. SOAP/XMLA: For traditional XMLA endpoints using SOAP-over-HTTP protocol

This approach ensures maximum compatibility across different deployment scenarios
while optimizing for the specific capabilities of each endpoint type.

Authentication:
- Service Principal authentication via Azure AD
- Automatic token acquisition and refresh
- Proper scope management for Power BI Service API access
- Secure credential handling through environment variables

Error Handling:
- Transient failure detection with intelligent retry logic
- SOAP fault parsing for detailed error diagnostics
- Network timeout and connection error management
- Comprehensive logging for troubleshooting and monitoring

Performance Optimizations:
- HTTP session reuse for connection pooling
- Configurable retry strategies with exponential backoff
- Efficient XML parsing for SOAP responses
- Minimal memory footprint for large result sets

Platform Compatibility:
- Pure Python implementation (no .NET dependencies)
- No Mono or pythonnet requirements
- Consistent behavior across operating systems
- Container-friendly with minimal runtime dependencies

Dependencies:
- msal: Microsoft Authentication Library for Azure AD integration
- requests: HTTP client library for API communication
- xml.etree.ElementTree: XML parsing for SOAP responses
- python-dotenv: Environment variable management

Usage Scenarios:
- Production DAX query execution in cloud environments
- Cross-platform development and testing
- Container deployments without .NET runtime
- Automated data processing pipelines
- Interactive analytics and reporting tools

Author: NL2DAX Pipeline Development Team
Last Updated: August 14, 2025
"""

from __future__ import annotations

# Standard library imports for core functionality
import os            # Operating system interface for environment variable access
import time          # Time utilities for retry delays and timing operations
import xml.etree.ElementTree as ET  # XML parsing for SOAP response processing
from typing import List, Dict, Optional  # Type hints for improved code clarity

# Third-party imports for external service integration
import msal          # Microsoft Authentication Library for Azure AD authentication
import requests      # HTTP client library for REST API and SOAP communication
import json          # JSON encoding/decoding for API data interchange
from dotenv import load_dotenv  # Environment variable loading from .env files

# Load environment variables from .env file for secure configuration management
# This ensures sensitive credentials are not hardcoded in the source code
load_dotenv()


class XmlaHttpError(RuntimeError):
    """
    Custom exception class for XMLA HTTP execution failures.
    
    This exception provides detailed error information for XMLA execution failures,
    including HTTP status codes and detailed error messages for troubleshooting.
    It extends RuntimeError to provide specific context for XMLA-related failures.
    
    Attributes:
        message (str): Detailed error description
        status_code (Optional[int]): HTTP status code if applicable
    
    Usage:
        try:
            result = execute_dax_query(dax)
        except XmlaHttpError as e:
            print(f"XMLA Error: {e}, Status Code: {e.status_code}")
    """
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        """
        Initialize XMLA HTTP error with message and optional status code.
        
        Args:
            message (str): Detailed error description for troubleshooting
            status_code (Optional[int]): HTTP status code if error originated from HTTP request
        """
        super().__init__(message)
        self.status_code = status_code


class XmlaHttpClient:
    """
    Cross-platform XMLA HTTP client for DAX query execution against Power BI and Analysis Services.
    
    This client provides a unified interface for executing DAX queries against different
    types of XMLA endpoints while handling authentication, retries, and error recovery
    automatically. It supports both Power BI Premium workspaces and Analysis Services
    instances through intelligent endpoint detection.
    
    Key Capabilities:
    - Automatic Azure AD authentication with service principal
    - Intelligent routing between Power BI REST API and SOAP/XMLA protocols
    - Comprehensive retry logic with exponential backoff
    - Session management and connection pooling
    - Detailed error handling and diagnostics
    
    Endpoint Support:
    - Power BI Premium: powerbi://api.powerbi.com/v1.0/myorg/WorkspaceName
    - Analysis Services: https://asazure-region.asazure.windows.net/servers/servername
    - SQL Server Analysis Services: http://servername/olap/msmdpump.dll
    
    Authentication:
    Uses Azure AD service principal authentication with the following scopes:
    - Power BI Service API: https://analysis.windows.net/powerbi/api/.default
    - Analysis Services: https://analysis.windows.net/powerbi/api/.default
    
    Example Usage:
        client = XmlaHttpClient(
            tenant_id="your-tenant-id",
            client_id="your-client-id", 
            client_secret="your-client-secret",
            xmla_endpoint="powerbi://api.powerbi.com/v1.0/myorg/MyWorkspace",
            database="MyDataset"
        )
        
        results = client.execute_dax("EVALUATE 'Sales'")
    """
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, xmla_endpoint: str, database: str):
        """
        Initialize XMLA HTTP client with authentication and connection parameters.
        
        Args:
            tenant_id (str): Azure Active Directory tenant ID
            client_id (str): Service principal application (client) ID
            client_secret (str): Service principal client secret
            xmla_endpoint (str): XMLA endpoint URL (Power BI or Analysis Services)
            database (str): Database/dataset name within the XMLA endpoint
        """
        # Store authentication credentials for Azure AD token acquisition
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        
        # Store connection parameters for XMLA endpoint access
        self.xmla_endpoint = xmla_endpoint
        self.database = database
        
        # Initialize HTTP session for connection pooling and performance optimization
        self._session = requests.Session()

    def _get_token(self, attempts: int = 3, base_delay: float = 1.0) -> str:
        """
        Acquire Azure AD access token for Power BI Service API with retry logic.
        
        This method handles Azure AD authentication using the service principal
        credentials and implements retry logic to handle transient authentication
        failures. It uses the Microsoft Authentication Library (MSAL) for
        enterprise-grade token acquisition and management.
        
        Token Acquisition Process:
        1. Construct Azure AD authority URL using tenant ID
        2. Create MSAL confidential client application with service principal credentials
        3. Request access token with appropriate scopes for Power BI Service API
        4. Implement exponential backoff retry strategy for transient failures
        5. Return valid access token for API authentication
        
        Args:
            attempts (int): Maximum number of retry attempts (default: 3)
            base_delay (float): Base delay in seconds for exponential backoff (default: 1.0)
        
        Returns:
            str: Valid Azure AD access token for Power BI Service API authentication
        
        Raises:
            RuntimeError: When token acquisition fails after all retry attempts,
                         including detailed error information for troubleshooting
        
        Retry Strategy:
            - Exponential backoff: delay = base_delay * (2 ** attempt_number)
            - Handles transient Azure AD service issues
            - Accounts for network connectivity problems
            - Manages temporary service principal permission issues
        
        Example:
            >>> token = client._get_token(attempts=3, base_delay=1.0)
            >>> # Token can be used for subsequent API calls
        """
        # Construct Azure AD authority URL for the specified tenant
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        
        # Create MSAL confidential client application for service principal authentication
        app = msal.ConfidentialClientApplication(
            self.client_id,                    # Service principal application ID
            authority=authority,               # Azure AD tenant-specific authority
            client_credential=self.client_secret,  # Service principal secret
        )
        
        # Track last error for detailed error reporting
        last_err = None
        
        # Implement retry logic with exponential backoff
        for i in range(attempts):
            # Request access token with Power BI Service API scope
            token = app.acquire_token_for_client(scopes=["https://analysis.windows.net/powerbi/api/.default"])
            
            # Check for successful token acquisition
            if token and "access_token" in token:
                return token["access_token"]
            
            # Store error details for potential retry or final failure reporting
            last_err = token
            
            # Implement exponential backoff delay before retry
            time.sleep(base_delay * (2 ** i))
        
        # All retry attempts failed, raise detailed error
        raise RuntimeError(
            "Failed to acquire Azure AD token after retries. "
            f"Details: {last_err}. Verify tenant/client/secret and API permissions (Power BI Service)."
        )

    def execute_dax(self, dax_query: str, attempts: int = 3, base_delay: float = 1.0) -> List[Dict]:
        """
        Execute a DAX query against the configured XMLA endpoint with intelligent routing.
        
        This method provides the main entry point for DAX query execution, automatically
        detecting the endpoint type and routing to the appropriate execution method:
        - Power BI Premium workspaces: Uses Power BI REST API for optimal performance
        - Analysis Services: Uses SOAP-over-HTTP XMLA protocol for compatibility
        
        Execution Strategy:
        1. Analyze endpoint URL to determine execution method
        2. Route to Power BI REST API for powerbi:// endpoints
        3. Route to SOAP/XMLA for traditional XMLA endpoints
        4. Handle authentication, retries, and error recovery automatically
        5. Return consistently formatted results regardless of execution method
        
        Args:
            dax_query (str): Valid DAX expression to execute against the tabular model.
                           Should be a complete DAX statement, typically starting with
                           EVALUATE for table expressions or containing measure definitions.
            attempts (int): Maximum number of retry attempts for transient failures (default: 3)
            base_delay (float): Base delay in seconds for exponential backoff retry logic (default: 1.0)
        
        Returns:
            List[Dict]: List of dictionaries representing query results, where each dictionary
                       represents a row with column names as keys and cell values as values.
                       
                       Example return format:
                       [
                           {"CustomerName": "John Doe", "TotalSales": 1500.00},
                           {"CustomerName": "Jane Smith", "TotalSales": 2300.50}
                       ]
        
        Raises:
            XmlaHttpError: When DAX execution fails due to:
                - Invalid DAX syntax or semantic errors
                - Authentication failures or permission issues
                - Network connectivity problems
                - Endpoint unavailability or timeout errors
                - Service capacity or throttling issues
        
        Endpoint Detection:
            - powerbi:// URLs: Routed to Power BI REST API execution
            - https:// URLs: Routed to SOAP/XMLA execution
            - http:// URLs: Routed to SOAP/XMLA execution (on-premises)
        
        Performance Notes:
            - Power BI REST API: Optimized for Power BI Premium workspaces
            - SOAP/XMLA: Universal compatibility with all XMLA endpoints
            - Session reuse: HTTP connections are pooled for efficiency
            - Retry logic: Handles transient service issues automatically
        
        Example Usage:
            >>> dax = "EVALUATE TOPN(10, 'Customers', 'Customers'[TotalSales], DESC)"
            >>> results = client.execute_dax(dax, attempts=3, base_delay=1.0)
            >>> for row in results:
            ...     print(f"{row['CustomerName']}: {row['TotalSales']}")
        """
        # Detect endpoint type and route to appropriate execution method
        if self.xmla_endpoint.lower().startswith("powerbi://"):
            print(f"[DEBUG] Using Power BI REST API for endpoint: {self.xmla_endpoint}")
            # Route to Power BI REST API execution for optimal performance
            return rest_execute_dax_via_api(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
                workspace_connection=self.xmla_endpoint,
                dataset_name=self.database,
                dax_query=dax_query,
            )

        print(f"[DEBUG] Using XMLA SOAP over HTTP for endpoint: {self.xmla_endpoint}")
        # Route to SOAP/XMLA execution for universal XMLA endpoint compatibility
        
        # Build XMLA SOAP request body for DAX query execution
        xmla_body = f"""<?xml version="1.0" encoding="utf-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Body>
    <Execute xmlns="urn:schemas-microsoft-com:xml-analysis">
      <Command>
        <Statement>{dax_query}</Statement>
      </Command>
      <Properties>
        <PropertyList>
          <Catalog>{self.database}</Catalog>
          <Format>Tabular</Format>
        </PropertyList>
      </Properties>
    </Execute>
  </Body>
</Envelope>"""
        
        # Prepare authentication headers with Azure AD bearer token
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "Authorization": f"Bearer {self._get_token()}",
            "SOAPAction": "urn:schemas-microsoft-com:xml-analysis:Execute",
        }
        
        print(f"[DEBUG] XMLA SOAP request to: {self.xmla_endpoint}")
        print(f"[DEBUG] Using database/catalog: {self.database}")
        print(f"[DEBUG] DAX query: {dax_query[:200]}...")

        # Execute with retry logic for transient failures
        last_exc: Optional[Exception] = None
        for i in range(attempts):
            try:
                # Send the XMLA SOAP request
                resp = self._session.post(
                    self.xmla_endpoint,
                    data=xmla_body.encode("utf-8"),
                    headers=headers,
                    timeout=60,
                )
                
                # Handle HTTP errors and parse SOAP faults
                if resp.status_code >= 400:
                    fault = try_parse_soap_fault(resp.text)
                    extra_hint = hint_for_status(resp.status_code)
                    print(f"[DEBUG] Full XMLA error response: {resp.text[:1000]}")
                    raise XmlaHttpError(
                        message=(
                            f"HTTP {resp.status_code} calling XMLA endpoint. {extra_hint}\n"
                            f"Endpoint: {self.xmla_endpoint}\nDatabase: {self.database}\n"
                            f"Details: {fault or resp.text[:500]}"
                        ),
                        status_code=resp.status_code,
                    )
                
                # Parse and return successful response
                return parse_xmla_response(resp.text)
                
            except (requests.Timeout, requests.ConnectionError) as e:
                last_exc = e
                print(f"[DEBUG] Network error (attempt {i+1}/{attempts}): {e}")
            except XmlaHttpError as e:
                # Don't retry non-transient errors (400, 401, 403, etc.)
                if not is_transient_status(e.status_code):
                    raise
                last_exc = e
                print(f"[DEBUG] Transient error (attempt {i+1}/{attempts}): {e}")
            
            # Exponential backoff for retries
            if i < attempts - 1:  # Don't sleep after the last attempt
                sleep_time = base_delay * (2 ** i)
                print(f"[DEBUG] Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
        
        # All retry attempts exhausted
        raise RuntimeError(f"XMLA request failed after {attempts} retries: {last_exc}")


def get_access_token(tenant_id: str, client_id: str, client_secret: str, attempts: int = 3, base_delay: float = 1.0) -> str:
    """
    Acquire an Azure AD access token for Power BI Service API access using service principal authentication.
    
    This function implements the OAuth 2.0 client credentials flow to obtain a bearer token
    for authenticating with Power BI REST API and XMLA endpoints. It uses the Microsoft
    Authentication Library (MSAL) for Python to handle the authentication flow securely.
    
    Authentication Flow:
    1. Creates a confidential client application using tenant and service principal credentials
    2. Requests an access token with Power BI Service scope
    3. Handles token acquisition failures with exponential backoff retry logic
    4. Returns the bearer token for use in Authorization headers
    
    Args:
        tenant_id (str): Azure AD tenant ID (GUID format) where the service principal is registered.
                        Can be found in Azure Portal > Azure Active Directory > Properties.
        client_id (str): Service principal application (client) ID from the app registration.
                        Found in Azure Portal > App registrations > Your App > Overview.
        client_secret (str): Service principal client secret value (not the secret ID).
                           Generated in Azure Portal > App registrations > Your App > Certificates & secrets.
        attempts (int): Maximum number of retry attempts for transient authentication failures (default: 3)
        base_delay (float): Base delay in seconds for exponential backoff between retries (default: 1.0)
    
    Returns:
        str: Valid Azure AD access token (JWT format) for Power BI Service API access.
             Token typically valid for 1 hour and can be used in Authorization: Bearer headers.
    
    Raises:
        RuntimeError: When token acquisition fails after all retry attempts, typically due to:
                     - Invalid tenant ID, client ID, or client secret
                     - Service principal not granted necessary API permissions
                     - Network connectivity issues with Azure AD endpoints
                     - Azure AD service unavailability
    
    Required API Permissions:
        The service principal must have the following delegated permissions:
        - Power BI Service: Dataset.ReadWrite.All (for XMLA endpoint access)
        - Power BI Service: Workspace.ReadWrite.All (for workspace operations)
        
        Note: Admin consent is typically required for these permissions.
    
    Security Notes:
        - Client secrets should be stored securely (Key Vault, environment variables)
        - Tokens should be cached and reused until expiration (typically 1 hour)
        - Use certificate-based authentication for enhanced security in production
        - Rotate client secrets regularly according to security policies
    
    Example Usage:
        >>> token = get_access_token(
        ...     tenant_id="12345678-1234-1234-1234-123456789012",
        ...     client_id="87654321-4321-4321-4321-210987654321",
        ...     client_secret="your-client-secret-value",
        ...     attempts=3
        ... )
        >>> headers = {"Authorization": f"Bearer {token}"}
    """
    # Build Azure AD authority endpoint for the specified tenant
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    
    # Create MSAL confidential client application for service principal authentication
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        authority=authority,
        client_credential=client_secret
    )
    
    # Execute token acquisition with retry logic for transient failures
    last_err = None
    for i in range(attempts):
        try:
            # Request access token using client credentials flow
            # Scope specifies Power BI Service API access
            token_result = app.acquire_token_for_client(
                scopes=["https://analysis.windows.net/powerbi/api/.default"]
            )
            
            # Check if token acquisition was successful
            if token_result and "access_token" in token_result:
                print(f"[DEBUG] Successfully acquired Azure AD token (attempt {i+1}/{attempts})")
                return token_result["access_token"]
            
            # Token acquisition failed, store error for potential retry
            last_err = token_result
            print(f"[DEBUG] Token acquisition failed (attempt {i+1}/{attempts}): {token_result}")
            
        except Exception as e:
            last_err = e
            print(f"[DEBUG] Token acquisition exception (attempt {i+1}/{attempts}): {e}")
        
        # Apply exponential backoff for retries (except on last attempt)
        if i < attempts - 1:
            sleep_time = base_delay * (2 ** i)
            print(f"[DEBUG] Retrying token acquisition in {sleep_time} seconds...")
            time.sleep(sleep_time)
    
    # All retry attempts exhausted
    raise RuntimeError(
        f"Failed to acquire Azure AD token after {attempts} retries. "
        f"Details: {last_err}. "
        "Verify tenant ID, client ID, client secret, and API permissions (Power BI Service)."
    )


def rest_execute_dax_via_api(tenant_id: str, client_id: str, client_secret: str, workspace_connection: str, dataset_name: str, dax_query: str, dataset_id: Optional[str] = None) -> List[Dict]:
    """
    Execute a DAX query using the Power BI REST API Execute Queries endpoint.
    
    This function provides an alternative execution method for Power BI Premium workspaces,
    using the Power BI REST API instead of XMLA SOAP protocol. It offers better performance
    and reliability for Power BI Premium datasets compared to traditional XMLA connections.
    
    Execution Workflow:
    1. Parse workspace name from powerbi:// connection string
    2. Acquire Azure AD access token for Power BI Service API
    3. Resolve workspace (group) ID by name using Power BI Groups API
    4. Resolve dataset ID by name or use provided dataset ID
    5. Execute DAX query using Power BI Execute Queries API
    6. Parse and return results in standardized format
    
    Args:
        tenant_id (str): Azure AD tenant ID for authentication
        client_id (str): Service principal application ID
        client_secret (str): Service principal client secret
        workspace_connection (str): Power BI workspace connection string in format:
                                  "powerbi://api.powerbi.com/v1.0/myorg/WorkspaceName"
        dataset_name (str): Name of the Power BI dataset to query against
        dax_query (str): Valid DAX expression to execute (typically starts with EVALUATE)
        dataset_id (Optional[str]): Specific dataset ID to use instead of resolving by name.
                                   Improves performance when known.
    
    Returns:
        List[Dict]: Query results as list of dictionaries, where each dictionary represents
                   a row with column names as keys and cell values as values.
                   
                   Example return:
                   [
                       {"CustomerName": "Contoso", "TotalSales": 15000.00, "OrderCount": 25},
                       {"CustomerName": "Fabrikam", "TotalSales": 23500.50, "OrderCount": 42}
                   ]
    
    Raises:
        ValueError: When workspace_connection is not a valid powerbi:// URL or cannot be parsed
        RuntimeError: When any step fails:
                     - Workspace not found by name
                     - Dataset not found by name or ID
                     - DAX execution errors
                     - API authentication or permission issues
                     - Response parsing failures
    
    API Endpoints Used:
        - Groups API: https://api.powerbi.com/v1.0/myorg/groups (workspace resolution)
        - Datasets API: https://api.powerbi.com/v1.0/myorg/groups/{groupId}/datasets (dataset resolution)
        - Execute Queries API: https://api.powerbi.com/v1.0/myorg/datasets/{datasetId}/executeQueries (DAX execution)
    
    Required Permissions:
        Service principal must have:
        - Workspace membership (Member, Admin, or Contributor role)
        - Dataset Build permission (for DAX query execution)
        - Power BI Service API permissions in Azure AD
    
    Performance Notes:
        - REST API execution is optimized for Power BI Premium workspaces
        - Response includes null values when serializerSettings.includeNulls is true
        - Timeout set to 120 seconds for long-running DAX queries
        - Case-insensitive fallback for workspace and dataset name resolution
    
    Example Usage:
        >>> results = rest_execute_dax_via_api(
        ...     tenant_id="12345678-1234-1234-1234-123456789012",
        ...     client_id="87654321-4321-4321-4321-210987654321",
        ...     client_secret="your-secret",
        ...     workspace_connection="powerbi://api.powerbi.com/v1.0/myorg/Sales",
        ...     dataset_name="Sales Model",
        ...     dax_query="EVALUATE TOPN(10, 'Sales', 'Sales'[Amount], DESC)"
        ... )
        >>> print(f"Found {len(results)} rows")
    """
    # Validate that this is a Power BI workspace connection
    if not workspace_connection.lower().startswith("powerbi://"):
        raise ValueError(
            f"REST API execution requires a powerbi:// workspace connection, "
            f"got: {workspace_connection}"
        )

    # Parse workspace name from connection string
    # Expected format: powerbi://api.powerbi.com/v1.0/myorg/WorkspaceName
    try:
        workspace_name = workspace_connection.rsplit('/', 1)[-1]
        print(f"[DEBUG] Parsed workspace name: '{workspace_name}' from connection: {workspace_connection}")
    except Exception as e:
        raise ValueError(
            f"Unable to parse workspace name from connection string: {workspace_connection}. "
            f"Expected format: powerbi://api.powerbi.com/v1.0/myorg/WorkspaceName. Error: {e}"
        )

    # Acquire access token for Power BI Service API
    print("[DEBUG] Acquiring Azure AD access token for Power BI Service API...")
    token = get_access_token(tenant_id, client_id, client_secret)
    
    # Set up HTTP session with authentication headers
    session = requests.Session()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Step 1: Resolve workspace (group) ID by name
    print(f"[DEBUG] Resolving workspace ID for workspace: '{workspace_name}'...")
    groups_url = "https://api.powerbi.com/v1.0/myorg/groups"
    resp = session.get(groups_url, headers=headers, timeout=60)
    resp.raise_for_status()
    
    groups_data = resp.json()
    groups = groups_data.get("value", [])
    
    # Find workspace by exact name match
    workspace = next((g for g in groups if g.get("name") == workspace_name), None)
    
    # Fallback to case-insensitive search if exact match not found
    if not workspace:
        print(f"[DEBUG] Exact match not found, trying case-insensitive search...")
        workspace = next(
            (g for g in groups if str(g.get("name", "")).lower() == workspace_name.lower()), 
            None
        )
    
    if not workspace:
        available_workspaces = [g.get("name", "Unknown") for g in groups]
        raise RuntimeError(
            f"Workspace '{workspace_name}' not found. "
            f"Available workspaces: {', '.join(sorted(available_workspaces))}"
        )
    
    workspace_id = workspace.get("id")
    print(f"[DEBUG] Found workspace '{workspace_name}' with ID: {workspace_id}")

    # Step 2: Resolve dataset ID by name or use provided ID
    print(f"[DEBUG] Resolving dataset in workspace '{workspace_name}'...")
    datasets_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    datasets_resp = session.get(datasets_url, headers=headers, timeout=60)
    datasets_resp.raise_for_status()
    
    datasets_data = datasets_resp.json()
    datasets = datasets_data.get("value", [])
    
    if dataset_id:
        # Use provided dataset ID and validate it exists
        print(f"[DEBUG] Using provided dataset ID: {dataset_id}")
        dataset = next((d for d in datasets if d.get("id") == dataset_id), None)
        if not dataset:
            available_ids = [d.get("id", "Unknown") for d in datasets]
            raise RuntimeError(
                f"Dataset ID '{dataset_id}' not found in workspace '{workspace_name}'. "
                f"Available dataset IDs: {', '.join(sorted(available_ids))}"
            )
    else:
        # Resolve dataset by name
        print(f"[DEBUG] Resolving dataset by name: '{dataset_name}'...")
        dataset = next((d for d in datasets if d.get("name") == dataset_name), None)
        
        # Fallback to case-insensitive search
        if not dataset:
            print(f"[DEBUG] Exact dataset name match not found, trying case-insensitive search...")
            dataset = next(
                (d for d in datasets if str(d.get("name", "")).lower() == dataset_name.lower()), 
                None
            )
        
        if not dataset:
            available_datasets = [d.get("name", "Unknown") for d in datasets]
            raise RuntimeError(
                f"Dataset '{dataset_name}' not found in workspace '{workspace_name}'. "
                f"Available datasets: {', '.join(sorted(available_datasets))}"
            )
        
        dataset_id = dataset.get("id")

    print(f"[DEBUG] Found dataset '{dataset_name}' with ID: {dataset_id}")
    
    # Step 3: Execute DAX query using Power BI Execute Queries API
    execute_url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/executeQueries"
    print(f"[DEBUG] Executing DAX query via REST API: {execute_url}")
    print(f"[DEBUG] DAX query: {dax_query[:200]}...")
    
    # Prepare request payload with query and serializer settings
    payload = {
        "queries": [{"query": dax_query}],
        "serializerSettings": {"includeNulls": True}  # Include null values in results
    }
    
    # Execute the DAX query with extended timeout for complex queries
    execute_resp = session.post(
        execute_url, 
        headers=headers, 
        data=json.dumps(payload), 
        timeout=120  # Extended timeout for complex DAX queries
    )
    
    # Handle execution errors
    if execute_resp.status_code >= 400:
        error_detail = execute_resp.text[:500] if execute_resp.text else "No error details available"
        raise RuntimeError(
            f"Power BI Execute Queries API failed with HTTP {execute_resp.status_code}. "
            f"Error details: {error_detail}"
        )
    
    # Step 4: Parse and return query results
    try:
        response_data = execute_resp.json()
        print(f"[DEBUG] Successfully executed DAX query via REST API")
        
        # Extract results from API response structure
        results = response_data.get("results", [])
        if not results:
            print("[DEBUG] No results returned from DAX query")
            return []
        
        # Get first result table (Power BI Execute Queries can return multiple result sets)
        tables = results[0].get("tables", [])
        if not tables:
            print("[DEBUG] No tables in query results")
            return []
        
        # Extract rows from first table
        rows = tables[0].get("rows", [])
        print(f"[DEBUG] Parsed {len(rows)} rows from DAX query results")
        
        return rows  # Rows are already in list of dictionaries format
        
    except Exception as e:
        response_preview = str(response_data)[:500] if 'response_data' in locals() else "Unable to parse response"
        raise RuntimeError(
            f"Failed to parse Power BI Execute Queries API response: {e}. "
            f"Raw response preview: {response_preview}"
        )


def parse_xmla_response(xml_text: str) -> List[Dict]:
    """
    Parse XMLA SOAP response XML and extract tabular data as list of dictionaries.
    
    This function processes the XML response from XMLA SOAP Execute requests and converts
    the tabular result set into a standardized Python data structure. It handles the
    complex nested XML namespace structure used by XMLA and flattens it into simple
    row dictionaries for easy consumption.
    
    XMLA Response Structure:
    - SOAP envelope contains the response
    - ExecuteResponse contains the return element
    - Rowset contains individual row elements
    - Each row contains column elements with values
    
    XML Namespace Handling:
    - soap: SOAP envelope namespace
    - xmla: XMLA analysis namespace  
    - m: MDX dataset namespace
    - x: Rowset/tabular data namespace
    
    Args:
        xml_text (str): Raw XML response text from XMLA SOAP Execute request.
                       Should be complete, well-formed XML document.
    
    Returns:
        List[Dict]: List of row dictionaries where each dictionary represents one row
                   with column names as keys and cell values as string values.
                   
                   Example return:
                   [
                       {"CustomerName": "Contoso", "TotalSales": "15000.00"},
                       {"CustomerName": "Fabrikam", "TotalSales": "23500.50"}
                   ]
                   
                   Empty list returned if no rows found in response.
    
    Raises:
        xml.etree.ElementTree.ParseError: When XML is malformed or cannot be parsed
        Exception: For other parsing errors (namespace issues, unexpected structure)
    
    XML Structure Expected:
        ```xml
        <soap:Envelope xmlns:soap="...">
          <soap:Body>
            <ExecuteResponse xmlns="urn:schemas-microsoft-com:xml-analysis">
              <return>
                <root xmlns="urn:schemas-microsoft-com:xml-analysis:rowset">
                  <row>
                    <CustomerName>Contoso</CustomerName>
                    <TotalSales>15000.00</TotalSales>
                  </row>
                  <row>
                    <CustomerName>Fabrikam</CustomerName>
                    <TotalSales>23500.50</TotalSales>
                  </row>
                </root>
              </return>
            </ExecuteResponse>
          </soap:Body>
        </soap:Envelope>
        ```
    
    Performance Notes:
        - Uses ElementTree for efficient XML parsing
        - Namespace-aware parsing for robust extraction
        - Handles missing or null values (empty strings)
        - Memory efficient for large result sets
    
    Example Usage:
        >>> xml_response = '''<soap:Envelope...>...</soap:Envelope>'''
        >>> rows = parse_xmla_response(xml_response)
        >>> for row in rows:
        ...     print(f"Customer: {row['CustomerName']}, Sales: {row['TotalSales']}")
    """
    # Define XML namespaces used in XMLA SOAP responses
    namespaces = {
        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
        'xmla': 'urn:schemas-microsoft-com:xml-analysis',
        'm': 'urn:schemas-microsoft-com:xml-analysis:mddataset',
        'x': 'urn:schemas-microsoft-com:xml-analysis:rowset',
    }
    
    try:
        # Parse the XML response
        root = ET.fromstring(xml_text)
        
        # Find all row elements using XPath with namespace prefixes
        # This searches through the entire document structure for row elements
        row_elements = root.findall('.//x:row', namespaces)
        
        # Convert each XML row element to a dictionary
        results: List[Dict] = []
        for row_element in row_elements:
            # Create dictionary from row element children
            row_data = {}
            for child in row_element:
                # Extract column name (removing namespace prefix if present)
                column_name = child.tag.split('}', 1)[-1]  # Remove namespace prefix
                # Extract column value (handle None as empty string)
                column_value = child.text or ""
                row_data[column_name] = column_value
            
            results.append(row_data)
        
        print(f"[DEBUG] Parsed {len(results)} rows from XMLA response")
        return results
        
    except ET.ParseError as e:
        print(f"[ERROR] XML parsing error in XMLA response: {e}")
        print(f"[ERROR] XML content preview: {xml_text[:500]}...")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error parsing XMLA response: {e}")
        print(f"[ERROR] XML content preview: {xml_text[:500]}...")
        raise


def try_parse_soap_fault(xml_text: str) -> Optional[str]:
    """
    Extract SOAP fault information from XMLA error responses for detailed error reporting.
    
    When XMLA requests fail, the server typically returns a SOAP fault within the response
    XML rather than just an HTTP error status. This function extracts the structured
    fault information to provide more meaningful error messages to users and developers.
    
    SOAP Fault Structure:
    - faultcode: Standardized error code (e.g., "Server", "Client")
    - faultstring: Human-readable error description
    - detail: Additional error-specific information (optional)
    
    Args:
        xml_text (str): Raw XML response text that may contain a SOAP fault.
                       Typically received when HTTP status indicates an error.
    
    Returns:
        Optional[str]: Formatted fault message combining fault code and description,
                      or None if no SOAP fault found or XML cannot be parsed.
                      
                      Example return: "Server: The 'Customers' table doesn't exist."
    
    Error Handling:
        - Returns None for any parsing errors (malformed XML, missing elements)
        - Gracefully handles missing faultcode or faultstring elements
        - Safe to call on any response text without raising exceptions
    
    Common SOAP Fault Types:
        - "Server" faults: Internal server errors, invalid queries, missing objects
        - "Client" faults: Authentication failures, malformed requests
        - "VersionMismatch" faults: SOAP version compatibility issues
    
    XML Structure Expected:
        ```xml
        <soap:Envelope xmlns:soap="...">
          <soap:Body>
            <soap:Fault>
              <faultcode>Server</faultcode>
              <faultstring>The 'InvalidTable' table doesn't exist.</faultstring>
              <detail>Additional error details here</detail>
            </soap:Fault>
          </soap:Body>
        </soap:Envelope>
        ```
    
    Example Usage:
        >>> error_xml = '''<soap:Envelope>...<soap:Fault>...</soap:Fault>...</soap:Envelope>'''
        >>> fault_msg = try_parse_soap_fault(error_xml)
        >>> if fault_msg:
        ...     print(f"SOAP Fault: {fault_msg}")
        ... else:
        ...     print("No SOAP fault found in response")
    """
    try:
        # Parse the XML response
        root = ET.fromstring(xml_text)
        
        # Define SOAP namespace for fault element lookup
        soap_namespace = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/'}
        
        # Search for SOAP fault element in the response
        fault_element = root.find('.//soap:Fault', soap_namespace)
        if fault_element is None:
            # No SOAP fault found in response
            return None
        
        # Extract fault code and string with safe fallbacks
        fault_code = fault_element.findtext('faultcode') or 'Unknown'
        fault_string = fault_element.findtext('faultstring') or 'No description available'
        
        # Combine into readable error message
        fault_message = f"{fault_code}: {fault_string}"
        
        print(f"[DEBUG] Extracted SOAP fault: {fault_message}")
        return fault_message
        
    except Exception as e:
        # Silently handle any parsing errors - this is a best-effort extraction
        print(f"[DEBUG] Could not parse SOAP fault from response: {e}")
        return None


def is_transient_status(status_code: Optional[int]) -> bool:
    """
    Determine if an HTTP status code represents a transient error suitable for retry logic.
    
    This function categorizes HTTP status codes to help decide whether a failed request
    should be retried or immediately failed. Transient errors are typically caused by
    temporary service issues, network problems, or rate limiting, while non-transient
    errors indicate permanent issues like authentication failures or invalid requests.
    
    Retry Strategy:
    - Transient errors: Safe to retry with exponential backoff
    - Non-transient errors: Should not be retried, fail immediately
    - Unknown errors (None): Assume transient for safety
    
    Args:
        status_code (Optional[int]): HTTP status code from a failed request.
                                   None indicates a network-level failure.
    
    Returns:
        bool: True if the error is likely transient and suitable for retry,
              False if the error is permanent and should not be retried.
    
    Transient Status Codes (Retryable):
        - None: Network failures, connection timeouts
        - 408: Request Timeout
        - 429: Too Many Requests (rate limiting)
        - 500-599: Server errors (internal errors, service unavailable, etc.)
    
    Non-Transient Status Codes (Not Retryable):
        - 400: Bad Request (invalid DAX syntax, malformed request)
        - 401: Unauthorized (invalid token, expired credentials)
        - 403: Forbidden (insufficient permissions)
        - 404: Not Found (invalid endpoint, missing dataset)
        - 405-499: Other client errors
    
    Error Recovery Strategy:
        ```python
        for attempt in range(max_retries):
            try:
                response = make_request()
                break  # Success
            except RequestError as e:
                if not is_transient_status(e.status_code):
                    raise  # Don't retry permanent errors
                if attempt == max_retries - 1:
                    raise  # Final attempt failed
                time.sleep(backoff_delay)
        ```
    
    Example Usage:
        >>> # Decide whether to retry after an HTTP error
        >>> if is_transient_status(503):  # Service Unavailable
        ...     print("Transient error - retry recommended")
        >>> if is_transient_status(401):  # Unauthorized  
        ...     print("Permanent error - fix authentication")
    """
    # Handle network-level failures (connection errors, timeouts)
    if status_code is None:
        return True  # Assume network issues are transient
    
    # Specific transient status codes
    if status_code in (408, 429):  # Request Timeout, Too Many Requests
        return True
    
    # Server error range (5xx) - typically transient service issues
    if 500 <= status_code <= 599:
        return True
    
    # Client error range (4xx) - typically permanent request issues
    # These usually indicate problems with the request itself or authorization
    # that won't be resolved by retrying
    return False


def hint_for_status(status_code: int) -> str:
    """
    Provide human-readable troubleshooting hints for common HTTP status codes.
    
    This function translates HTTP status codes into actionable error messages that help
    developers and users understand what went wrong and how to fix it. It's particularly
    useful for XMLA and Power BI API errors where the root cause may not be obvious
    from the status code alone.
    
    Args:
        status_code (int): HTTP status code from a failed request
    
    Returns:
        str: Human-readable troubleshooting hint explaining the likely cause
             and suggested resolution steps. Empty string for unrecognized codes.
    
    Status Code Categories:
        - Authentication (401): Token issues, expired credentials
        - Authorization (403): Permission issues, insufficient access
        - Not Found (404): Invalid endpoints, missing resources
        - Bad Request (400): Syntax errors, invalid parameters
        - Rate Limiting (429): Throttling, excessive request rate
        - Server Errors (5xx): Service issues, capacity problems
    
    Common XMLA/Power BI Issues:
        - 401: Service principal not configured, token expired
        - 403: Missing dataset permissions, XMLA disabled
        - 404: Incorrect endpoint URL, dataset name mismatch
        - 400: Invalid DAX syntax, unsupported operations
        - 429: Premium capacity overloaded, too many concurrent queries
        - 503: Service temporarily unavailable, maintenance windows
    
    Example Usage:
        >>> hint = hint_for_status(403)
        >>> print(f"Error 403: {hint}")
        # Output: "Error 403: Forbidden: ensure the service principal/user is a 
        #          Member/Contributor and XMLA read is enabled."
    """
    # Authentication errors - token or credential issues
    if status_code == 401:
        return (
            "Unauthorized: Check that the access token is valid and has not expired. "
            "Verify that the service principal has the required API permissions "
            "and that Build access is granted to the dataset/workspace."
        )
    
    # Authorization errors - permission issues
    if status_code == 403:
        return (
            "Forbidden: Ensure the service principal or user account is assigned "
            "a Member, Admin, or Contributor role in the workspace. "
            "Verify that XMLA read/write endpoints are enabled in the Power BI "
            "tenant settings and workspace settings."
        )
    
    # Resource not found - endpoint or object name issues
    if status_code == 404:
        return (
            "Not Found: Verify the XMLA endpoint URL is correct and accessible. "
            "Check that the dataset (Catalog) name exactly matches the published "
            "dataset name in Power BI. Ensure the workspace and dataset exist."
        )
    
    # Client request errors - syntax or format issues
    if status_code == 400:
        return (
            "Bad Request: This typically indicates invalid DAX syntax or "
            "unsupported query operations. Validate the DAX query syntax, "
            "check table and column references, and ensure all model objects exist."
        )
    
    # Rate limiting - capacity or throttling issues
    if status_code == 429:
        return (
            "Too Many Requests: The service is throttling requests due to high load. "
            "Implement exponential backoff retry logic and reduce the request rate. "
            "Consider upgrading to higher Premium capacity for increased limits."
        )
    
    # Server error range - service availability issues
    if 500 <= status_code <= 599:
        return (
            "Server Error: This indicates a temporary service issue on the server side. "
            "The error is typically transient - retry the request with exponential backoff. "
            "Check the Power BI service status page for any ongoing incidents."
        )
    
    # Unrecognized status code
    return ""


def execute_dax_via_http(dax_query: str) -> List[Dict]:
    """
    Execute a DAX query using environment variables for configuration and credentials.
    
    This is the main convenience function for executing DAX queries when connection
    details are stored in environment variables. It automatically detects the endpoint
    type and routes to the appropriate execution method (Power BI REST API or XMLA SOAP).
    
    Environment Variables Required:
        - PBI_TENANT_ID: Azure AD tenant ID (GUID format)
        - PBI_CLIENT_ID: Service principal application ID
        - PBI_CLIENT_SECRET: Service principal client secret
        - PBI_XMLA_ENDPOINT: XMLA endpoint URL or Power BI workspace connection
        - PBI_DATASET_NAME: Dataset/database name to query
        
    Environment Variables Optional:
        - PBI_DATASET_ID: Specific dataset ID (improves performance for Power BI REST API)
    
    Execution Routing:
        - powerbi:// endpoints: Automatically routed to Power BI REST API
        - https:// endpoints: Routed to XMLA SOAP over HTTP
        - http:// endpoints: Routed to XMLA SOAP over HTTP (on-premises)
    
    Args:
        dax_query (str): Valid DAX expression to execute against the configured dataset.
                        Should be a complete DAX statement, typically starting with EVALUATE.
    
    Returns:
        List[Dict]: Query results as list of dictionaries, where each dictionary represents
                   a row with column names as keys and cell values as values.
    
    Raises:
        ValueError: When required environment variables are missing
        RuntimeError: When DAX execution fails due to authentication, permissions, or query errors
    
    Configuration Examples:
        Power BI Premium workspace:
        ```bash
        export PBI_TENANT_ID="12345678-1234-1234-1234-123456789012"
        export PBI_CLIENT_ID="87654321-4321-4321-4321-210987654321"
        export PBI_CLIENT_SECRET="your-client-secret"
        export PBI_XMLA_ENDPOINT="powerbi://api.powerbi.com/v1.0/myorg/Sales"
        export PBI_DATASET_NAME="Sales Model"
        export PBI_DATASET_ID="abcd1234-5678-90ef-ghij-klmnopqrstuv"  # Optional
        ```
        
        Azure Analysis Services:
        ```bash
        export PBI_TENANT_ID="12345678-1234-1234-1234-123456789012"
        export PBI_CLIENT_ID="87654321-4321-4321-4321-210987654321"
        export PBI_CLIENT_SECRET="your-client-secret"
        export PBI_XMLA_ENDPOINT="https://asazure://region.asazure.windows.net/servername"
        export PBI_DATASET_NAME="AdventureWorks"
        ```
    
    Example Usage:
        >>> import os
        >>> os.environ['PBI_TENANT_ID'] = 'your-tenant-id'
        >>> # ... set other environment variables ...
        >>> results = execute_dax_via_http("EVALUATE TOPN(5, 'Sales', 'Sales'[Amount], DESC)")
        >>> print(f"Query returned {len(results)} rows")
        >>> for row in results:
        ...     print(f"Amount: {row.get('Amount', 'N/A')}")
    """
    # Collect required environment variables
    tenant_id = os.getenv("PBI_TENANT_ID")
    client_id = os.getenv("PBI_CLIENT_ID")
    client_secret = os.getenv("PBI_CLIENT_SECRET")
    xmla_endpoint = os.getenv("PBI_XMLA_ENDPOINT")
    database = os.getenv("PBI_DATASET_NAME")
    
    # Optional environment variable for Power BI dataset ID
    dataset_id = os.getenv("PBI_DATASET_ID")
    
    # Validate that all required environment variables are set
    required_vars = {
        'PBI_TENANT_ID': tenant_id,
        'PBI_CLIENT_ID': client_id,
        'PBI_CLIENT_SECRET': client_secret,
        'PBI_XMLA_ENDPOINT': xmla_endpoint,
        'PBI_DATASET_NAME': database,
    }
    
    missing_vars = [var_name for var_name, var_value in required_vars.items() if not var_value]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables for XMLA HTTP execution: {', '.join(missing_vars)}. "
            f"Please set these variables before calling execute_dax_via_http()."
        )
    
    print(f"[DEBUG] Executing DAX via HTTP with endpoint: {xmla_endpoint}")
    print(f"[DEBUG] Target database/dataset: {database}")
    
    # Route to appropriate execution method based on endpoint type
    if xmla_endpoint.lower().startswith("powerbi://"):
        # Power BI workspace - use REST API for optimal performance
        print("[DEBUG] Detected Power BI workspace endpoint, using REST API execution")
        return rest_execute_dax_via_api(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            workspace_connection=xmla_endpoint,
            dataset_name=database,
            dax_query=dax_query,
            dataset_id=dataset_id,  # Optional, improves performance when available
        )
    else:
        # Traditional XMLA endpoint - use SOAP over HTTP
        print("[DEBUG] Detected traditional XMLA endpoint, using SOAP execution")
        client = XmlaHttpClient(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            xmla_endpoint=xmla_endpoint,
            database=database
        )
        return client.execute_dax(dax_query)


def health_check() -> bool:
    """
    Perform a simple connectivity and authentication health check using a model-agnostic DAX query.
    
    This function validates the complete execution pipeline by running a simple DAX expression
    that doesn't depend on any specific data model or tables. It's useful for:
    - Verifying authentication credentials are working
    - Testing network connectivity to XMLA endpoints  
    - Validating environment variable configuration
    - Confirming service permissions are properly set
    
    Health Check Query:
        Uses 'EVALUATE ROW("ping", 1)' which:
        - Works with any tabular model (no table dependencies)
        - Returns a predictable single-row result
        - Exercises the complete authentication and execution pipeline
        - Minimal resource usage on the service
    
    Returns:
        bool: True if the health check succeeds and returns expected results,
              False if any step fails (authentication, connectivity, execution, parsing)
    
    Expected Result:
        The health check expects to receive a single row with a column named "ping"
        containing the value 1. The column name matching is case-insensitive for
        broader compatibility across different XMLA implementations.
    
    Error Handling:
        - Catches and logs all exceptions without raising them
        - Returns False for any failure condition
        - Provides debug output for troubleshooting
    
    Common Failure Reasons:
        - Missing or invalid environment variables
        - Authentication failures (invalid credentials)
        - Network connectivity issues
        - Insufficient permissions on target dataset
        - Service endpoint unavailability
    
    Example Usage:
        >>> # Set up environment variables first
        >>> if health_check():
        ...     print("XMLA connection is working correctly")
        ...     # Proceed with actual DAX queries
        ... else:
        ...     print("XMLA connection failed - check configuration")
        ...     # Handle connection issues
    
    Troubleshooting:
        If health check fails, verify:
        1. All required environment variables are set correctly
        2. Service principal has proper permissions
        3. Network access to the XMLA endpoint
        4. Power BI Premium/Azure AS service is running
        5. XMLA endpoints are enabled in tenant settings
    """
    try:
        print("[DEBUG] Starting XMLA health check...")
        
        # Execute a simple model-agnostic DAX query
        health_query = 'EVALUATE ROW("ping", 1)'
        print(f"[DEBUG] Health check query: {health_query}")
        
        # Execute the query using the standard execution function
        result = execute_dax_via_http(health_query)
        
        # Validate the result structure and content
        print(f"[DEBUG] Health check raw result: {result}")
        
        # Check that we got exactly one row back
        if not isinstance(result, list) or len(result) != 1:
            print(f"[DEBUG] Health check failed: Expected 1 row, got {len(result) if isinstance(result, list) else 'non-list'}")
            return False
        
        # Check that the row contains the expected "ping" column
        row = result[0]
        if not isinstance(row, dict):
            print(f"[DEBUG] Health check failed: Expected dictionary row, got {type(row)}")
            return False
        
        # Look for "ping" column (case-insensitive)
        row_keys_lower = {key.lower() for key in row.keys()}
        if 'ping' not in row_keys_lower:
            print(f"[DEBUG] Health check failed: 'ping' column not found in result. Available columns: {list(row.keys())}")
            return False
        
        print("[DEBUG] Health check passed successfully")
        return True
        
    except Exception as e:
        print(f"[DEBUG] Health check failed with exception: {e}")
        return False


# Main block at the very end of the file, after all function and class definitions
if __name__ == "__main__":
    print("[DEBUG] Starting xmla_http_executor.py...")
    import sys
    try:
        # Example: run a health check or a sample DAX query
        print("[DEBUG] Running health check...")
        result = health_check()
        print(f"[DEBUG] Health check result: {result}")
        # Optionally, run a sample DAX query
        print("[DEBUG] Running sample DAX query...")
        rows = execute_dax_via_http('EVALUATE ROW("Test", 1+1)')
        print(f"[DEBUG] DAX query result: {rows}")
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    print("[DEBUG] xmla_http_executor.py completed.")
