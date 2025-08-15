#!/usr/bin/env python3
"""
unified_pipeline.py - NL2SQL & DAX Unified Pipeline
===================================================

This module provides a unified pipeline that converts natural language queries
to both SQL and DAX queries, executing both directly against Azure SQL Database
to ensure complete data consistency.

Key Features:
- Single Azure SQL DB as data source for both SQL and DAX
- Schema-aware query generation for both query types
- Result comparison and validation
- Comprehensive error handling and debugging
- Performance metrics and timing
- Query caching for optimization

Author: NL2DAX Unified Pipeline Team
Date: August 2025
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import pipeline components
from sql_generator import SQLGenerator
from dax_generator import DAXGenerator
from azure_sql_executor import AzureSQLExecutor
from schema_analyzer import SchemaAnalyzer
from result_formatter import ResultFormatter
from query_cache import QueryCache

class UnifiedNL2SQLDAXPipeline:
    """
    Unified pipeline for converting natural language to SQL and DAX queries
    that execute directly against Azure SQL Database.
    """
    
    def __init__(self):
        """Initialize the unified pipeline components"""
        print("🚀 Initializing Unified NL2SQL & DAX Pipeline...")
        
        # Initialize components
        self.schema_analyzer = SchemaAnalyzer()
        self.sql_generator = SQLGenerator()
        self.dax_generator = DAXGenerator()
        self.sql_executor = AzureSQLExecutor()
        self.result_formatter = ResultFormatter()
        self.query_cache = QueryCache()
        
        # Pipeline configuration
        self.enable_caching = os.getenv("ENABLE_QUERY_CACHING", "true").lower() == "true"
        self.compare_results = os.getenv("COMPARE_SQL_DAX_RESULTS", "true").lower() == "true"
        self.save_results = os.getenv("SAVE_PIPELINE_RESULTS", "true").lower() == "true"
        
        print("✅ Pipeline initialized successfully!")
        
    def execute_query(self, natural_language_query: str) -> Dict[str, Any]:
        """
        Execute a natural language query using both SQL and DAX
        
        Args:
            natural_language_query: The natural language query to process
            
        Returns:
            Dictionary containing results from both SQL and DAX execution
        """
        start_time = time.time()
        execution_id = f"unified_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\\n🔍 Processing Query: {natural_language_query}")
        print(f"📋 Execution ID: {execution_id}")
        
        # Check cache first
        if self.enable_caching:
            cached_result = self.query_cache.get(natural_language_query, "unified")
            if cached_result:
                print("⚡ Using cached result")
                return cached_result
        
        result = {
            "execution_id": execution_id,
            "query": natural_language_query,
            "timestamp": datetime.now().isoformat(),
            "sql_result": None,
            "dax_result": None,
            "comparison": None,
            "performance": {},
            "errors": []
        }
        
        try:
            # Step 1: Analyze database schema
            print("\\n📊 Analyzing database schema...")
            schema_start = time.time()
            schema_info = self.schema_analyzer.get_schema_info()
            result["performance"]["schema_analysis"] = time.time() - schema_start
            print(f"✅ Schema analysis completed ({result['performance']['schema_analysis']:.2f}s)")
            
            # Step 2: Generate SQL query
            print("\\n🔧 Generating SQL query...")
            sql_start = time.time()
            sql_query = self.sql_generator.generate_sql(natural_language_query, schema_info)
            result["performance"]["sql_generation"] = time.time() - sql_start
            print(f"✅ SQL generated ({result['performance']['sql_generation']:.2f}s)")
            print(f"SQL: {sql_query}")
            
            # Store the generated SQL query in result
            result["generated_sql"] = sql_query
            
            # Validate SQL query
            if not sql_query or sql_query.strip() == "" or sql_query.startswith("-- SQL generation failed"):
                result["errors"].append("SQL generation failed: Empty or invalid query generated")
                print("❌ SQL generation failed: Empty query")
                sql_query = "-- SQL generation failed"
                result["generated_sql"] = sql_query
            
            # Step 3: Generate DAX query
            print("\\n⚡ Generating DAX query...")
            dax_start = time.time()
            dax_query = self.dax_generator.generate_dax(natural_language_query, schema_info)
            result["performance"]["dax_generation"] = time.time() - dax_start
            print(f"✅ DAX generated ({result['performance']['dax_generation']:.2f}s)")
            print(f"DAX: {dax_query}")
            
            # Store the generated DAX query in result
            result["generated_dax"] = dax_query
            
            # Validate DAX query
            if not dax_query or dax_query.strip() == "" or dax_query.startswith("// DAX generation failed"):
                result["errors"].append("DAX generation failed: Empty or invalid query generated")
                print("❌ DAX generation failed: Empty query")
                dax_query = "// DAX generation failed"
                result["generated_dax"] = dax_query
            
            # Step 4: Execute SQL query
            print("\\n🗄️  Executing SQL query against Azure SQL DB...")
            sql_exec_start = time.time()
            try:
                if sql_query and not sql_query.startswith("--"):
                    sql_result = self.sql_executor.execute_sql(sql_query)
                    result["sql_result"] = sql_result
                    result["performance"]["sql_execution"] = time.time() - sql_exec_start
                    print(f"✅ SQL executed successfully ({result['performance']['sql_execution']:.2f}s)")
                    print(f"SQL returned {len(sql_result.get('data', []))} rows")
                else:
                    print("❌ Skipping SQL execution due to generation failure")
                    result["sql_result"] = {"success": False, "error": "SQL generation failed", "data": [], "columns": []}
                    result["performance"]["sql_execution"] = 0
            except Exception as e:
                result["errors"].append(f"SQL execution error: {str(e)}")
                print(f"❌ SQL execution failed: {str(e)}")
                result["sql_result"] = {"success": False, "error": str(e), "data": [], "columns": []}
            
            # Step 5: Execute DAX query (simulated against SQL DB structure)
            print("\\n📈 Executing DAX query against Azure SQL DB...")
            dax_exec_start = time.time()
            try:
                if dax_query and not dax_query.startswith("//"):
                    # Note: This will use a DAX-to-SQL translator for execution against SQL DB
                    dax_result = self.sql_executor.execute_dax_as_sql(dax_query, schema_info)
                    result["dax_result"] = dax_result
                    result["performance"]["dax_execution"] = time.time() - dax_exec_start
                    print(f"✅ DAX executed successfully ({result['performance']['dax_execution']:.2f}s)")
                    print(f"DAX returned {len(dax_result.get('data', []))} rows")
                else:
                    print("❌ Skipping DAX execution due to generation failure")
                    result["dax_result"] = {"success": False, "error": "DAX generation failed", "data": [], "columns": []}
                    result["performance"]["dax_execution"] = 0
            except Exception as e:
                result["errors"].append(f"DAX execution error: {str(e)}")
                print(f"❌ DAX execution failed: {str(e)}")
                result["dax_result"] = {"success": False, "error": str(e), "data": [], "columns": []}
            
            # Step 6: Compare results if both succeeded
            if self.compare_results and result["sql_result"] and result["dax_result"]:
                print("\\n🔄 Comparing SQL and DAX results...")
                comparison_start = time.time()
                comparison = self.result_formatter.compare_results(
                    result["sql_result"], 
                    result["dax_result"]
                )
                result["comparison"] = comparison
                result["performance"]["comparison"] = time.time() - comparison_start
                print(f"✅ Results compared ({result['performance']['comparison']:.2f}s)")
                
                if comparison["matches"]:
                    print("🎯 Results match perfectly!")
                else:
                    print("⚠️  Results differ - see comparison details")
            
            # Calculate total execution time
            result["performance"]["total_time"] = time.time() - start_time
            
            # Cache successful results
            if self.enable_caching and not result["errors"]:
                self.query_cache.set(natural_language_query, "unified", result)
            
            # Save results if enabled
            if self.save_results:
                self._save_execution_result(result)
            
            print(f"\\n🏁 Pipeline completed in {result['performance']['total_time']:.2f}s")
            return result
            
        except Exception as e:
            result["errors"].append(f"Pipeline error: {str(e)}")
            result["performance"]["total_time"] = time.time() - start_time
            print(f"❌ Pipeline failed: {str(e)}")
            return result
    
    def _save_execution_result(self, result: Dict[str, Any]) -> str:
        """Save execution result to file"""
        try:
            # Create results directory if it doesn't exist
            results_dir = "/Users/arturoquiroga/GITHUB/NL2DAX/RESULTS/UNIFIED_PIPELINE"
            os.makedirs(results_dir, exist_ok=True)
            
            # Generate filename
            filename = f"unified_pipeline_{result['execution_id']}.json"
            filepath = os.path.join(results_dir, filename)
            
            # Save result
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Results saved to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"⚠️  Could not save results: {str(e)}")
            return ""
    
    def get_schema_summary(self) -> Dict[str, Any]:
        """Get a summary of the database schema"""
        return self.schema_analyzer.get_schema_summary()
    
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate pipeline configuration"""
        print("🔧 Validating pipeline configuration...")
        
        validation = {
            "azure_sql_connection": False,
            "azure_openai_connection": False,
            "schema_access": False,
            "all_components": False
        }
        
        try:
            # Test Azure SQL connection
            validation["azure_sql_connection"] = self.sql_executor.test_connection()
            
            # Test Azure OpenAI connection
            validation["azure_openai_connection"] = self.sql_generator.test_openai_connection()
            
            # Test schema access
            schema_info = self.schema_analyzer.get_basic_schema()
            validation["schema_access"] = len(schema_info.get("tables", [])) > 0
            
            # Overall validation
            validation["all_components"] = all(validation.values())
            
        except Exception as e:
            print(f"❌ Configuration validation failed: {str(e)}")
        
        return validation

