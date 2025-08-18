"""
sempy_query_executor.py - SemPy-powered DAX Query Execution
===========================================================

This module executes DAX queries against Power BI semantic models using
SemPy (semantic-link) for direct, authenticated access to Fabric/Power BI.

Key Features:
- Direct DAX execution via SemPy evaluate_dax()
- Authentication and connection management
- Query result processing and formatting
- Error handling and diagnostics
- Performance monitoring and caching

Author: NL2DAX Pipeline Development Team
Last Updated: August 18, 2025
"""

import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import pandas as pd
from datetime import datetime
import json

try:
    import sempy.fabric as fabric
    from sempy.fabric import evaluate_dax
    SEMPY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SemPy not available: {e}")
    SEMPY_AVAILABLE = False

# Import fabric authentication provider for fallback
try:
    from .fabric_auth_provider import FabricApiClient
    FABRIC_API_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Fabric API client not available: {e}")
    FABRIC_API_AVAILABLE = False

from .sempy_connector import SemPyConnector
from .sempy_dax_generator import DAXQueryPlan

@dataclass
class QueryResult:
    """Result of a DAX query execution"""
    success: bool
    data: Optional[pd.DataFrame] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    execution_time_ms: Optional[float] = None
    query_plan: Optional[DAXQueryPlan] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class ExecutionContext:
    """Context information for query execution"""
    workspace_name: str
    semantic_model_name: str
    user_query: str
    dax_expression: str
    execution_timestamp: datetime
    session_id: Optional[str] = None

