#!/usr/bin/env python3
"""
dax_generator.py - Natural Language to DAX Query Generator
==========================================================

This module converts natural language queries to DAX queries that can
be translated to SQL for execution against Azure SQL Database.

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

class DAXGenerator:
    """Generate DAX queries from natural language using Azure OpenAI"""
    
    def __init__(self):
        """Initialize the DAX generator"""
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        # Validate configuration
        if not all([os.getenv("AZURE_OPENAI_API_KEY"), os.getenv("AZURE_OPENAI_ENDPOINT"), self.deployment_name]):
            raise ValueError("Missing Azure OpenAI configuration. Check your .env file.")
    
    def generate_dax(self, natural_language_query: str, schema_info: Dict[str, Any]) -> str:
        """
        Generate DAX query from natural language
        
        Args:
            natural_language_query: The natural language query
            schema_info: Database schema information
            
        Returns:
            Generated DAX query string
        """
        try:
            # Create schema context for the prompt
            schema_context = self._create_dax_schema_context(schema_info)
            
            # Create the prompt
            prompt = self._create_dax_generation_prompt(natural_language_query, schema_context)
            
            # Generate DAX using Azure OpenAI (o4-mini reasoning model)
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Power BI DAX developer. Generate accurate DAX queries based on the provided table schema and natural language requests. Focus on queries that can be translated to SQL."
                    },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_completion_tokens=2000,  # Increased for o4-mini reasoning model
            reasoning_effort="medium"
        )            # Extract DAX from response
            dax_query = response.choices[0].message.content.strip()
            
            # Clean up the DAX
            dax_query = self._clean_dax_query(dax_query)
            
            return dax_query
            
        except Exception as e:
            print(f"❌ DAX generation failed: {str(e)}")
            return f"// DAX generation failed: {str(e)}"
    
    def _create_dax_schema_context(self, schema_info: Dict[str, Any]) -> str:
        """Create schema context for DAX prompt"""
        context_parts = []
        
        # Add database information
        context_parts.append(f"Data Model: {schema_info.get('database', 'Unknown')}")
        context_parts.append("")
        
        # Add table information
        context_parts.append("Available Tables:")
        for table in schema_info.get("tables", []):
            table_name = table.get("name", "Unknown")
            context_parts.append(f"\\n{table_name}:")
            
            # Add column information
            for column in table.get("columns", []):
                col_info = f"  - {column['name']}"
                
                # Map SQL data types to DAX-friendly descriptions
                dax_type = self._map_sql_to_dax_type(column['data_type'])
                col_info += f" ({dax_type})"
                
                context_parts.append(col_info)
            
            # Add primary key information
            if table.get("primary_key"):
                pk_cols = ", ".join(table["primary_key"])
                context_parts.append(f"  Key Column(s): {pk_cols}")
            
            # Add sample data if available
            if table.get("sample_data"):
                context_parts.append("  Sample values:")
                for i, sample in enumerate(table["sample_data"][:2], 1):
                    sample_str = ", ".join([f"{k}={v}" for k, v in sample.items()])
                    context_parts.append(f"    {i}. {sample_str}")
            
            context_parts.append("")
        
        # Add relationship information
        if schema_info.get("relationships"):
            context_parts.append("Table Relationships:")
            for rel in schema_info["relationships"]:
                rel_info = f"  {rel['from_table']}[{rel['from_column']}] -> {rel['to_table']}[{rel['to_column']}]"
                context_parts.append(rel_info)
            context_parts.append("")
        
        return "\\n".join(context_parts)
    
    def _map_sql_to_dax_type(self, sql_type: str) -> str:
        """Map SQL data types to DAX-friendly type descriptions"""
        sql_type_lower = sql_type.lower()
        
        type_mapping = {
            'int': 'Integer',
            'bigint': 'Integer',
            'smallint': 'Integer',
            'tinyint': 'Integer',
            'decimal': 'Decimal',
            'numeric': 'Decimal',
            'float': 'Decimal',
            'real': 'Decimal',
            'money': 'Currency',
            'smallmoney': 'Currency',
            'varchar': 'Text',
            'nvarchar': 'Text',
            'char': 'Text',
            'nchar': 'Text',
            'text': 'Text',
            'ntext': 'Text',
            'date': 'Date',
            'datetime': 'DateTime',
            'datetime2': 'DateTime',
            'smalldatetime': 'DateTime',
            'time': 'Time',
            'bit': 'Boolean'
        }
        
        return type_mapping.get(sql_type_lower, 'Text')
    
    def _create_dax_generation_prompt(self, natural_language_query: str, schema_context: str) -> str:
        """Create the prompt for DAX generation"""
        prompt = f"""
Given the following data model schema and natural language query, generate an accurate DAX query.

{schema_context}

Natural Language Query: "{natural_language_query}"

Requirements:
1. Generate valid DAX syntax that can be translated to SQL
2. Use table names and column names from the schema above
3. Use proper DAX functions like EVALUATE, FILTER, SUMMARIZE, TOPN, etc.
4. Reference columns using TableName[ColumnName] syntax
5. Use appropriate aggregation functions (SUM, COUNT, AVERAGE, etc.)
6. Keep queries simple and translatable to SQL
7. Return only the DAX query without explanations
8. Start with EVALUATE for table expressions
9. Use FILTER for WHERE conditions
10. Use SUMMARIZE for GROUP BY operations

Focus on generating queries that can be easily converted to SQL equivalents.

