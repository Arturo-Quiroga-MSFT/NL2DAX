"""
enhanced_dax_generator.py - Enhanced DAX Generator Using Clean DAX Engine
========================================================================

This module integrates the Clean DAX Engine capabilities into the UNIVERSAL pipeline,
providing improved schema management, validation, and pattern-based DAX generation.

Key Enhancements:
- Uses Clean DAX Engine's proven patterns and schema management
- Improved validation with calculated column recognition
- Focus on core FACT and DIMENSION tables only
- Dimension-first approach with CALCULATE syntax for better relationships
- Comprehensive column classification and measure selection

Author: NL2DAX Pipeline Development Team  
Last Updated: August 18, 2025
"""

import os
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add clean_dax_core to path for direct imports
current_dir = os.path.dirname(__file__)
clean_dax_core_path = os.path.join(current_dir, '..', 'clean_dax_core')
sys.path.insert(0, clean_dax_core_path)

# Import local Clean DAX Engine components directly
try:
    import schema_manager
    import dax_generator  
    import dax_validator
    import dax_executor
    
    SchemaManager = schema_manager.SchemaManager
    CleanDAXGenerator = dax_generator.CleanDAXGenerator
    DAXGenerationRequest = dax_generator.DAXGenerationRequest
    CleanDAXValidator = dax_validator.CleanDAXValidator
    CleanDAXExecutor = dax_executor.CleanDAXExecutor
    
    CLEAN_DAX_AVAILABLE = True
    print("[INFO] Clean DAX Engine components loaded successfully from local copy")
except ImportError as e:
    print(f"[WARNING] Clean DAX Engine not available: {e}")
    CLEAN_DAX_AVAILABLE = False

@dataclass
class EnhancedDAXResult:
    """Enhanced DAX generation result"""
    dax_query: str
    success: bool
    pattern_used: str
    confidence_score: float
    execution_success: bool
    data: List[Dict[str, Any]]
    row_count: int
    execution_time: float
    validation_issues: List[str]
    error_message: Optional[str] = None

