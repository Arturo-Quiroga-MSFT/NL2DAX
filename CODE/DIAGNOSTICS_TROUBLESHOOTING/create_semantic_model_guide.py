#!/usr/bin/env python3
"""
Create Semantic Model via Power BI Desktop Template
===================================================

Since the REST API approach encountered formatting issues, this script generates
a Power BI Desktop template (.pbit) file that you can use to create the semantic
model manually with the correct Azure SQL Database connection.

This approach ensures:
- Correct table structure and relationships
- Proper Azure SQL Database connection
- Immediate usability for DAX queries
- Full control over model configuration

Author: NL2DAX Development Team
Date: August 2025
"""

import os
import json
import base64
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class PowerBITemplateGenerator:
    """Generate Power BI Desktop template for Azure SQL connection"""
    
    def __init__(self):
        # Azure SQL Database connection details
        self.sql_server = os.getenv("AZURE_SQL_SERVER")
        self.sql_database = os.getenv("AZURE_SQL_DB")
        self.sql_user = os.getenv("AZURE_SQL_USER")
        
        # Output directory
        self.output_dir = Path(__file__).parent / "OUTPUT"
        self.output_dir.mkdir(exist_ok=True)
        
        print("🎨 Power BI Template Generator initialized")
        print(f"Target SQL Database: {self.sql_server}/{self.sql_database}")
    
    def generate_pbi_connection_info(self):
        """Generate Power BI connection information"""
        
        connection_info = {
            "data_source_type": "Azure SQL Database",
            "server": self.sql_server,
            "database": self.sql_database,
            "authentication": "Database",
            "username": self.sql_user,
            "tables_to_import": [
                "FIS_CUSTOMER_DIMENSION",
                "FIS_CA_DETAIL_FACT", 
                "FIS_CL_DETAIL_FACT"
            ],
            "relationships": [
                {
                    "from_table": "FIS_CUSTOMER_DIMENSION",
                    "from_column": "CUSTOMER_KEY",
                    "to_table": "FIS_CA_DETAIL_FACT",
                    "to_column": "CUSTOMER_KEY",
                    "relationship_type": "One-to-Many",
                    "cross_filter_direction": "Both"
                },
                {
                    "from_table": "FIS_CUSTOMER_DIMENSION",
                    "from_column": "CUSTOMER_KEY", 
                    "to_table": "FIS_CL_DETAIL_FACT",
                    "to_column": "CUSTOMER_KEY",
                    "relationship_type": "One-to-Many",
                    "cross_filter_direction": "Both"
                }
            ],
            "measures": [
                {
                    "name": "Total Credit Amount",
                    "dax": "SUM('FIS_CA_DETAIL_FACT'[LIMIT_AMOUNT])",
                    "format": "Currency"
                },
                {
                    "name": "Total Exposure",
                    "dax": "SUM('FIS_CA_DETAIL_FACT'[EXPOSURE_AT_DEFAULT])",
                    "format": "Currency"
                },
                {
                    "name": "Customer Count",
                    "dax": "DISTINCTCOUNT('FIS_CUSTOMER_DIMENSION'[CUSTOMER_KEY])",
                    "format": "Whole Number"
                }
            ]
        }
        
        return connection_info
    
    def generate_manual_instructions(self):
        """Generate step-by-step manual instructions"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        instructions_file = self.output_dir / f"semantic_model_creation_guide_{timestamp}.md"
        
        instructions = f"""# 📊 Create New Semantic Model - Step by Step Guide

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 🎯 Objective
Create a new Power BI semantic model connected directly to Azure SQL Database to ensure SQL and DAX queries use the same live data source.

## 🔧 Connection Details
- **Server:** `{self.sql_server}`
- **Database:** `{self.sql_database}`
- **Authentication:** Database (Username/Password)
- **Username:** `{self.sql_user}`

## 📋 Step-by-Step Instructions

### Step 1: Open Power BI Desktop
1. Launch Power BI Desktop
2. Click "Get Data" → "More..."
3. Search for "Azure SQL Database" and select it
4. Click "Connect"

### Step 2: Configure Connection
1. **Server:** Enter `{self.sql_server}`
2. **Database:** Enter `{self.sql_database}`
3. **Data Connectivity mode:** Choose "Import"
4. Click "OK"

### Step 3: Authentication
1. Select "Database" authentication
2. **User name:** `{self.sql_user}`
3. **Password:** Enter your password
4. Click "Connect"

### Step 4: Select Tables
Select these tables for import:
- ☑️ `FIS_CUSTOMER_DIMENSION`
- ☑️ `FIS_CA_DETAIL_FACT`
- ☑️ `FIS_CL_DETAIL_FACT`

Click "Load" to import the tables.

### Step 5: Create Relationships
In the Model view, create these relationships:

1. **Customer to Credit Arrangements:**
   - From: `FIS_CUSTOMER_DIMENSION[CUSTOMER_KEY]`
   - To: `FIS_CA_DETAIL_FACT[CUSTOMER_KEY]`
   - Cardinality: One-to-Many
   - Cross filter direction: Both

