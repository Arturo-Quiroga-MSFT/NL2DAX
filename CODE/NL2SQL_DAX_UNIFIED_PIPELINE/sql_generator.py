#!/usr/bin/env python3
"""
sql_generator.py - Natural Language to SQL Query Generator
==========================================================

This module converts natural language queries to SQL queries using
Azure OpenAI and schema-aware generation techniques.

Author: Unified Pipeline Team
Date: August 2025
"""

import os
import json
from typing import Dict, List, Any, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SQLGenerator:
    """Generate SQL queries from natural language using Azure OpenAI"""
    
    def __init__(self):
        """Initialize the SQL generator"""
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        # Validate configuration
        if not all([os.getenv("AZURE_OPENAI_API_KEY"), os.getenv("AZURE_OPENAI_ENDPOINT"), self.deployment_name]):
            raise ValueError("Missing Azure OpenAI configuration. Check your .env file.")
    
    def test_openai_connection(self) -> bool:
        """Test connection to Azure OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": "Hello, this is a test."}],
                max_completion_tokens=10
            )
            return len(response.choices) > 0
        except Exception as e:
            print(f"❌ Azure OpenAI connection test failed: {str(e)}")
            return False
    
    def generate_sql(self, natural_language_query: str, schema_info: Dict[str, Any]) -> str:
        """
        Generate SQL query from natural language
        
        Args:
            natural_language_query: The natural language query
            schema_info: Database schema information
            
        Returns:
            Generated SQL query string
        """
        try:
            # Create schema context for the prompt
            schema_context = self._create_schema_context(schema_info)
            
            # Create the prompt
            prompt = self._create_sql_generation_prompt(natural_language_query, schema_context)
            
            # Generate SQL using Azure OpenAI (o4-mini reasoning model)
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert SQL developer. Generate accurate T-SQL queries for Azure SQL Database based on the provided schema and natural language requests."
                    },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_completion_tokens=2000,  # Increased for o4-mini reasoning model
            reasoning_effort="medium"
        )            # Extract SQL from response
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up the SQL
            sql_query = self._clean_sql_query(sql_query)
            
            return sql_query
            
        except Exception as e:
            print(f"❌ SQL generation failed: {str(e)}")
            return f"-- SQL generation failed: {str(e)}"
    
    def _create_schema_context(self, schema_info: Dict[str, Any]) -> str:
        """Create schema context for the prompt"""
        context_parts = []
        
        # Add database information
        context_parts.append(f"Database: {schema_info.get('database', 'Unknown')}")
        context_parts.append("")
        
        # Add table information
        context_parts.append("Available Tables:")
        for table in schema_info.get("tables", []):
            table_name = table.get("full_name", table.get("name", "Unknown"))
            context_parts.append(f"\\n{table_name}:")
            
            # Add column information
            for column in table.get("columns", []):
                col_info = f"  - {column['name']} ({column['data_type']}"
                if column.get('max_length'):
                    col_info += f"({column['max_length']})"
                if not column.get('is_nullable', True):
                    col_info += ", NOT NULL"
                col_info += ")"
                context_parts.append(col_info)
            
            # Add primary key information
            if table.get("primary_key"):
                pk_cols = ", ".join(table["primary_key"])
                context_parts.append(f"  Primary Key: {pk_cols}")
            
            # Add sample data if available
            if table.get("sample_data"):
                context_parts.append("  Sample data:")
                for i, sample in enumerate(table["sample_data"][:2], 1):
                    sample_str = ", ".join([f"{k}={v}" for k, v in sample.items()])
                    context_parts.append(f"    {i}. {sample_str}")
            
            context_parts.append("")
        
        # Add relationship information
        if schema_info.get("relationships"):
            context_parts.append("Table Relationships:")
            for rel in schema_info["relationships"]:
                rel_info = f"  {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}"
                context_parts.append(rel_info)
            context_parts.append("")
        
        return "\\n".join(context_parts)
    
    def _create_sql_generation_prompt(self, natural_language_query: str, schema_context: str) -> str:
        """Create the prompt for SQL generation"""
        prompt = f"""
Given the following database schema and natural language query, generate an accurate T-SQL query for Azure SQL Database.

{schema_context}

Natural Language Query: "{natural_language_query}"