class EnhancedDAXGenerator:
    """Enhanced DAX generator using Clean DAX Engine capabilities"""
    
    def __init__(self):
        """Initialize the enhanced DAX generator"""
        self.clean_dax_available = CLEAN_DAX_AVAILABLE
        self.schema_manager = None
        self.dax_generator = None
        self.dax_validator = None
        self.dax_executor = None
        
        if self.clean_dax_available:
            try:
                print("[INFO] Initializing Enhanced DAX Generator with Clean DAX Engine components...")
                # Use cache directory from UNIVERSAL system
                cache_dir = os.path.join(os.path.dirname(__file__), '..', 'cache')
                self.schema_manager = SchemaManager(cache_dir)
                self.dax_generator = CleanDAXGenerator(self.schema_manager)
                self.dax_validator = CleanDAXValidator(self.schema_manager)
                self.dax_executor = CleanDAXExecutor()
                print("[SUCCESS] Enhanced DAX Generator ready with Clean DAX Engine integration")
            except Exception as e:
                print(f"[WARNING] Failed to initialize Clean DAX Engine components: {e}")
                self.clean_dax_available = False
    
    def generate_dax(self, business_intent: str, schema_info: Dict[str, Any], 
                    analysis_type: str = "custom", limit: int = 10, 
                    execute: bool = True) -> EnhancedDAXResult:
        """
        Generate DAX query using enhanced capabilities
        
        Args:
            business_intent: Natural language description of what the user wants
            schema_info: Schema information (for compatibility, but Clean DAX Engine uses its own)
            analysis_type: Type of analysis requested
            limit: Number of results to return
            execute: Whether to execute the query against Power BI
            
        Returns:
            EnhancedDAXResult with generation and execution details
        """
        
        if not self.clean_dax_available or not self.dax_generator:
            return self._fallback_generation(business_intent, schema_info, limit)
        
        try:
            print(f"[INFO] Enhanced DAX Generator processing: {business_intent}")
            
            # Use Clean DAX Engine components for generation and validation
            request = DAXGenerationRequest(
                business_intent=business_intent,
                limit=limit
            )
            
            # Generate DAX
            generation_result = self.dax_generator.generate_dax(request)
            
            # Validate DAX
            validation_result = self.dax_validator.validate(generation_result.dax_query)
            
            # Extract validation issues as strings
            validation_issues = [f"{issue.severity.value}: {issue.message}" for issue in validation_result.issues]
            
            # Execute DAX if requested
            execution_success = False
            data = []
            row_count = 0
            execution_time = 0.0
            error_message = None
            
            if execute and self.dax_executor:
                try:
                    print("[INFO] Executing DAX query against Power BI...")
                    execution_result = self.dax_executor.execute(generation_result.dax_query, limit)
                    execution_success = execution_result.success
                    data = execution_result.data
                    row_count = execution_result.row_count
                    execution_time = execution_result.execution_time
                    if not execution_success:
                        error_message = execution_result.error_message
                        print(f"[ERROR] DAX execution failed: {error_message}")
                    else:
                        print(f"[SUCCESS] DAX executed successfully: {row_count} rows in {execution_time:.3f}s")
                except Exception as e:
                    error_message = str(e)
                    print(f"[ERROR] DAX execution exception: {error_message}")
            
            return EnhancedDAXResult(
                dax_query=generation_result.dax_query,
                success=True,
                pattern_used=generation_result.pattern_used,
                confidence_score=generation_result.confidence_score,
                execution_success=execution_success,
                data=data,
                row_count=row_count,
                execution_time=execution_time,
                validation_issues=validation_issues,
                error_message=error_message
            )
            
        except Exception as e:
            print(f"[ERROR] Enhanced DAX generation failed: {e}")
            return EnhancedDAXResult(
                dax_query="",
                success=False,
                pattern_used="Error",
                confidence_score=0.0,
                execution_success=False,
                data=[],
                row_count=0,
                execution_time=0.0,
                validation_issues=[],
                error_message=str(e)
            )
    
    def _fallback_generation(self, business_intent: str, schema_info: Dict[str, Any], 
                           limit: int) -> EnhancedDAXResult:
        """Fallback generation when Clean DAX Engine is not available"""
        print("[WARNING] Using fallback DAX generation - Clean DAX Engine not available")
        
        # Simple fallback DAX template
        fallback_dax = f"""EVALUATE
TOPN(
    {limit},
    VALUES('FIS_CUSTOMER_DIMENSION'[CUSTOMER_NAME])
)"""
        
        return EnhancedDAXResult(
            dax_query=fallback_dax,
            success=True,
            pattern_used="Fallback Template",
            confidence_score=0.5,
            execution_success=False,
            data=[],
            row_count=0,
            execution_time=0.0,
            validation_issues=["Using fallback generation - limited functionality"],
            error_message="Clean DAX Engine not available"
        )
    
    def get_schema_summary(self) -> Dict[str, Any]:
        """Get schema summary from Clean DAX Engine"""
        if not self.clean_dax_available or not self.clean_engine:
            return {"tables": 0, "fact_tables": [], "dimension_tables": []}
        
        try:
            schema = self.clean_engine.schema_manager.get_schema()
            fact_tables = [name for name, table in schema.tables.items() if table.table_type == 'fact']
            dimension_tables = [name for name, table in schema.tables.items() if table.table_type == 'dimension']
            
            return {
                "total_tables": len(schema.tables),
                "fact_tables": fact_tables,
                "dimension_tables": dimension_tables,
                "schema_type": "Enhanced Star Schema (FACT/DIMENSION only)"
            }
        except Exception as e:
            print(f"[ERROR] Failed to get schema summary: {e}")
            return {"error": str(e)}
    
    def validate_dax(self, dax_query: str) -> Dict[str, Any]:
        """Validate DAX query using Clean DAX Engine validator"""
        if not self.clean_dax_available or not self.clean_engine:
            return {"valid": False, "issues": ["Clean DAX Engine not available"]}
        
        try:
            result = self.clean_engine.validator.validate(dax_query)
            return {
                "valid": result.is_valid,
                "issues": [f"{issue.severity.value}: {issue.message}" for issue in result.issues],
                "tables_referenced": result.tables_referenced,
                "columns_referenced": result.columns_referenced
            }
        except Exception as e:
            return {"valid": False, "issues": [f"Validation error: {e}"]}

# Compatibility function for existing UNIVERSAL pipeline
def create_enhanced_dax_generator() -> EnhancedDAXGenerator:
    """Factory function to create enhanced DAX generator"""
    return EnhancedDAXGenerator()