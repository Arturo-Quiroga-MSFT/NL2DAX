#!/usr/bin/env python3
"""
result_formatter.py - Result Formatting and Comparison
======================================================

This module provides formatting and comparison capabilities for
SQL and DAX query results.

Author: Unified Pipeline Team
Date: August 2025
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class ResultFormatter:
    """Format and compare SQL and DAX query results"""
    
    def __init__(self):
        """Initialize the result formatter"""
        pass
    
    def format_result(self, result: Dict[str, Any], query_type: str = "SQL") -> str:
        """
        Format query result for display
        
        Args:
            result: Query result dictionary
            query_type: Type of query (SQL or DAX)
            
        Returns:
            Formatted string representation of the result
        """
        if not result.get("success", False):
            return f"❌ {query_type} Query Failed: {result.get('error', 'Unknown error')}"
        
        data = result.get("data", [])
        if not data:
            return f"✅ {query_type} Query Successful - No results returned"
        
        # Format as table
        formatted_lines = []
        formatted_lines.append(f"✅ {query_type} Query Results ({len(data)} rows):")
        formatted_lines.append("")
        
        # Get column names
        columns = result.get("columns", [])
        if not columns and data:
            columns = list(data[0].keys())
        
        if columns:
            # Create header
            header = " | ".join(f"{col:15}" for col in columns)
            separator = "-" * len(header)
            
            formatted_lines.append(header)
            formatted_lines.append(separator)
            
            # Add data rows (limit to first 10 for display)
            for i, row in enumerate(data[:10]):
                if isinstance(row, dict):
                    row_values = [str(row.get(col, ""))[:15] for col in columns]
                else:
                    row_values = [str(val)[:15] for val in row]
                
                row_line = " | ".join(f"{val:15}" for val in row_values)
                formatted_lines.append(row_line)
            
            if len(data) > 10:
                formatted_lines.append(f"... and {len(data) - 10} more rows")
        
        # Add execution metadata
        if result.get("execution_time"):
            formatted_lines.append("")
            formatted_lines.append(f"Execution Time: {result['execution_time']:.3f}s")
        
        return "\\n".join(formatted_lines)
    
    def compare_results(self, sql_result: Dict[str, Any], dax_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare SQL and DAX query results
        
        Args:
            sql_result: SQL query result
            dax_result: DAX query result
            
        Returns:
            Comparison analysis
        """
        comparison = {
            "matches": False,
            "row_count_match": False,
            "column_count_match": False,
            "data_match": False,
            "sql_rows": 0,
            "dax_rows": 0,
            "sql_columns": 0,
            "dax_columns": 0,
            "differences": [],
            "summary": ""
        }
        
        # Check if both queries succeeded
        sql_success = sql_result.get("success", False)
        dax_success = dax_result.get("success", False)
        
        if not sql_success or not dax_success:
            comparison["summary"] = "Cannot compare - one or both queries failed"
            if not sql_success:
                comparison["differences"].append(f"SQL query failed: {sql_result.get('error', 'Unknown error')}")
            if not dax_success:
                comparison["differences"].append(f"DAX query failed: {dax_result.get('error', 'Unknown error')}")
            return comparison
        
        # Get data
        sql_data = sql_result.get("data", [])
        dax_data = dax_result.get("data", [])
        
        comparison["sql_rows"] = len(sql_data)
        comparison["dax_rows"] = len(dax_data)
        
        # Compare row counts
        comparison["row_count_match"] = comparison["sql_rows"] == comparison["dax_rows"]
        if not comparison["row_count_match"]:
            comparison["differences"].append(f"Row count differs: SQL={comparison['sql_rows']}, DAX={comparison['dax_rows']}")
        
        # Compare column counts
        sql_columns = sql_result.get("columns", [])
        dax_columns = dax_result.get("columns", [])
        
        if not sql_columns and sql_data:
            sql_columns = list(sql_data[0].keys()) if sql_data else []
        if not dax_columns and dax_data:
            dax_columns = list(dax_data[0].keys()) if dax_data else []
        
        comparison["sql_columns"] = len(sql_columns)
        comparison["dax_columns"] = len(dax_columns)
        comparison["column_count_match"] = comparison["sql_columns"] == comparison["dax_columns"]
        
        if not comparison["column_count_match"]:
            comparison["differences"].append(f"Column count differs: SQL={comparison['sql_columns']}, DAX={comparison['dax_columns']}")
        
        # Compare actual data if both have data
        if sql_data and dax_data:
            data_comparison = self._compare_data_content(sql_data, dax_data, sql_columns, dax_columns)
            comparison["data_match"] = data_comparison["matches"]
            comparison["differences"].extend(data_comparison["differences"])
        elif not sql_data and not dax_data:
            comparison["data_match"] = True  # Both empty
        else:
            comparison["data_match"] = False
            comparison["differences"].append("One result set is empty while the other has data")
        
        # Overall match
        comparison["matches"] = (
            comparison["row_count_match"] and 
            comparison["column_count_match"] and 
            comparison["data_match"]
        )
        
        # Generate summary
        if comparison["matches"]:
            comparison["summary"] = f"✅ Results match perfectly ({comparison['sql_rows']} rows, {comparison['sql_columns']} columns)"
        else:
            diff_count = len(comparison["differences"])
            comparison["summary"] = f"❌ Results differ ({diff_count} differences found)"
        
        return comparison
    
    def _compare_data_content(self, sql_data: List[Dict], dax_data: List[Dict], 
                             sql_columns: List[str], dax_columns: List[str]) -> Dict[str, Any]:
        """Compare the actual data content between SQL and DAX results"""
        result = {
            "matches": True,
            "differences": []
        }
        
        # Compare up to first 100 rows for performance
        max_rows = min(len(sql_data), len(dax_data), 100)
        
        for i in range(max_rows):
            sql_row = sql_data[i] if i < len(sql_data) else {}
            dax_row = dax_data[i] if i < len(dax_data) else {}
            
            # Compare common columns
            common_columns = set(sql_columns) & set(dax_columns)
            
            for col in common_columns:
                sql_val = sql_row.get(col)
                dax_val = dax_row.get(col)
                
                # Normalize values for comparison
                sql_val_norm = self._normalize_value(sql_val)
                dax_val_norm = self._normalize_value(dax_val)
                
                if sql_val_norm != dax_val_norm:
                    result["matches"] = False
                    result["differences"].append(
                        f"Row {i+1}, Column '{col}': SQL='{sql_val}', DAX='{dax_val}'"
                    )
                    
                    # Limit difference reporting
                    if len(result["differences"]) >= 10:
                        result["differences"].append("... (more differences truncated)")
                        return result
        
        return result
    
    def _normalize_value(self, value: Any) -> Any:
        """Normalize a value for comparison"""
        if value is None:
            return None
        
        # Convert to string and strip whitespace
        str_val = str(value).strip()
        
        # Try to convert to number if possible
        try:
            if '.' in str_val:
                return float(str_val)
            else:
                return int(str_val)
        except (ValueError, TypeError):
            return str_val.lower()  # Case-insensitive string comparison
    
    def create_comparison_report(self, comparison: Dict[str, Any], 
                               sql_result: Dict[str, Any], 
                               dax_result: Dict[str, Any]) -> str:
        """Create a detailed comparison report"""
        report_lines = []
        
        report_lines.append("📊 SQL vs DAX Results Comparison Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Summary
        report_lines.append("📋 Summary:")
        report_lines.append(f"   {comparison['summary']}")
        report_lines.append("")
        
        # Metrics
        report_lines.append("📊 Metrics:")
        report_lines.append(f"   SQL Rows: {comparison['sql_rows']}")
        report_lines.append(f"   DAX Rows: {comparison['dax_rows']}")
        report_lines.append(f"   SQL Columns: {comparison['sql_columns']}")
        report_lines.append(f"   DAX Columns: {comparison['dax_columns']}")
        report_lines.append("")
        
        # Performance
        sql_time = sql_result.get("execution_time", 0)
        dax_time = dax_result.get("execution_time", 0)
        report_lines.append("⏱️  Performance:")
        report_lines.append(f"   SQL Execution: {sql_time:.3f}s")
        report_lines.append(f"   DAX Execution: {dax_time:.3f}s")
        if sql_time > 0 and dax_time > 0:
            faster = "SQL" if sql_time < dax_time else "DAX"
            ratio = max(sql_time, dax_time) / min(sql_time, dax_time)
            report_lines.append(f"   Faster: {faster} ({ratio:.2f}x)")
        report_lines.append("")
        
        # Differences
        if comparison["differences"]:
            report_lines.append("❌ Differences Found:")
            for i, diff in enumerate(comparison["differences"][:20], 1):
                report_lines.append(f"   {i}. {diff}")
            if len(comparison["differences"]) > 20:
                report_lines.append(f"   ... and {len(comparison['differences']) - 20} more differences")
        else:
            report_lines.append("✅ No differences found - results match perfectly!")
        
        return "\\n".join(report_lines)

def main():
    """Test the result formatter"""
    print("🧪 Testing Result Formatter")
    print("=" * 40)
    
    formatter = ResultFormatter()
    
    # Sample results for testing
    sql_result = {
        "success": True,
        "columns": ["ID", "Name", "Value"],
        "data": [
            {"ID": 1, "Name": "Alice", "Value": 100},
            {"ID": 2, "Name": "Bob", "Value": 200},
            {"ID": 3, "Name": "Charlie", "Value": 300}
        ],
        "execution_time": 0.025
    }
    
    dax_result = {
        "success": True,
        "columns": ["ID", "Name", "Value"],
        "data": [
            {"ID": 1, "Name": "Alice", "Value": 100},
            {"ID": 2, "Name": "Bob", "Value": 200},
            {"ID": 3, "Name": "Charlie", "Value": 300}
        ],
        "execution_time": 0.045
    }
    
    # Test formatting
    print("📊 SQL Result:")
    print(formatter.format_result(sql_result, "SQL"))
    
    print("\\n📊 DAX Result:")
    print(formatter.format_result(dax_result, "DAX"))
    
    # Test comparison
    print("\\n🔄 Comparison:")
    comparison = formatter.compare_results(sql_result, dax_result)
    print(f"Match: {'✅' if comparison['matches'] else '❌'}")
    print(f"Summary: {comparison['summary']}")
    
    # Test comparison report
    print("\\n📋 Detailed Report:")
    report = formatter.create_comparison_report(comparison, sql_result, dax_result)
    print(report)
    
    print("\\n🏁 Testing completed!")
    return 0

if __name__ == "__main__":
    exit(main())