Requirements:
1. Generate only valid T-SQL syntax for Azure SQL Database
2. Use proper table and column names from the schema above
3. Include appropriate WHERE clauses, JOINs, and aggregations as needed
4. Use proper data types and avoid syntax errors
5. Return only the SQL query without explanations or comments
6. Use TOP instead of LIMIT for row limiting
7. Handle NULL values appropriately
8. Use square brackets for table/column names if they contain spaces or special characters

SQL Query:
"""
        return prompt
    
    def _clean_sql_query(self, sql_query: str) -> str:
        """Clean and validate the generated SQL query"""
        # Remove common markdown artifacts
        sql_query = sql_query.replace("```sql", "").replace("```", "")
        
        # Remove leading/trailing whitespace
        sql_query = sql_query.strip()
        
        # Remove any explanatory text before/after the SQL
        lines = sql_query.split("\\n")
        sql_lines = []
        in_sql = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines at the beginning
            if not line and not in_sql:
                continue
            
            # Start collecting SQL when we see SQL keywords
            if any(line.upper().startswith(keyword) for keyword in ['SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE']):
                in_sql = True
            
            if in_sql:
                sql_lines.append(line)
                
                # Stop at semicolon (end of query)
                if line.endswith(';'):
                    break
        
        # Join the SQL lines
        cleaned_sql = "\\n".join(sql_lines)
        
        # Ensure it ends with semicolon
        if cleaned_sql and not cleaned_sql.rstrip().endswith(';'):
            cleaned_sql += ';'
        
        return cleaned_sql
    
    def validate_sql_syntax(self, sql_query: str) -> Dict[str, Any]:
        """Basic SQL syntax validation"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Basic checks
        if not sql_query.strip():
            validation_result["is_valid"] = False
            validation_result["errors"].append("Empty SQL query")
            return validation_result
        
        # Check for required SQL keywords
        sql_upper = sql_query.upper()
        if not any(keyword in sql_upper for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
            validation_result["is_valid"] = False
            validation_result["errors"].append("No valid SQL statement found")
        
        # Check for balanced parentheses
        if sql_query.count('(') != sql_query.count(')'):
            validation_result["warnings"].append("Unbalanced parentheses detected")
        
        # Check for common T-SQL specific features
        if 'LIMIT ' in sql_upper:
            validation_result["warnings"].append("LIMIT syntax detected - consider using TOP for T-SQL")
        
        return validation_result
    
    def generate_sql_with_validation(self, natural_language_query: str, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL with validation"""
        sql_query = self.generate_sql(natural_language_query, schema_info)
        validation = self.validate_sql_syntax(sql_query)
        
        return {
            "sql_query": sql_query,
            "validation": validation,
            "natural_language_query": natural_language_query
        }

def main():
    """Test the SQL generator"""
    print("🧪 Testing SQL Generator")
    print("=" * 40)
    
    generator = SQLGenerator()
    
    # Test OpenAI connection
    print("🔌 Testing Azure OpenAI connection...")
    if generator.test_openai_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed!")
        return 1
    
    # Sample schema for testing
    sample_schema = {
        "database": "testdb",
        "tables": [
            {
                "name": "FIS_CUSTOMER_DIMENSION",
                "full_name": "dbo.FIS_CUSTOMER_DIMENSION",
                "columns": [
                    {"name": "CUSTOMER_KEY", "data_type": "int", "is_nullable": False},
                    {"name": "CUSTOMER_NAME", "data_type": "varchar", "max_length": 100},
                    {"name": "RISK_RATING_CODE", "data_type": "varchar", "max_length": 10},
                    {"name": "COUNTRY", "data_type": "varchar", "max_length": 50}
                ],
                "primary_key": ["CUSTOMER_KEY"]
            }
        ]
    }
    
    # Test SQL generation
    test_queries = [
        "Show me all customers",
        "Find customers with high risk rating",
        "List customers by country"
    ]
    
    for query in test_queries:
        print(f"\\n🔍 Testing: {query}")
        result = generator.generate_sql_with_validation(query, sample_schema)
        
        print(f"SQL: {result['sql_query']}")
        print(f"Valid: {'✅' if result['validation']['is_valid'] else '❌'}")
        
        if result['validation']['errors']:
            print(f"Errors: {result['validation']['errors']}")
        if result['validation']['warnings']:
            print(f"Warnings: {result['validation']['warnings']}")
    
    print("\\n🏁 Testing completed!")
    return 0

if __name__ == "__main__":
    exit(main())