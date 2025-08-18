"""
Clean DAX Executor - Power BI execution engine
"""
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings

@dataclass
class ExecutionResult:
    """Result of DAX execution"""
    success: bool
    data: List[Dict[str, Any]]
    row_count: int
    execution_time: float
    error_message: Optional[str] = None
    columns: Optional[List[str]] = None

class CleanDAXExecutor:
    """Clean DAX executor for Power BI"""
    
    def __init__(self):
        self.config = settings.powerbi
        self._executor = None
    
    def execute(self, dax_query: str, limit: Optional[int] = None) -> ExecutionResult:
        """Execute DAX query against Power BI"""
        import time
        start_time = time.time()
        
        try:
            # Apply limit if specified
            limited_query = self._apply_limit(dax_query, limit)
            
            # Get the executor
            executor_func = self._get_executor()
            
            # Execute the query
            result_data = executor_func(limited_query)
            
            execution_time = time.time() - start_time
            
            # Extract columns if data exists
            columns = list(result_data[0].keys()) if result_data else []
            
            return ExecutionResult(
                success=True,
                data=result_data,
                row_count=len(result_data),
                execution_time=execution_time,
                columns=columns
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                data=[],
                row_count=0,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def _get_executor(self):
        """Get the DAX executor function"""
        if self._executor is None:
            try:
                # Import the existing HTTP/XMLA executor
                sys.path.append('/Users/arturoquiroga/GITHUB/NL2DAX/CODE/NL2DAX_PIPELINE')
                from xmla_http_executor import execute_dax_via_http
                self._executor = execute_dax_via_http
                print("[INFO] Using HTTP/XMLA executor for Power BI")
            except ImportError as e:
                raise RuntimeError(f"Failed to import DAX executor: {e}")
        
        return self._executor
    
    def _apply_limit(self, dax_query: str, limit: Optional[int]) -> str:
        """Apply row limit to DAX query if specified"""
        if limit is None:
            limit = settings.dax.max_results
        
        # If query already has TOPN, don't modify
        if 'TOPN(' in dax_query.upper():
            return dax_query
        
        # For other queries, we can't easily add TOPN, so just return as-is
        # The executor might have its own limiting mechanism
        return dax_query
    
    def test_connection(self) -> bool:
        """Test the Power BI connection"""
        try:
            # Simple test query
            test_query = "EVALUATE ROW(\"Test\", 1)"
            result = self.execute(test_query)
            return result.success
        except Exception:
            return False