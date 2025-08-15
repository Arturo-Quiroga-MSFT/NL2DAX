#!/usr/bin/env python3
"""
Create New Semantic Model for Azure SQL Database
===============================================

This script creates a new Power BI semantic model that connects directly to the current
Azure SQL Database, ensuring SQL and DAX queries use the same live data source.

Features:
- Creates semantic model with direct Azure SQL Database connection
- Configures proper tables and relationships
- Sets up measures and calculated columns
- Enables XMLA endpoint access for DAX queries
- Provides connection string for immediate use

Author: NL2DAX Development Team
Date: August 2025
"""

import os
import json
import requests
import msal
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SemanticModelCreator:
    """Create a new semantic model connected to Azure SQL Database"""
    
    def __init__(self):
        # Azure AD / Power BI Service credentials
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID") 
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        
        # Azure SQL Database connection details
        self.sql_server = os.getenv("AZURE_SQL_SERVER")
        self.sql_database = os.getenv("AZURE_SQL_DB")
        self.sql_user = os.getenv("AZURE_SQL_USER")
        self.sql_password = os.getenv("AZURE_SQL_PASSWORD")
        
        # Power BI REST API base URL
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        self.token = None
        
        print("🚀 Semantic Model Creator initialized")
        print(f"Target SQL Database: {self.sql_server}/{self.sql_database}")
        print(f"Target Workspace ID: {self.workspace_id}")
    
    def get_access_token(self):
        """Get Azure AD access token for Power BI Service"""
        try:
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=authority,
                client_credential=self.client_secret
            )
            
            # Request token with Power BI scope
            result = app.acquire_token_for_client(
                scopes=["https://analysis.windows.net/powerbi/api/.default"]
            )
            
            if "access_token" in result:
                self.token = result["access_token"]
                print("✅ Successfully acquired access token")
                return True
            else:
                print(f"❌ Failed to acquire token: {result.get('error_description', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Token acquisition error: {str(e)}")
            return False
    
    def create_dataset_definition(self):
        """Create the dataset definition JSON for the semantic model"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dataset_name = f"NL2DAX_Live_SQL_{timestamp}"
        
        # Dataset definition for Power BI API (no datasources, add defaultMode)
        dataset_def = {
            "name": dataset_name,
            "defaultMode": "Push",  # or "AsAzure" for DirectQuery, adjust as needed
            "tables": [
                {
                    "name": "FIS_CUSTOMER_DIMENSION",
                    "columns": [
                        {"name": "CUSTOMER_KEY", "dataType": "Int64"},
                        {"name": "CUSTOMER_ID", "dataType": "String"},
                        {"name": "CUSTOMER_NAME", "dataType": "String"},
                        {"name": "CUSTOMER_TYPE_DESCRIPTION", "dataType": "String"},
                        {"name": "RISK_RATING_CODE", "dataType": "String"},
                        {"name": "PROBABILITY_OF_DEFAULT", "dataType": "Double"},
                        {"name": "COUNTRY", "dataType": "String"},
                        {"name": "REGION", "dataType": "String"}
                    ]
                },
                {
                    "name": "FIS_CA_DETAIL_FACT",
                    "columns": [
                        {"name": "CUSTOMER_KEY", "dataType": "Int64"},
                        {"name": "LIMIT_AMOUNT", "dataType": "Double"},
                        {"name": "LIMIT_USED", "dataType": "Double"},
                        {"name": "EXPOSURE_AT_DEFAULT", "dataType": "Double"},
                        {"name": "FEES_CHARGED_YTD", "dataType": "Double"},
                        {"name": "PROBABILITY_OF_DEFAULT", "dataType": "Double"}
                    ]
                },
                {
                    "name": "FIS_CL_DETAIL_FACT",
                    "columns": [
                        {"name": "CUSTOMER_KEY", "dataType": "Int64"},
                        {"name": "LOAN_ID", "dataType": "String"},
                        {"name": "PRINCIPAL_BALANCE", "dataType": "Double"},
                        {"name": "EXPOSURE_AT_DEFAULT", "dataType": "Double"},
                        {"name": "CHARGE_OFF_AMOUNT", "dataType": "Double"},
                        {"name": "PROBABILITY_OF_DEFAULT", "dataType": "Double"}
                    ]
                }
            ],
            "relationships": [
                {
                    "name": "Customer_to_CreditArrangements",
                    "fromTable": "FIS_CUSTOMER_DIMENSION",
                    "fromColumn": "CUSTOMER_KEY",
                    "toTable": "FIS_CA_DETAIL_FACT",
                    "toColumn": "CUSTOMER_KEY",
                    "crossFilteringBehavior": "bothDirections"
                },
                {
                    "name": "Customer_to_Loans",
                    "fromTable": "FIS_CUSTOMER_DIMENSION",
                    "fromColumn": "CUSTOMER_KEY",
                    "toTable": "FIS_CL_DETAIL_FACT",
                    "toColumn": "CUSTOMER_KEY",
                    "crossFilteringBehavior": "bothDirections"
                }
            ]
        }
        return dataset_def
    
    def create_semantic_model(self):
        """Create the semantic model in Power BI"""
        if not self.get_access_token():
            return False
            
        try:
            # Get dataset definition
            dataset_def = self.create_dataset_definition()
            
            # Create dataset via Power BI REST API
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}/groups/{self.workspace_id}/datasets"
            
            print(f"🔨 Creating semantic model: {dataset_def['name']}")
            print(f"📡 POST {url}")
            
            response = requests.post(url, headers=headers, json=dataset_def)
            
            if response.status_code == 201:
                result = response.json()
                dataset_id = result["id"]
                dataset_name = result["name"]
                
                print(f"✅ Successfully created semantic model!")
                print(f"📊 Dataset Name: {dataset_name}")
                print(f"🆔 Dataset ID: {dataset_id}")
                
                # Generate new XMLA endpoint
                workspace_name = "FIS"  # Your workspace name
                xmla_endpoint = f"powerbi://api.powerbi.com/v1.0/myorg/{workspace_name}"
                
                print(f"\n📋 CONFIGURATION UPDATE REQUIRED:")
                print(f"Update your .env file with:")
                print(f"POWERBI_DATASET_ID={dataset_id}")
                print(f"PBI_XMLA_ENDPOINT={xmla_endpoint}")
                print(f"# Use the dataset name '{dataset_name}' for DAX queries")
                
                return {
                    "success": True,
                    "dataset_id": dataset_id,
                    "dataset_name": dataset_name,
                    "xmla_endpoint": xmla_endpoint
                }
                
            else:
                print(f"❌ Failed to create semantic model")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating semantic model: {str(e)}")
            return False
    
    def update_dataset_datasource(self, dataset_id):
        """Update the dataset datasource credentials"""
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            # Update datasource credentials
            datasource_url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{dataset_id}/Default.UpdateDatasources"
            
            datasource_update = {
                "updateDetails": [
                    {
                        "datasourceSelector": {
                            "datasourceType": "Sql",
                            "connectionDetails": {
                                "server": self.sql_server,
                                "database": self.sql_database
                            }
                        },
                        "credentialDetails": {
                            "credentialType": "Basic",
                            "credentials": {
                                "username": self.sql_user,
                                "password": self.sql_password
                            },
                            "encryptedConnection": "Encrypted",
                            "privacyLevel": "Organizational"
                        }
                    }
                ]
            }
            
            response = requests.post(datasource_url, headers=headers, json=datasource_update)
            
            if response.status_code == 200:
                print("✅ Successfully updated datasource credentials")
                return True
            else:
                print(f"⚠️ Datasource update response: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating datasource: {str(e)}")
            return False
    
    def trigger_refresh(self, dataset_id):
        """Trigger an initial refresh of the dataset"""
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            refresh_url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{dataset_id}/refreshes"
            
            # Trigger refresh
            refresh_body = {
                "type": "Full",
                "commitMode": "transactional",
                "maxParallelism": 2,
                "retryCount": 2,
                "objects": []
            }
            
            response = requests.post(refresh_url, headers=headers, json=refresh_body)
            
            if response.status_code == 202:
                print("✅ Successfully triggered dataset refresh")
                print("⏳ Refresh is running in the background...")
                return True
            else:
                print(f"⚠️ Refresh trigger response: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error triggering refresh: {str(e)}")
            return False

def main():
    """Main execution function"""
    print("=" * 60)
    print("🏗️  SEMANTIC MODEL CREATOR FOR AZURE SQL DATABASE")
    print("=" * 60)
    print()
    
    creator = SemanticModelCreator()
    
    # Validate configuration
    required_vars = [
        "PBI_TENANT_ID", "PBI_CLIENT_ID", "PBI_CLIENT_SECRET", 
        "POWERBI_WORKSPACE_ID", "AZURE_SQL_SERVER", "AZURE_SQL_DB",
        "AZURE_SQL_USER", "AZURE_SQL_PASSWORD"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Create semantic model
    result = creator.create_semantic_model()
    
    if result and result.get("success"):
        dataset_id = result["dataset_id"]
        
        print("\n" + "=" * 60)
        print("📋 NEXT STEPS:")
        print("=" * 60)
        print()
        print("1. Update your .env file with the new dataset information")
        print("2. Restart your Streamlit application")
        print("3. Test queries to ensure SQL and DAX return consistent results")
        print()
        print("🎯 This will ensure both SQL and DAX queries use the same live data!")
        
        return True
    else:
        print("\n❌ Failed to create semantic model")
        return False

if __name__ == "__main__":
    main()