DAX Query:
"""
        return prompt
    
    def _clean_dax_query(self, dax_query: str) -> str:
        """Clean and validate the generated DAX query"""
        # Remove common markdown artifacts
        dax_query = dax_query.replace("```dax", "").replace("```", "")
        
        # Remove leading/trailing whitespace
        dax_query = dax_query.strip()
        
        # Remove any explanatory text before/after the DAX
        lines = dax_query.split("\\n")
        dax_lines = []
        in_dax = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines at the beginning
            if not line and not in_dax:
                continue
            
            # Start collecting DAX when we see DAX keywords
            if any(line.upper().startswith(keyword) for keyword in ['EVALUATE', 'DEFINE', 'MEASURE', 'VAR']):
                in_dax = True
            
            if in_dax:
                dax_lines.append(line)
        
        # Join the DAX lines
        cleaned_dax = "\\n".join(dax_lines)
        
        return cleaned_dax
    
    def validate_dax_syntax(self, dax_query: str) -> Dict[str, Any]:
        """Basic DAX syntax validation"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Basic checks
        if not dax_query.strip():
            validation_result["is_valid"] = False
            validation_result["errors"].append("Empty DAX query")
            return validation_result
        
        # Check for required DAX keywords
        dax_upper = dax_query.upper()
        if not any(keyword in dax_upper for keyword in ['EVALUATE', 'DEFINE', 'MEASURE']):
            validation_result["warnings"].append("No EVALUATE statement found - may not be a complete DAX query")
        
        # Check for proper column references
        if '[' in dax_query and ']' in dax_query:
            if dax_query.count('[') != dax_query.count(']'):
                validation_result["warnings"].append("Unbalanced square brackets detected")
        
        # Check for balanced parentheses
        if dax_query.count('(') != dax_query.count(')'):
            validation_result["warnings"].append("Unbalanced parentheses detected")
        
        # Check for common DAX functions
        dax_functions = ['SUM', 'COUNT', 'AVERAGE', 'MAX', 'MIN', 'FILTER', 'SUMMARIZE', 'TOPN']
        if not any(func in dax_upper for func in dax_functions):
            validation_result["warnings"].append("No common DAX functions detected")
        
        return validation_result
    
    def generate_dax_with_validation(self, natural_language_query: str, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate DAX with validation"""
        dax_query = self.generate_dax(natural_language_query, schema_info)
        validation = self.validate_dax_syntax(dax_query)
        
        return {
            "dax_query": dax_query,
            "validation": validation,
            "natural_language_query": natural_language_query
        }
    
    def suggest_dax_improvements(self, dax_query: str) -> List[str]:
        """Suggest improvements for DAX query"""
        suggestions = []
        
        dax_upper = dax_query.upper()
        
        # Suggest using EVALUATE
        if 'EVALUATE' not in dax_upper:
            suggestions.append("Consider wrapping table expressions with EVALUATE")
        
        # Suggest using proper column references
        if '[' not in dax_query or ']' not in dax_query:
            suggestions.append("Use TableName[ColumnName] syntax for column references")
        
        # Suggest using FILTER instead of WHERE
        if 'WHERE' in dax_upper and 'FILTER' not in dax_upper:
            suggestions.append("Consider using FILTER function instead of WHERE clause")
        
        # Suggest using SUMMARIZE for grouping
        if any(keyword in dax_upper for keyword in ['GROUP BY', 'GROUPBY']) and 'SUMMARIZE' not in dax_upper:
            suggestions.append("Consider using SUMMARIZE function for grouping operations")
        
        return suggestions

def main():
    """Test the DAX generator"""
    print("🧪 Testing DAX Generator")
    print("=" * 40)
    
    generator = DAXGenerator()
    
    # Sample schema for testing
    sample_schema = {
        "database": "testdb",
        "tables": [
            {
                "name": "FIS_CUSTOMER_DIMENSION",
                "columns": [
                    {"name": "CUSTOMER_KEY", "data_type": "int"},
                    {"name": "CUSTOMER_NAME", "data_type": "varchar"},
                    {"name": "RISK_RATING_CODE", "data_type": "varchar"},
                    {"name": "COUNTRY", "data_type": "varchar"}
                ],
                "primary_key": ["CUSTOMER_KEY"]
            },
            {
                "name": "FIS_CA_DETAIL_FACT",
                "columns": [
                    {"name": "CUSTOMER_KEY", "data_type": "int"},
                    {"name": "LIMIT_AMOUNT", "data_type": "decimal"},
                    {"name": "EXPOSURE_AT_DEFAULT", "data_type": "decimal"}
                ]
            }
        ],
        "relationships": [
            {
                "from_table": "FIS_CA_DETAIL_FACT",
                "from_column": "CUSTOMER_KEY",
                "to_table": "FIS_CUSTOMER_DIMENSION",
                "to_column": "CUSTOMER_KEY"
            }
        ]
    }
    
    # Test DAX generation
    test_queries = [
        "Show me all customers",
        "Find customers with high risk rating",
        "Calculate total exposure by country",
        "List top 10 customers by credit limit"
    ]
    
    for query in test_queries:
        print(f"\\n🔍 Testing: {query}")
        result = generator.generate_dax_with_validation(query, sample_schema)
        
        print(f"DAX: {result['dax_query']}")
        print(f"Valid: {'✅' if result['validation']['is_valid'] else '❌'}")
        
        if result['validation']['errors']:
            print(f"Errors: {result['validation']['errors']}")
        if result['validation']['warnings']:
            print(f"Warnings: {result['validation']['warnings']}")
        
        # Show suggestions
        suggestions = generator.suggest_dax_improvements(result['dax_query'])
        if suggestions:
            print(f"Suggestions: {suggestions}")
    
    print("\\n🏁 Testing completed!")
    return 0

if __name__ == "__main__":
    exit(main())