#!/usr/bin/env python3
"""
Fabric API with Correct Scopes
===============================
This script uses Microsoft Fabric APIs with proper authentication scopes to access 
mirrored database tables and semantic models. It's designed to troubleshoot why 
Fabric mirrored databases may not be accessible via standard Power BI APIs.

Key Features:
- Dual token authentication (Power BI + Fabric scopes)
- Fabric semantic model exploration
- Mirrored database status checking
- DAX query testing with actual table names from Fabric
- Comprehensive error handling and diagnostics

Use Case:
When Power BI datasets show as "Abf" storage mode (Azure Blob File), they are
Fabric mirrored databases that may require different API approaches than
traditional Power BI datasets.
"""

import os
import requests
import msal
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file containing Azure AD app registration details
load_dotenv()

class FabricAPIHandler:
    """
    Handle Fabric API with correct authentication scopes
    
    This class manages authentication and API calls to Microsoft Fabric services
    specifically for accessing mirrored databases and their semantic models.
    It handles both Power BI and Fabric authentication tokens since different
    endpoints may require different scopes.
    
    Attributes:
        tenant_id (str): Azure AD tenant ID
        client_id (str): Azure AD application (service principal) ID
        client_secret (str): Azure AD application secret
        workspace_id (str): Power BI/Fabric workspace ID containing the mirrored database
        dataset_id (str): Semantic model ID associated with the mirrored database
        powerbi_token (str): Access token for Power BI APIs
        fabric_token (str): Access token for Fabric APIs
        base_url (str): Base URL for Power BI REST APIs
        fabric_url (str): Base URL for Microsoft Fabric APIs
    """
    
    def __init__(self):
        """
        Initialize the Fabric API handler with environment variables.
        
        Loads configuration from environment variables:
        - PBI_TENANT_ID: Azure AD tenant ID
        - PBI_CLIENT_ID: Service principal application ID
        - PBI_CLIENT_SECRET: Service principal secret
        - POWERBI_WORKSPACE_ID: Target workspace containing mirrored database
        - POWERBI_DATASET_ID: Target semantic model ID (defaults to known value)
        """
        # Load Azure AD and workspace configuration from environment variables
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.dataset_id = os.getenv("POWERBI_DATASET_ID", "fc4d80c8-090e-4441-8336-217490bde820")
        
        # Initialize token storage - will be populated by authentication methods
        self.powerbi_token = None
        self.fabric_token = None
        
        # API endpoint base URLs
        self.base_url = "https://api.powerbi.com/v1.0/myorg"  # Power BI REST API
        self.fabric_url = "https://api.fabric.microsoft.com/v1"  # Microsoft Fabric API
        
    def get_powerbi_token(self):
        """
        Acquire Power BI access token using service principal authentication.
        
        Uses the Microsoft Authentication Library (MSAL) to authenticate with
        Azure AD using client credentials (service principal) flow. The token
        is scoped for Power BI APIs (analysis.windows.net/powerbi/api).
        
        Returns:
            bool: True if token acquisition succeeded, False otherwise
            
        Side Effects:
            Sets self.powerbi_token with the acquired access token
        """
        try:
            # Create MSAL confidential client application for service principal auth
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            # Request token with Power BI API scope
            # The ".default" scope requests all permissions granted to the app in Azure AD
            scopes = ["https://analysis.windows.net/powerbi/api/.default"]
            result = app.acquire_token_for_client(scopes=scopes)
            
            # Check if token acquisition was successful
            if "access_token" in result:
                self.powerbi_token = result["access_token"]
                return True
            else:
                print(f"❌ Power BI token failed: {result.get('error_description', 'Unknown')}")
                return False
                
        except Exception as e:
            print(f"❌ Power BI token error: {e}")
            return False
    
    def get_fabric_token(self):
        """
        Acquire Microsoft Fabric access token with fallback strategy.
        
        Attempts to get a Fabric-specific token first, then falls back to using
        the Power BI token if Fabric scope is not available. Some Fabric APIs
        may work with Power BI tokens depending on the service configuration.
        
        Returns:
            bool: True if token acquisition succeeded, False otherwise
            
        Side Effects:
            Sets self.fabric_token with either a Fabric-specific token or
            the Power BI token as fallback
        """
        try:
            # Create MSAL client for Fabric token acquisition
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            # Try Fabric-specific scope first
            # Microsoft Fabric has its own API scope separate from Power BI
            fabric_scopes = ["https://api.fabric.microsoft.com/.default"]
            result = app.acquire_token_for_client(scopes=fabric_scopes)
            
            if "access_token" in result:
                self.fabric_token = result["access_token"]
                print("✅ Fabric token acquired successfully")
                return True
            else:
                print(f"❌ Fabric token failed: {result.get('error_description', 'Unknown')}")
                print("   Trying with Power BI scope for Fabric APIs...")
                
                # Fallback strategy: Use Power BI token for Fabric APIs
                # Some Fabric endpoints may accept Power BI tokens
                self.fabric_token = self.powerbi_token
                return True
                
        except Exception as e:
            print(f"❌ Fabric token error: {e}")
            return False
    
    def explore_fabric_semantic_model(self):
        """
        Explore the Fabric semantic model structure and retrieve table information.
        
        This method attempts to access the semantic model associated with a 
        Fabric mirrored database to discover what tables and metadata are available.
        This is particularly useful for diagnosing why mirrored databases may
        appear empty or inaccessible.
        
        Returns:
            list: List of table objects from the semantic model, empty list if none found
            
        The method performs two main operations:
        1. Get semantic model details (name, type, workspace info)
        2. Retrieve list of tables within the semantic model
        """
        # Prepare authorization header with Fabric token
        headers = {"Authorization": f"Bearer {self.fabric_token}"}
        
        print("🔍 FABRIC SEMANTIC MODEL EXPLORATION")
        print("-" * 50)
        
        # Step 1: Get semantic model details
        print("1️⃣ Semantic Model Details:")
        try:
            # Call Fabric API to get semantic model information
            response = requests.get(
                f"{self.fabric_url}/workspaces/{self.workspace_id}/semanticModels/{self.dataset_id}",
                headers=headers,
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                model = response.json()
                print("   ✅ Semantic Model Found:")
                print(f"      Name: {model.get('displayName', 'Unknown')}")
                print(f"      Type: {model.get('type', 'Unknown')}")
                print(f"      ID: {model.get('id', 'Unknown')}")
                print(f"      Workspace: {model.get('workspaceId', 'Unknown')}")
            else:
                print(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
        
        # Step 2: Try to get tables from the semantic model
        print("2️⃣ Tables in Semantic Model:")
        try:
            # Call Fabric API to get tables within the semantic model
            # This is where we often get 404 errors if the mirrored database is empty
            response = requests.get(
                f"{self.fabric_url}/workspaces/{self.workspace_id}/semanticModels/{self.dataset_id}/tables",
                headers=headers,
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                tables_data = response.json()
                tables = tables_data.get('value', [])
                print(f"   ✅ Found {len(tables)} tables!")
                
                # Display information about each table found
                for i, table in enumerate(tables[:5], 1):  # Show first 5 tables
                    print(f"      {i}. {table.get('name', 'Unknown')}")
                    print(f"         Description: {table.get('description', 'No description')}")
                    print(f"         Hidden: {table.get('isHidden', False)}")
                
                if len(tables) > 5:
                    print(f"      ... and {len(tables) - 5} more tables")
                    
                return tables
                
            else:
                # This is often where we get 404 EntityNotFound errors
                print(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
        return []
    
    def try_dax_with_actual_tables(self, tables):
        """
        Test DAX queries using actual table names discovered from Fabric.
        
        Once we have table names from the Fabric semantic model, this method
        attempts to execute DAX queries against those specific tables to verify
        they are accessible and contain data.
        
        Args:
            tables (list): List of table objects from Fabric semantic model
            
        Returns:
            bool: True if any DAX query succeeded, False if all failed
            
        The method tests multiple types of DAX queries:
        - Row count queries (COUNTROWS)
        - Data sampling queries (TOPN)
        - Column count queries (COLUMNCOUNT)
        """
        if not tables:
            print("⚠️  No tables found to query")
            return False
            
        # Prepare headers for Power BI API calls (DAX queries use Power BI endpoints)
        headers = {
            "Authorization": f"Bearer {self.powerbi_token}",
            "Content-Type": "application/json"
        }
        
        print("🧪 DAX QUERIES WITH ACTUAL TABLE NAMES")
        print("-" * 50)
        
        # Use Power BI executeQueries endpoint for DAX execution
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        # Test DAX queries against the first 3 tables found
        for i, table in enumerate(tables[:3], 1):  # Test first 3 tables
            table_name = table.get('name', 'Unknown')
            
            # Define test queries for each table
            # These queries test different aspects of table accessibility
            test_queries = [
                (f"Count rows in {table_name}", f"EVALUATE ROW(\"TableRowCount\", COUNTROWS({table_name}))"),
                (f"Top 1 from {table_name}", f"EVALUATE TOPN(1, {table_name})"),
                (f"Column count in {table_name}", f"EVALUATE ROW(\"ColumnCount\", COLUMNCOUNT({table_name}))")
            ]
            
            print(f"Testing Table {i}: {table_name}")
            
            # Execute each test query for the current table
            for test_name, query in test_queries:
                print(f"   {test_name}")
                print(f"   Query: {query}")
                
                # Prepare DAX query payload according to Power BI API specification
                payload = {
                    "queries": [{"query": query}],
                    "serializerSettings": {"includeNulls": True}
                }
                
                try:
                    # Execute the DAX query via Power BI REST API
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    print(f"   Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("   ✅ SUCCESS!")
                        data = response.json()
                        
                        # Parse and display query results
                        if data.get('results') and data['results'][0].get('tables'):
                            result_table = data['results'][0]['tables'][0]
                            rows = result_table.get('rows', [])
                            if rows:
                                print(f"   Result: {rows[0]}")
                        return True
                    else:
                        # Handle and display DAX query errors
                        try:
                            error_data = response.json()
                            error_details = error_data.get('error', {}).get('pbi.error', {}).get('details', [])
                            if error_details:
                                detail = error_details[0].get('detail', {}).get('value', 'No detail')
                                print(f"   Error: {detail}")
                            else:
                                print(f"   Error: {response.text[:100]}")
                        except:
                            print(f"   Error: {response.text[:100]}")
                            
                except Exception as e:
                    print(f"   Exception: {e}")
                print()
        
        return False
    
    def check_mirrored_database_sync(self):
        """
        Check if the mirrored database is properly synced and configured.
        
        This method examines the workspace to identify mirrored databases and
        semantic models, helping to understand the relationship between them
        and diagnose sync issues. It's particularly useful for troubleshooting
        when mirrored databases exist but don't contain accessible data.
        
        The method looks for:
        - Mirrored database items in the workspace
        - Associated semantic models
        - The target semantic model we're trying to access
        """
        # Prepare authorization header with Fabric token
        headers = {"Authorization": f"Bearer {self.fabric_token}"}
        
        print("🔄 MIRRORED DATABASE SYNC CHECK")
        print("-" * 40)
        
        try:
            # Get all items in the workspace to identify mirrored databases
            response = requests.get(
                f"{self.fabric_url}/workspaces/{self.workspace_id}/items",
                headers=headers,
                timeout=30
            )
            
            print(f"Workspace items status: {response.status_code}")
            
            if response.status_code == 200:
                items = response.json().get('value', [])
                print(f"Found {len(items)} items in workspace")
                
                # Categorize items by type to understand workspace structure
                mirrored_dbs = [item for item in items if item.get('type') == 'MirroredDatabase']
                semantic_models = [item for item in items if item.get('type') == 'SemanticModel']
                
                print(f"   Mirrored Databases: {len(mirrored_dbs)}")
                print(f"   Semantic Models: {len(semantic_models)}")
                
                # Display information about each mirrored database
                for db in mirrored_dbs:
                    print(f"      Mirrored DB: {db.get('displayName', 'Unknown')}")
                    
                # Display information about semantic models, highlighting our target
                for model in semantic_models:
                    model_name = model.get('displayName', 'Unknown')
                    model_id = model.get('id', 'Unknown')
                    print(f"      Semantic Model: {model_name}")
                    
                    # Check if this is our target semantic model
                    if model_id == self.dataset_id:
                        print(f"         🎯 This is our target semantic model!")
                        
            else:
                print(f"   ❌ Error getting workspace items: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

def main():
    """
    Main Fabric API handler function.
    
    This is the entry point that orchestrates the entire Fabric mirrored database
    diagnostic process. It performs the following steps:
    
    1. Authenticates with both Power BI and Fabric APIs
    2. Checks mirrored database sync status in the workspace
    3. Explores the semantic model structure to find tables
    4. Tests DAX queries against discovered tables
    5. Provides recommendations based on results
    
    Returns:
        int: 0 if successful, 1 if errors occurred
        
    The function provides comprehensive diagnostics for troubleshooting
    Fabric mirrored databases that may not be accessible via standard
    Power BI APIs.
    """
    print("🏗️ FABRIC API WITH CORRECT SCOPES")
    print("=" * 40)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Access Fabric mirrored database with proper API scopes")
    print()
    
    # Initialize the Fabric API handler
    handler = FabricAPIHandler()
    
    # Step 1: Acquire both Power BI and Fabric authentication tokens
    if not handler.get_powerbi_token():
        print("❌ Cannot proceed without Power BI token")
        return 1
    
    if not handler.get_fabric_token():
        print("❌ Cannot proceed without Fabric token")
        return 1
    
    print("✅ Both tokens acquired successfully")
    print()
    
    # Step 2: Check mirrored database sync status in the workspace
    handler.check_mirrored_database_sync()
    print()
    
    # Step 3: Explore semantic model structure to find available tables
    tables = handler.explore_fabric_semantic_model()
    print()
    
    # Step 4: Test DAX queries with actual table names if tables were found
    if tables:
        success = handler.try_dax_with_actual_tables(tables)
    else:
        success = False
        print("❌ No tables found in semantic model")
    
    # Step 5: Provide summary and recommendations
    print("📊 FABRIC MIRRORED DATABASE RESULTS")
    print("=" * 40)
    
    if success:
        print("🎉 SUCCESS! DAX queries work with Fabric mirrored database")
        print("   The semantic model is properly configured and accessible")
        print("   Tables are available and can be queried")
    elif tables:
        print("⚠️  Tables found but DAX queries still failing")
        print("   This suggests the mirrored database may not be fully synced")
        print("   or there are specific query syntax requirements")
    else:
        print("❌ No tables found in semantic model")
        print("   The mirrored database may not be fully synced")
        print("   or the semantic model needs to be refreshed")
    
    print()
    print("🔧 RECOMMENDATIONS:")
    print("1. Check Fabric portal for mirrored database sync status")
    print("2. Verify semantic model refresh/update status") 
    print("3. Ensure all Azure SQL tables are properly mirrored")
    print("4. Check if mirrored database replication is complete")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if success else 1

if __name__ == "__main__":
    # Execute the main function and exit with the returned status code
    # This allows the script to be run directly and report success/failure
    # to the operating system via exit codes (0 = success, 1 = error)
    exit(main())