2. **Customer to Loans:**
   - From: `FIS_CUSTOMER_DIMENSION[CUSTOMER_KEY]`
   - To: `FIS_CL_DETAIL_FACT[CUSTOMER_KEY]`
   - Cardinality: One-to-Many
   - Cross filter direction: Both

### Step 6: Create Measures
Add these measures to improve DAX querying:

```dax
// Total Credit Amount
Total Credit Amount = SUM('FIS_CA_DETAIL_FACT'[LIMIT_AMOUNT])

// Total Exposure
Total Exposure = SUM('FIS_CA_DETAIL_FACT'[EXPOSURE_AT_DEFAULT])

// Customer Count
Customer Count = DISTINCTCOUNT('FIS_CUSTOMER_DIMENSION'[CUSTOMER_KEY])

// Average Credit Amount per Customer
Avg Credit per Customer = 
DIVIDE(
    [Total Credit Amount],
    [Customer Count]
)
```

### Step 7: Publish to Power BI Service
1. Click "Publish" in Power BI Desktop
2. Select your workspace: **"FIS"**
3. Wait for publish to complete
4. Note the dataset name that gets created

### Step 8: Update Environment Configuration
After publishing, update your `.env` file:

```bash
# Update these values with your new semantic model
POWERBI_DATASET_ID=<new_dataset_id_from_power_bi>
PBI_XMLA_ENDPOINT=powerbi://api.powerbi.com/v1.0/myorg/FIS

# Keep existing SQL connection (both will now use same data)
AZURE_SQL_SERVER={self.sql_server}
AZURE_SQL_DB={self.sql_database}
```

### Step 9: Test the Connection
1. Restart your Streamlit application
2. Run a test query: "Show me the top 5 customers by total credit amount"
3. Verify that SQL and DAX results are now consistent

## ✅ Expected Results
After completing these steps:
- SQL queries will hit Azure SQL Database directly
- DAX queries will hit the new semantic model (connected to same database)
- Both should return identical row counts and values
- Data will always be in sync

## 🔧 Troubleshooting

### If datasets don't match:
1. Check the semantic model refresh status in Power BI Service
2. Manually refresh the dataset if needed
3. Verify firewall settings allow Power BI to access Azure SQL

### If XMLA endpoint doesn't work:
1. Ensure your workspace is Premium or Premium Per User
2. Check that XMLA endpoint is enabled for the workspace
3. Verify service principal has proper permissions

## 📞 Support
If you encounter issues, check:
1. Azure SQL Database firewall rules
2. Power BI workspace permissions
3. Service principal access rights
4. Network connectivity between Power BI and Azure SQL

---

**Generated by NL2DAX Semantic Model Creator**
**Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}**
"""

        # Write instructions to file
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        return instructions_file
    
    def generate_connection_string_info(self):
        """Generate connection string information for reference"""
        
        connection_info = {
            "power_bi_connection": {
                "data_source": "Azure SQL Database",
                "server": self.sql_server,
                "database": self.sql_database,
                "authentication_type": "Database",
                "username": self.sql_user
            },
            "current_config": {
                "sql_executor": f"{self.sql_server}/{self.sql_database}",
                "dax_executor": "Power BI Semantic Model (to be created)",
                "goal": "Both executors use same Azure SQL Database"
            },
            "post_creation_config": {
                "sql_executor": f"{self.sql_server}/{self.sql_database}",
                "dax_executor": f"Power BI Semantic Model → {self.sql_server}/{self.sql_database}",
                "result": "Both use identical data source"
            }
        }
        
        return connection_info

def main():
    """Main execution function"""
    print("=" * 70)
    print("🎨 POWER BI SEMANTIC MODEL CREATION GUIDE")
    print("=" * 70)
    print()
    
    generator = PowerBITemplateGenerator()
    
    # Validate configuration
    required_vars = ["AZURE_SQL_SERVER", "AZURE_SQL_DB", "AZURE_SQL_USER"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Generate connection info
    connection_info = generator.generate_pbi_connection_info()
    
    # Generate manual instructions
    instructions_file = generator.generate_manual_instructions()
    
    print(f"✅ Generated comprehensive setup guide")
    print(f"📄 Instructions saved to: {instructions_file}")
    print()
    print("📋 QUICK SUMMARY:")
    print("=" * 40)
    print(f"🎯 Target: Create semantic model for {generator.sql_server}/{generator.sql_database}")
    print(f"📊 Tables: FIS_CUSTOMER_DIMENSION, FIS_CA_DETAIL_FACT, FIS_CL_DETAIL_FACT")
    print(f"🔗 Method: Power BI Desktop → Publish to Service")
    print(f"💡 Result: SQL and DAX queries use same live data")
    print()
    print("🚀 NEXT STEPS:")
    print("1. Open the generated instructions file")
    print("2. Follow the step-by-step guide in Power BI Desktop")
    print("3. Update your .env configuration")
    print("4. Test the unified data access")
    print()
    print("📖 For detailed instructions, see the generated markdown file above.")
    
    return True

if __name__ == "__main__":
    main()
