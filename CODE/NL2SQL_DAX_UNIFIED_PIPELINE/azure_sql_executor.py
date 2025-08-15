#!/usr/bin/env python3
"""
azure_sql_executor.py - Azure SQL Database Executor
===================================================

This module provides execution capabilities for both SQL and DAX queries
against Azure SQL Database. For DAX queries, it includes a DAX-to-SQL
translation layer to enable DAX-style queries against relational data.

Key Features:
- Direct SQL query execution against Azure SQL Database
- DAX-to-SQL translation for DAX query compatibility
- Secure connection management with encryption
- Consistent result formatting for both query types
- Error handling and debugging support

Author: Unified Pipeline Team
Date: August 2025
"""

import os
import pyodbc
import json
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class AzureSQLExecutor:
    """Executor for SQL and DAX queries against Azure SQL Database"""
    
    def __init__(self):
        """Initialize the Azure SQL executor"""
        self.server = os.getenv("AZURE_SQL_SERVER")
        self.database = os.getenv("AZURE_SQL_DB")
        self.username = os.getenv("AZURE_SQL_USER")
        self.password = os.getenv("AZURE_SQL_PASSWORD")
        self.driver = "{ODBC Driver 18 for SQL Server}"
        
        # Validate required configuration
        if not all([self.server, self.database, self.username, self.password]):
            raise ValueError("Missing required Azure SQL configuration. Check your .env file.")
    
    def get_connection_string(self) -> str:
        """Generate secure connection string for Azure SQL Database"""
        return (
            f"DRIVER={self.driver};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
    
    def test_connection(self) -> bool:
        """Test connection to Azure SQL Database"""
        try:
            with pyodbc.connect(self.get_connection_string()) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            print(f"❌ Connection test failed: {str(e)}")
            return False
    
    def execute_sql(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute a SQL query against Azure SQL Database
        
        Args:
            sql_query: The SQL query to execute
            
        Returns:
            Dictionary containing query results and metadata
        """
        start_time = datetime.now()
        
        try:
            with pyodbc.connect(self.get_connection_string()) as conn:
                cursor = conn.cursor()
                
                # Execute the query
                cursor.execute(sql_query)
                
                # Get column information
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Fetch all results
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                data = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        # Handle different data types
                        if value is None:
                            row_dict[columns[i]] = None
                        elif isinstance(value, (int, float, str, bool)):
                            row_dict[columns[i]] = value
                        else:
                            # Convert other types to string
                            row_dict[columns[i]] = str(value)
                    data.append(row_dict)
                
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                
                return {
                    "success": True,
                    "query": sql_query,
                    "columns": columns,
                    "data": data,
                    "row_count": len(data),
                    "execution_time": execution_time,
                    "timestamp": start_time.isoformat()
                }
                
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return {
                "success": False,
                "query": sql_query,
                "error": str(e),
                "execution_time": execution_time,
                "timestamp": start_time.isoformat()
            }
    
    def execute_dax_as_sql(self, dax_query: str, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a DAX query by translating it to SQL
        
        Args:
            dax_query: The DAX query to execute
            schema_info: Database schema information for translation
            
        Returns:
            Dictionary containing query results and metadata
        """
        try:
            # Translate DAX to SQL
            sql_query = self._translate_dax_to_sql(dax_query, schema_info)
            
            if sql_query:
                # Execute the translated SQL
                result = self.execute_sql(sql_query)
                
                # Add DAX-specific metadata
                result["original_dax"] = dax_query
                result["translated_sql"] = sql_query
                result["query_type"] = "DAX-to-SQL"
                
                return result
            else:
                return {
                    "success": False,
                    "query": dax_query,
                    "error": "Could not translate DAX query to SQL",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "query": dax_query,
                "error": f"DAX execution error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _translate_dax_to_sql(self, dax_query: str, schema_info: Dict[str, Any]) -> Optional[str]:
        """
        Translate a DAX query to equivalent SQL using patterns from main.py
        
        This comprehensive translator handles common DAX patterns and converts them
        to equivalent T-SQL for execution against Azure SQL Database.
        """
        try:
            # Clean and normalize the DAX query
            dax_clean = dax_query.strip()
            
            # Remove any code block markers (from LLM output)
            dax_clean = self._extract_dax_code(dax_clean)
            
            # Replace smart quotes with standard quotes (from main.py pattern)
            dax_clean = self._sanitize_quotes(dax_clean)
            
            # Validate DAX completeness (from main.py validation logic)
            is_valid, validation_msg = self._validate_dax_completeness(dax_clean)
            if not is_valid:
                print(f"❌ DAX validation failed: {validation_msg}")
                return None
            
            # Handle EVALUATE expressions (most DAX queries start with EVALUATE)
            if dax_clean.upper().startswith("EVALUATE"):
                return self._translate_evaluate_expression(dax_clean, schema_info)
            
            # Handle simple table references
            if self._is_simple_table_reference(dax_clean):
                return self._translate_simple_table_reference(dax_clean, schema_info)
            
            # Handle direct SUMMARIZE expressions
            if "SUMMARIZE" in dax_clean.upper():
                return self._translate_summarize_expression(dax_clean, schema_info)
            
            # Handle FILTER expressions
            if "FILTER" in dax_clean.upper():
                return self._translate_filter_expression(dax_clean, schema_info)
            
            # Handle TOPN expressions
            if "TOPN" in dax_clean.upper():
                return self._translate_topn_expression(dax_clean, schema_info)
            
            # If no specific pattern matches, try basic translation
            return self._basic_dax_to_sql_translation(dax_clean, schema_info)
            
        except Exception as e:
            print(f"❌ DAX translation error: {str(e)}")
            return None
    
    def _extract_dax_code(self, dax: str) -> str:
        """Extract DAX code from LLM output, similar to main.py logic"""
        dax_code = dax
        
        # Look for DAX code blocks first
        dax_code_block = re.search(r"```dax\s*([\s\S]+?)```", dax, re.IGNORECASE)
        if not dax_code_block:
            dax_code_block = re.search(r"```([\s\S]+?)```", dax)
        if dax_code_block:
            dax_code = dax_code_block.group(1).strip()
        else:
            # Look for EVALUATE statement (DAX queries always start with EVALUATE)
            evaluate_match = re.search(r'(EVALUATE[\s\S]+)', dax, re.IGNORECASE)
            if evaluate_match:
                dax_code = evaluate_match.group(1).strip()
            else:
                # Try to find any pattern that looks like DAX after explanatory text
                lines = dax.split('\n')
                dax_lines = []
                found_dax = False
                for line in lines:
                    # Skip explanatory lines
                    if any(phrase in line.lower() for phrase in ['here\'s', 'here is', 'following', 'below', 'query', ':']):
                        continue
                    # Look for DAX keywords
                    if any(keyword in line.upper() for keyword in ['EVALUATE', 'SELECTCOLUMNS', 'FILTER', 'ADDCOLUMNS', 'SUMMARIZE']):
                        found_dax = True
                    if found_dax:
                        dax_lines.append(line)
                if dax_lines:
                    dax_code = '\n'.join(dax_lines).strip()
        
        return dax_code
    
    def _sanitize_quotes(self, text: str) -> str:
        """Replace smart quotes with standard quotes, from main.py logic"""
        return text.replace(''', "'").replace(''', "'").replace('"', '"').replace('"', '"')
    
    def _validate_dax_completeness(self, dax_query: str) -> tuple:
        """Validate DAX completeness, from main.py validation logic"""
        if not dax_query.strip():
            return False, "Empty DAX query"
        
        if not dax_query.strip().upper().startswith('EVALUATE'):
            return False, "DAX query must start with EVALUATE"
            
        # Count parentheses to check for basic balance
        open_parens = dax_query.count('(')
        close_parens = dax_query.count(')')
        if open_parens > close_parens:
            return False, f"Unbalanced parentheses: {open_parens} open, {close_parens} close - query may be incomplete"
            
        # Check for incomplete function calls (common LLM truncation issue)
        if dax_query.rstrip().endswith(',') or dax_query.rstrip().endswith('('):
            return False, "Query appears to end mid-function - possibly truncated"
            
        return True, "DAX query appears complete"
    
    def _translate_evaluate_expression(self, dax_query: str, schema_info: Dict[str, Any]) -> str:
        """Translate DAX EVALUATE expressions to SQL with comprehensive pattern support"""
        # Extract the expression after EVALUATE
        evaluate_match = re.search(r'EVALUATE\s+(.+)', dax_query, re.IGNORECASE | re.DOTALL)
        
        if evaluate_match:
            expression = evaluate_match.group(1).strip()
            
            # Handle TOPN within EVALUATE (e.g., EVALUATE TOPN(...))
            if expression.upper().startswith("TOPN"):
                return self._translate_topn_expression(expression, schema_info)
            
            # Handle SUMMARIZE within EVALUATE (e.g., EVALUATE SUMMARIZE(...))
            if expression.upper().startswith("SUMMARIZE"):
                return self._translate_summarize_within_evaluate(expression, schema_info)
            
            # Handle SELECTCOLUMNS within EVALUATE
            if expression.upper().startswith("SELECTCOLUMNS"):
                return self._translate_selectcolumns_expression(expression, schema_info)
            
            # Handle FILTER within EVALUATE
            if expression.upper().startswith("FILTER"):
                return self._translate_filter_expression(expression, schema_info)
            
            # Handle simple table references
            if self._is_table_reference(expression, schema_info):
                table_name = self._extract_table_name(expression, schema_info)
                return f"SELECT * FROM [dbo].[{table_name}]"
            
            # Handle more complex expressions
            return self._translate_complex_expression(expression, schema_info)
        
        return None
    
    def _translate_summarize_within_evaluate(self, expression: str, schema_info: Dict[str, Any]) -> str:
        """Handle SUMMARIZE expressions that appear within EVALUATE"""
        try:
            # Pattern for multi-line SUMMARIZE with detailed column references
            # SUMMARIZE(table, table[col1], table[col2], ...)
            summarize_match = re.search(
                r'SUMMARIZE\s*\(\s*([^,\s]+)\s*,\s*(.*?)\)\s*$', 
                expression, 
                re.IGNORECASE | re.DOTALL
            )
            
            if summarize_match:
                table_ref = summarize_match.group(1).strip()
                columns_part = summarize_match.group(2).strip()
                
                # Extract actual table name (remove any prefixes)
                table_name = self._extract_table_name(table_ref, schema_info)
                
                # Parse column references more intelligently
                columns = self._parse_dax_column_references(columns_part, table_name)
                
                if columns:
                    # Create SQL SELECT with DISTINCT to mimic SUMMARIZE behavior
                    column_list = ', '.join([f"[{col}]" for col in columns])
                    return f"SELECT DISTINCT {column_list} FROM [dbo].[{table_name}] ORDER BY {columns[0]}"
                else:
                    # Fallback to all columns
                    return f"SELECT * FROM [dbo].[{table_name}]"
            
            # Fallback to the original summarize method
            return self._translate_summarize_expression(expression, schema_info)
            
        except Exception as e:
            print(f"❌ SUMMARIZE within EVALUATE translation error: {str(e)}")
            return f"SELECT * FROM [dbo].[{self._extract_table_name(expression, schema_info)}]"
    
    def _parse_dax_column_references(self, columns_text: str, table_name: str) -> list:
        """Parse DAX column references like Table[Column] into clean column names"""
        columns = []
        
        # Split by comma and process each part
        parts = self._split_dax_columns(columns_text)
        
        for part in parts:
            part = part.strip()
            
            # Skip calculated columns (contain quotes and formulas)
            if '"' in part and ('SUM(' in part.upper() or 'COUNT(' in part.upper() or 'AVG(' in part.upper()):
                continue
            
            # Handle Table[Column] format
            if '[' in part and ']' in part:
                # Extract column name from Table[Column] format
                column_match = re.search(r'([^[]*\[)?([^\]]+)\]', part)
                if column_match:
                    column_name = column_match.group(2).strip()
                    # Clean up column name mappings based on actual schema
                    column_name = self._map_dax_column_to_sql(column_name, table_name)
                    if column_name:
                        columns.append(column_name)
        
        return columns
    
    def _map_dax_column_to_sql(self, dax_column: str, table_name: str) -> str:
        """Map DAX column names to actual SQL column names"""
        # Handle common DAX to SQL column name mappings
        mapping = {
            'CustomerKey': 'CUSTOMER_KEY',
            'CustomerID': 'CUSTOMER_ID', 
            'CustomerName': 'CUSTOMER_NAME',
            'CustomerTypeDescription': 'CUSTOMER_TYPE_DESCRIPTION',
            'IndustryDescription': 'INDUSTRY_DESCRIPTION',
            'CountryDescription': 'COUNTRY_DESCRIPTION',
            'StateDescription': 'STATE_DESCRIPTION',
            'City': 'CITY',
            'PostalCode': 'POSTAL_CODE',
            'Risk_Rating_Description': 'RISK_RATING_DESCRIPTION',
            'RelationshipManager': 'RELATIONSHIP_MANAGER'
        }
        
        return mapping.get(dax_column, dax_column)
    
    def _translate_summarize_expression(self, dax_query: str, schema_info: Dict[str, Any]) -> str:
        """Translate DAX SUMMARIZE expressions to SQL GROUP BY"""
        try:
            # More flexible pattern to handle multi-line SUMMARIZE with column references
            # Pattern: SUMMARIZE(table, column1, column2, ...)
            summarize_match = re.search(r'SUMMARIZE\\s*\\(\\s*([^,\\(\\)]+?)\\s*,(.+?)\\)\\s*$', dax_query, re.IGNORECASE | re.DOTALL)
            
            if summarize_match:
                table_ref = summarize_match.group(1).strip()
                columns_part = summarize_match.group(2).strip()
                
                # Extract table name
                table_name = self._extract_table_name(table_ref, schema_info)
                
                # Parse column references (handle Table[Column] format)
                columns = []
                # Split by comma but ignore commas within parentheses or quotes
                column_parts = self._split_dax_columns(columns_part)
                
                for col in column_parts:
                    col = col.strip()
                    # Handle Table[Column] format
                    if '[' in col and ']' in col:
                        # Extract column name from Table[Column] format
                        column_match = re.search(r'\\[([^\\]]+)\\]', col)
                        if column_match:
                            columns.append(f"[{column_match.group(1)}]")
                    elif '"' in col:
                        # Handle calculated columns (ignore for now)
                        continue
                    else:
                        columns.append(col)
                
                if columns:
                    column_list = ', '.join(columns)
                    return f"SELECT DISTINCT {column_list} FROM [dbo].[{table_name}] ORDER BY {columns[0]}"
                else:
                    return f"SELECT * FROM [dbo].[{table_name}]"
            
            # Fallback to basic pattern
            basic_pattern = r'SUMMARIZE\\s*\\(\\s*([^,]+)\\s*,\\s*(.+)\\)'
            match = re.search(basic_pattern, dax_query, re.IGNORECASE)
            
            if match:
                table_ref = match.group(1).strip()
                columns_and_agg = match.group(2).strip()
                
                # Extract table name
                table_name = self._extract_table_name(table_ref, schema_info)
                
                # Parse group by columns and aggregations
                return f"SELECT {columns_and_agg} FROM [dbo].[{table_name}] GROUP BY {columns_and_agg}"
            
            return None
        except Exception as e:
            print(f"❌ SUMMARIZE translation error: {str(e)}")
            return None
    
    def _split_dax_columns(self, columns_text: str) -> list:
        """Split DAX column list by commas, respecting parentheses and quotes"""
        columns = []
        current_col = ""
        paren_count = 0
        in_quotes = False
        quote_char = None
        
        for char in columns_text:
            if char in ['"', "'"] and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char == '(' and not in_quotes:
                paren_count += 1
            elif char == ')' and not in_quotes:
                paren_count -= 1
            elif char == ',' and paren_count == 0 and not in_quotes:
                columns.append(current_col.strip())
                current_col = ""
                continue
            
            current_col += char
        
        if current_col.strip():
            columns.append(current_col.strip())
        
        return columns
    
    def _translate_filter_expression(self, dax_query: str, schema_info: Dict[str, Any]) -> str:
        """Translate DAX FILTER expressions to SQL WHERE clauses"""
        # Pattern: FILTER(table, condition)
        filter_pattern = r'FILTER\\s*\\(\\s*([^,]+)\\s*,\\s*(.+)\\)'
        match = re.search(filter_pattern, dax_query, re.IGNORECASE)
        
        if match:
            table_ref = match.group(1).strip()
            condition = match.group(2).strip()
            
            # Extract table name
            table_name = self._extract_table_name(table_ref, schema_info)
            
            # Convert DAX condition to SQL condition
            sql_condition = self._convert_dax_condition_to_sql(condition)
            
            return f"SELECT * FROM {table_name} WHERE {sql_condition}"
        
        return None
    
    def _translate_simple_table_reference(self, dax_query: str, schema_info: Dict[str, Any]) -> str:
        """Translate simple DAX table reference to SQL SELECT"""
        table_name = self._extract_table_name(dax_query, schema_info)
        return f"SELECT * FROM {table_name}"
    
    def _is_simple_table_reference(self, expression: str) -> bool:
        """Check if expression is a simple table reference"""
        # Remove quotes and whitespace
        clean_expr = expression.strip().strip("'\"")
        
        # Simple heuristic: if it contains no functions or operators, it's likely a table
        return not any(char in clean_expr for char in ['(', ')', '+', '-', '*', '/', '=', '<', '>'])
    
    def _is_table_reference(self, expression: str, schema_info: Dict[str, Any]) -> bool:
        """Check if expression references a known table"""
        table_names = [table["name"] for table in schema_info.get("tables", [])]
        clean_expr = expression.strip().strip("'\"")
        return clean_expr in table_names
    
    def _extract_table_name(self, expression: str, schema_info: Dict[str, Any]) -> str:
        """Extract table name from expression"""
        # Remove quotes and whitespace
        clean_expr = expression.strip().strip("'\"")
        
        # Check if it's a known table
        table_names = [table["name"] for table in schema_info.get("tables", [])]
        if clean_expr in table_names:
            return clean_expr
        
        # Return as-is if not found (might need schema prefix)
        return clean_expr
    
    def _convert_dax_condition_to_sql(self, dax_condition: str) -> str:
        """Convert DAX condition syntax to SQL WHERE clause syntax"""
        sql_condition = dax_condition
        
        # DAX uses && and ||, SQL uses AND and OR
        sql_condition = sql_condition.replace("&&", "AND")
        sql_condition = sql_condition.replace("||", "OR")
        
        # DAX column references might use [Table][Column], convert to Table.Column
        sql_condition = re.sub(r'\\[([^\\]]+)\\]\\[([^\\]]+)\\]', r'\\1.\\2', sql_condition)
        
        return sql_condition
    
    def _translate_complex_expression(self, expression: str, schema_info: Dict[str, Any]) -> str:
        """Handle complex DAX expressions"""
        # This is a placeholder for more sophisticated DAX-to-SQL translation
        # In a production system, you'd use a proper DAX parser
        
        # For now, try basic patterns
        if "TOPN" in expression.upper():
            return self._translate_topn_expression(expression, schema_info)
        
        # Default: treat as table reference
        table_name = self._extract_table_name(expression, schema_info)
        return f"SELECT * FROM {table_name}"
    
    def _translate_topn_expression(self, expression: str, schema_info: Dict[str, Any]) -> str:
        """Translate DAX TOPN to SQL TOP"""
        # Pattern: TOPN(n, table, orderby)
        topn_pattern = r'TOPN\\s*\\(\\s*(\\d+)\\s*,\\s*([^,]+)(?:,\\s*(.+))?\\)'
        match = re.search(topn_pattern, expression, re.IGNORECASE)
        
        if match:
            n = match.group(1)
            table_ref = match.group(2).strip()
            order_by = match.group(3).strip() if match.group(3) else ""
            
            table_name = self._extract_table_name(table_ref, schema_info)
            
            sql = f"SELECT TOP {n} * FROM {table_name}"
            if order_by:
                sql += f" ORDER BY {order_by}"
            
            return sql
        
        return None
    
    def _basic_dax_to_sql_translation(self, dax_query: str, schema_info: Dict[str, Any]) -> str:
        """Basic fallback DAX-to-SQL translation"""
        # This is a very basic translator for demonstration
        # In production, you'd use a proper DAX parser and AST translator
        
        # Try to identify table references and convert to SELECT statements
        table_names = [table["name"] for table in schema_info.get("tables", [])]
        
        for table_name in table_names:
            if table_name in dax_query:
                return f"SELECT * FROM {table_name}"
        
        # If no table found, return a generic error query
        return "SELECT 'DAX query could not be translated' as error_message"

def main():
    """Test the Azure SQL executor"""
    print("🧪 Testing Azure SQL Executor")
    print("=" * 40)
    
    executor = AzureSQLExecutor()
    
    # Test connection
    print("🔌 Testing connection...")
    if executor.test_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed!")
        return 1
    
    # Test SQL query
    print("\\n🗄️  Testing SQL query...")
    sql_result = executor.execute_sql("SELECT TOP 5 * FROM FIS_CUSTOMER_DIMENSION")
    
    if sql_result["success"]:
        print(f"✅ SQL query successful! Returned {sql_result['row_count']} rows")
    else:
        print(f"❌ SQL query failed: {sql_result['error']}")
    
    # Test DAX translation
    print("\\n⚡ Testing DAX translation...")
    schema_info = {"tables": [{"name": "FIS_CUSTOMER_DIMENSION"}]}
    dax_result = executor.execute_dax_as_sql("EVALUATE FIS_CUSTOMER_DIMENSION", schema_info)
    
    if dax_result["success"]:
        print(f"✅ DAX translation successful! Returned {dax_result['row_count']} rows")
    else:
        print(f"❌ DAX translation failed: {dax_result['error']}")
    
    print("\\n🏁 Testing completed!")
    return 0

if __name__ == "__main__":
    exit(main())