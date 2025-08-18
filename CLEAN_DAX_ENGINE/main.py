"""
Clean DAX Engine - Main interface for DAX generation, validation, and execution
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.schema_manager import SchemaManager
from core.dax_generator import CleanDAXGenerator, DAXGenerationRequest
from core.dax_validator import CleanDAXValidator
from core.dax_executor import CleanDAXExecutor
from config.settings import settings

@dataclass
class DAXEngineResult:
    """Complete result from DAX engine"""
    # Generation
    dax_query: str
    generation_time: float
    pattern_used: str
    confidence_score: float
    
    # Validation
    is_valid: bool
    validation_issues: List[str]
    
    # Execution
    execution_success: bool
    data: List[Dict[str, Any]]
    row_count: int
    execution_time: float
    error_message: Optional[str] = None

class CleanDAXEngine:
    """Main DAX engine orchestrating generation, validation, and execution"""
    
    def __init__(self):
        """Initialize the clean DAX engine"""
        print("[INFO] Initializing Clean DAX Engine...")
        
        # Initialize components
        self.schema_manager = SchemaManager(settings.schema.cache_dir)
        self.generator = CleanDAXGenerator(self.schema_manager)
        self.validator = CleanDAXValidator(self.schema_manager)
        self.executor = CleanDAXExecutor()
        
        # Load schema on initialization
        print("[INFO] Loading schema...")
        self.schema_manager.get_schema()
        print("[INFO] Clean DAX Engine ready!")
    
    def process_request(self, business_intent: str, limit: int = 10, execute: bool = True) -> DAXEngineResult:
        """Process a complete DAX request from intent to results"""
        
        # Step 1: Generate DAX
        print(f"[INFO] Generating DAX for: {business_intent}")
        gen_start = time.time()
        
        request = DAXGenerationRequest(
            business_intent=business_intent,
            limit=limit,
            analysis_type="customer_analysis"
        )
        
        generation_result = self.generator.generate_dax(request)
        generation_time = time.time() - gen_start
        
        print(f"[INFO] Generated DAX using pattern: {generation_result.pattern_used}")
        print(f"[INFO] Generation confidence: {generation_result.confidence_score:.2f}")
        
        # Step 2: Validate DAX
        print("[INFO] Validating DAX query...")
        validation_result = self.validator.validate(generation_result.dax_query)
        
        validation_issues = []
        for issue in validation_result.issues:
            validation_issues.append(f"{issue.severity.value}: {issue.message}")
        
        if validation_result.has_errors:
            print(f"[ERROR] Validation failed with {len(validation_issues)} issues")
            for issue in validation_issues:
                print(f"  - {issue}")
        elif validation_result.has_warnings:
            print(f"[WARNING] Validation passed with {len(validation_issues)} warnings")
            for issue in validation_issues:
                print(f"  - {issue}")
        else:
            print("[SUCCESS] DAX validation passed!")
        
        # Step 3: Execute DAX (if requested and valid)
        execution_success = False
        data = []
        row_count = 0
        execution_time = 0.0
        error_message = None
        
        if execute and not validation_result.has_errors:
            print("[INFO] Executing DAX query...")
            execution_result = self.executor.execute(generation_result.dax_query, limit)
            
            execution_success = execution_result.success
            data = execution_result.data
            row_count = execution_result.row_count
            execution_time = execution_result.execution_time
            error_message = execution_result.error_message
            
            if execution_success:
                print(f"[SUCCESS] DAX executed successfully: {row_count} rows in {execution_time:.2f}s")
            else:
                print(f"[ERROR] DAX execution failed: {error_message}")
        elif not execute:
            print("[INFO] Execution skipped (execute=False)")
        else:
            print("[INFO] Execution skipped due to validation errors")
        
        return DAXEngineResult(
            dax_query=generation_result.dax_query,
            generation_time=generation_time,
            pattern_used=generation_result.pattern_used,
            confidence_score=generation_result.confidence_score,
            is_valid=validation_result.is_valid,
            validation_issues=validation_issues,
            execution_success=execution_success,
            data=data,
            row_count=row_count,
            execution_time=execution_time,
            error_message=error_message
        )
    
    def get_schema_summary(self) -> Dict[str, Any]:
        """Get summary of the current schema"""
        schema = self.schema_manager.get_schema()
        
        fact_tables = [name for name, table in schema.tables.items() if table.table_type == 'fact']
        dimension_tables = [name for name, table in schema.tables.items() if table.table_type == 'dimension']
        
        return {
            'total_tables': len(schema.tables),
            'fact_tables': len(fact_tables),
            'dimension_tables': len(dimension_tables),
            'fact_table_names': fact_tables,
            'dimension_table_names': dimension_tables,
            'cached_at': schema.cached_at.isoformat(),
            'is_expired': schema.is_expired()
        }
    
    def test_components(self) -> Dict[str, bool]:
        """Test all engine components"""
        results = {}
        
        # Test schema manager
        try:
            schema = self.schema_manager.get_schema()
            results['schema_manager'] = len(schema.tables) > 0
        except Exception:
            results['schema_manager'] = False
        
        # Test generator
        try:
            request = DAXGenerationRequest(business_intent="test query")
            gen_result = self.generator.generate_dax(request)
            results['generator'] = bool(gen_result.dax_query)
        except Exception:
            results['generator'] = False
        
        # Test validator
        try:
            val_result = self.validator.validate("EVALUATE ROW(\"Test\", 1)")
            results['validator'] = True
        except Exception:
            results['validator'] = False
        
        # Test executor
        try:
            results['executor'] = self.executor.test_connection()
        except Exception:
            results['executor'] = False
        
        return results