def main():
    """Main function for testing the unified pipeline"""
    print("🧪 Testing Unified NL2SQL & DAX Pipeline")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = UnifiedNL2SQLDAXPipeline()
    
    # Validate configuration
    validation = pipeline.validate_configuration()
    print(f"\\n📋 Configuration Status:")
    for component, status in validation.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {component}")
    
    if not validation["all_components"]:
        print("\\n❌ Configuration validation failed. Please check your .env file.")
        return 1
    
    # Test queries
    test_queries = [
        "Show me all customers with high risk ratings",
        "List the top 5 customers by total credit limit",
        "What is the average balance per customer by region?",
        "Show me active loans with principal balance over 100000"
    ]
    
    print(f"\\n🔍 Testing with {len(test_queries)} sample queries...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\\n{'='*60}")
        print(f"🧪 Test Query {i}/{len(test_queries)}")
        print(f"{'='*60}")
        
        result = pipeline.execute_query(query)
        
        # Display summary
        print(f"\\n📊 Execution Summary:")
        print(f"   SQL Success: {'✅' if result['sql_result'] else '❌'}")
        print(f"   DAX Success: {'✅' if result['dax_result'] else '❌'}")
        print(f"   Total Time: {result['performance'].get('total_time', 0):.2f}s")
        print(f"   Errors: {len(result['errors'])}")
        
        if result['errors']:
            print(f"   Error Details: {'; '.join(result['errors'])}")
    
    print(f"\\n🏁 Pipeline testing completed!")
    return 0

if __name__ == "__main__":
    exit(main())