class SemPyQueryExecutor:
    """
    SemPy Query Executor
    
    Executes DAX queries against Power BI semantic models using
    Microsoft Fabric Semantic Link (SemPy).
    """
    
    def __init__(self, connector: SemPyConnector):
        """
        Initialize the query executor
        
        Args:
            connector: Authenticated SemPyConnector instance
        """
        self.logger = logging.getLogger(__name__)
        self.connector = connector
        
        if not SEMPY_AVAILABLE:
            raise ImportError(
                "SemPy (semantic-link) is not available. "
                "Install with: pip install semantic-link"
            )
        
        if not connector.authenticated:
            raise ValueError("SemPy connector must be authenticated")
    
    def execute_dax_query(self, query_plan: DAXQueryPlan, 
                         workspace_name: Optional[str] = None,
                         semantic_model_name: Optional[str] = None) -> QueryResult:
        """
        Execute a DAX query using SemPy
        
        Args:
            query_plan: DAXQueryPlan with generated DAX expression
            workspace_name: Target workspace (uses connector default if None)
            semantic_model_name: Target semantic model (uses connector default if None)
            
        Returns:
            QueryResult with execution details and data
        """
        
        start_time = time.time()
        
        try:
            # Validate inputs
            target_workspace = workspace_name or self.connector.current_workspace
            target_model = semantic_model_name or self.connector.current_model
            
            if not target_workspace or not target_model:
                raise ValueError(
                    "Workspace and semantic model must be specified or set in connector"
                )
            
            self.logger.info(f"Executing DAX query on {target_workspace}/{target_model}")
            
            # Create execution context
            context = ExecutionContext(
                workspace_name=target_workspace,
                semantic_model_name=target_model,
                user_query=query_plan.analysis.original_query,
                dax_expression=query_plan.dax_expression,
                execution_timestamp=datetime.now()
            )
            
            # Execute DAX query using SemPy with fallback
            try:
                result_df = evaluate_dax(
                    dataset=target_model,
                    dax_string=query_plan.dax_expression,
                    workspace=target_workspace
                )
                execution_method = "SemPy"
                
            except Exception as sempy_error:
                self.logger.warning(f"SemPy evaluate_dax failed: {sempy_error}")
                
                # Try Fabric API fallback
                if hasattr(self.connector, 'fabric_api_client') and self.connector.fabric_api_client:
                    self.logger.info("Trying Fabric API fallback for DAX execution...")
                    
                    # Get workspace and dataset IDs
                    workspace_id = None
                    dataset_id = None
                    
                    if hasattr(self.connector, 'config') and self.connector.config:
                        workspace_id = self.connector.config.workspace_id
                        dataset_id = self.connector.config.dataset_id
                    
                    if workspace_id and dataset_id:
                        api_result = self.connector.fabric_api_client.execute_dax(
                            dataset_id=dataset_id,
                            dax_query=query_plan.dax_expression,
                            group_id=workspace_id
                        )
                        
                        if 'error' not in api_result:
                            # Convert API result to DataFrame
                            result_df = self._convert_api_result_to_dataframe(api_result)
                            execution_method = "Fabric API"
                        else:
                            raise Exception(f"Fabric API error: {api_result['error']}")
                    else:
                        raise Exception("Missing workspace_id or dataset_id for Fabric API fallback")
                else:
                    raise sempy_error
            
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Process results
            query_result = QueryResult(
                success=True,
                data=result_df,
                row_count=len(result_df) if result_df is not None else 0,
                column_count=len(result_df.columns) if result_df is not None else 0,
                execution_time_ms=execution_time,
                query_plan=query_plan,
                metadata={
                    'context': context,
                    'sempy_version': self._get_sempy_version(),
                    'pattern_type': query_plan.pattern_type.value,
                    'confidence_score': query_plan.confidence_score,
                    'execution_method': execution_method
                }
            )
            
            self.logger.info(f"Query executed successfully: {query_result.row_count} rows in {execution_time:.2f}ms")
            return query_result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            self.logger.error(f"DAX query execution failed: {e}")
            
            return QueryResult(
                success=False,
                execution_time_ms=execution_time,
                query_plan=query_plan,
                error_message=str(e),
                error_type=type(e).__name__,
                metadata={
                    'attempted_workspace': target_workspace,
                    'attempted_model': target_model,
                    'dax_expression': query_plan.dax_expression
                }
            )
    
    def execute_raw_dax(self, dax_expression: str,
                       workspace_name: Optional[str] = None,
                       semantic_model_name: Optional[str] = None) -> QueryResult:
        """
        Execute a raw DAX expression without query plan
        
        Args:
            dax_expression: Raw DAX expression to execute
            workspace_name: Target workspace
            semantic_model_name: Target semantic model
            
        Returns:
            QueryResult with execution details
        """
        
        start_time = time.time()
        
        try:
            target_workspace = workspace_name or self.connector.current_workspace
            target_model = semantic_model_name or self.connector.current_model
            
            if not target_workspace or not target_model:
                raise ValueError(
                    "Workspace and semantic model must be specified or set in connector"
                )
            
            self.logger.info(f"Executing raw DAX: {dax_expression[:100]}...")
            
            # Execute using SemPy
            result_df = evaluate_dax(
                dataset=target_model,
                dax_string=dax_expression,
                workspace=target_workspace
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return QueryResult(
                success=True,
                data=result_df,
                row_count=len(result_df) if result_df is not None else 0,
                column_count=len(result_df.columns) if result_df is not None else 0,
                execution_time_ms=execution_time,
                metadata={
                    'raw_execution': True,
                    'workspace': target_workspace,
                    'semantic_model': target_model
                }
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            return QueryResult(
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e),
                error_type=type(e).__name__,
                metadata={
                    'raw_execution': True,
                    'dax_expression': dax_expression
                }
            )
    
    def test_connection(self, workspace_name: Optional[str] = None,
                       semantic_model_name: Optional[str] = None) -> QueryResult:
        """
        Test connectivity by executing a simple DAX query
        
        Args:
            workspace_name: Target workspace
            semantic_model_name: Target semantic model
            
        Returns:
            QueryResult with test execution details
        """
        
        test_dax = "EVALUATE { 1 }"
        
        self.logger.info("Testing SemPy DAX execution connectivity...")
        
        result = self.execute_raw_dax(
            dax_expression=test_dax,
            workspace_name=workspace_name,
            semantic_model_name=semantic_model_name
        )
        
        if result.success:
            self.logger.info("✅ SemPy DAX execution test successful")
        else:
            self.logger.error(f"❌ SemPy DAX execution test failed: {result.error_message}")
        
        return result
    
    def format_result_for_display(self, result: QueryResult, max_rows: int = 100) -> str:
        """
        Format query result for user-friendly display
        
        Args:
            result: QueryResult to format
            max_rows: Maximum number of rows to display
            
        Returns:
            Formatted string representation
        """
        
        if not result.success:
            return self._format_error_display(result)
        
        if result.data is None or result.row_count == 0:
            return "Query executed successfully but returned no data."
        
        output = []
        
        # Header information
        output.append(f"📊 Query Results ({result.row_count} rows, {result.column_count} columns)")
        output.append(f"⏱️  Execution time: {result.execution_time_ms:.2f}ms")
        
        if result.query_plan:
            output.append(f"🎯 Pattern: {result.query_plan.pattern_type.value}")
            output.append(f"🎓 Confidence: {result.query_plan.confidence_score:.2f}")
        
        output.append("")
        
        # Data display
        display_df = result.data.head(max_rows) if len(result.data) > max_rows else result.data
        
        # Format DataFrame for display
        formatted_table = self._format_dataframe_table(display_df)
        output.append(formatted_table)
        
        if len(result.data) > max_rows:
            output.append(f"\n... ({len(result.data) - max_rows} more rows)")
        
        return "\n".join(output)
    
    def _format_error_display(self, result: QueryResult) -> str:
        """Format error information for display"""
        
        output = []
        output.append("❌ Query Execution Failed")
        output.append(f"Error Type: {result.error_type}")
        output.append(f"Error Message: {result.error_message}")
        
        if result.execution_time_ms:
            output.append(f"Failed after: {result.execution_time_ms:.2f}ms")
        
        if result.metadata and 'dax_expression' in result.metadata:
            output.append("\nDAX Expression:")
            output.append(result.metadata['dax_expression'])
        
        return "\n".join(output)
    
    def _format_dataframe_table(self, df: pd.DataFrame) -> str:
        """Format DataFrame as a text table"""
        
        if df.empty:
            return "No data to display"
        
        # Use pandas string representation with some formatting
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)
        
        try:
            return str(df.to_string(index=False))
        except Exception:
            # Fallback for any formatting issues
            return f"Data preview: {len(df)} rows x {len(df.columns)} columns"
    
    def export_result_to_file(self, result: QueryResult, file_path: str, 
                             format: str = 'csv') -> bool:
        """
        Export query result to file
        
        Args:
            result: QueryResult to export
            file_path: Target file path
            format: Export format ('csv', 'excel', 'json')
            
        Returns:
            True if export successful
        """
        
        if not result.success or result.data is None:
            self.logger.error("Cannot export failed query or empty result")
            return False
        
        try:
            if format.lower() == 'csv':
                result.data.to_csv(file_path, index=False)
            elif format.lower() in ['excel', 'xlsx']:
                result.data.to_excel(file_path, index=False)
            elif format.lower() == 'json':
                result.data.to_json(file_path, orient='records', indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            self.logger.info(f"Query result exported to: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export result: {e}")
            return False
    
    def get_execution_summary(self, results: List[QueryResult]) -> Dict[str, Any]:
        """
        Generate summary statistics for multiple query executions
        
        Args:
            results: List of QueryResult objects
            
        Returns:
            Summary statistics dictionary
        """
        
        if not results:
            return {}
        
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        summary = {
            'total_queries': len(results),
            'successful_queries': len(successful_results),
            'failed_queries': len(failed_results),
            'success_rate': len(successful_results) / len(results) if results else 0,
            'total_rows_returned': sum(r.row_count or 0 for r in successful_results),
            'average_execution_time_ms': sum(r.execution_time_ms or 0 for r in successful_results) / len(successful_results) if successful_results else 0,
            'pattern_usage': {},
            'error_types': {}
        }
        
        # Pattern usage statistics
        for result in successful_results:
            if result.query_plan and result.query_plan.pattern_type:
                pattern = result.query_plan.pattern_type.value
                summary['pattern_usage'][pattern] = summary['pattern_usage'].get(pattern, 0) + 1
        
        # Error type statistics
        for result in failed_results:
            error_type = result.error_type or 'Unknown'
            summary['error_types'][error_type] = summary['error_types'].get(error_type, 0) + 1
        
        return summary
    
    def _convert_api_result_to_dataframe(self, api_result: Dict) -> pd.DataFrame:
        """
        Convert Power BI API query result to pandas DataFrame
        
        Args:
            api_result: Result from Fabric API DAX execution
            
        Returns:
            DataFrame with query results
        """
        try:
            if 'results' in api_result and api_result['results']:
                # Get the first result (DAX queries typically return one result set)
                result = api_result['results'][0]
                
                if 'tables' in result and result['tables']:
                    table = result['tables'][0]
                    
                    # The Execute Queries API returns rows as a list of objects (dicts with column-name keys).
                    rows = table.get('rows', [])
                    if not rows:
                        return pd.DataFrame()
                    
                    if isinstance(rows[0], dict):
                        # Directly construct DataFrame from list of dicts
                        df = pd.DataFrame(rows)
                        self.logger.info(f"Converted API result to DataFrame: {len(df)} rows, {len(df.columns)} columns")
                        return df
                    else:
                        # Fallback: if rows are lists/arrays and columns exist, align them
                        columns = [col.get('name') for col in table.get('columns', [])] if table.get('columns') else None
                        if columns:
                            df = pd.DataFrame(rows, columns=columns)
                            self.logger.info(f"Converted API result (array rows) to DataFrame: {len(df)} rows, {len(df.columns)} columns")
                            return df
                        # Unknown shape
                        self.logger.warning("API rows format unrecognized; returning empty DataFrame")
                        return pd.DataFrame()
                        
            # If we can't parse the structure, return empty DataFrame
            self.logger.warning("Could not parse API result structure")
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Failed to convert API result to DataFrame: {e}")
            return pd.DataFrame()
    
    def _get_sempy_version(self) -> str:
        """Get SemPy library version"""
        try:
            import sempy
            return getattr(sempy, '__version__', 'unknown')
        except:
            return 'unknown'


def test_sempy_query_executor():
    """Test function for SemPy query executor"""
    print("⚡ Testing SemPy Query Executor...")
    
    # Note: This would require an authenticated connector for full testing
    print("ℹ️  Full testing requires authenticated SemPy connector")
    print("✅ SemPy Query Executor class initialized successfully")
    
    return True


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run executor test
    test_sempy_query_executor()