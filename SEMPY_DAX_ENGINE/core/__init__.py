"""
SemPy DAX Engine - Core Package
===============================

Core components for the SemPy-powered DAX engine that provides
end-to-end natural language to DAX query generation and execution.

Components:
- SemPyConnector: Authentication and connection to Power BI/Fabric
- SemanticAnalyzer: Semantic model metadata discovery and analysis  
- SemPyDAXGenerator: Intelligent DAX query generation
- SemPyQueryExecutor: DAX query execution via SemPy
- SemPyDAXEngine: Main engine interface

Author: NL2DAX Pipeline Development Team
Last Updated: August 18, 2025
"""

# Import error handling for missing dependencies
import logging

try:
    from .sempy_connector import SemPyConnector, WorkspaceInfo, SemanticModelInfo, ConnectionInfo
    CONNECTOR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SemPyConnector could not be imported: {e}")
    CONNECTOR_AVAILABLE = False

try:
    from .semantic_analyzer import (
        SemanticAnalyzer, SemanticModelSchema, TableInfo, ColumnInfo, 
        MeasureInfo, RelationshipInfo, DataTypeCategory, RelationshipType
    )
    ANALYZER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SemanticAnalyzer could not be imported: {e}")
    ANALYZER_AVAILABLE = False

try:
    from .sempy_dax_generator import (
        SemPyDAXGenerator, DAXQueryPlan, QueryAnalysis, 
        QueryIntent, DAXPatternType
    )
    GENERATOR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SemPyDAXGenerator could not be imported: {e}")
    GENERATOR_AVAILABLE = False

try:
    from .sempy_query_executor import SemPyQueryExecutor, QueryResult, ExecutionContext
    EXECUTOR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SemPyQueryExecutor could not be imported: {e}")
    EXECUTOR_AVAILABLE = False

try:
    from .sempy_dax_engine import SemPyDAXEngine, EngineSession
    ENGINE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SemPyDAXEngine could not be imported: {e}")
    ENGINE_AVAILABLE = False

# Build __all__ based on what's available
__all__ = []

if CONNECTOR_AVAILABLE:
    __all__.extend(['SemPyConnector', 'WorkspaceInfo', 'SemanticModelInfo', 'ConnectionInfo'])

if ANALYZER_AVAILABLE:
    __all__.extend([
        'SemanticAnalyzer', 'SemanticModelSchema', 'TableInfo', 'ColumnInfo', 
        'MeasureInfo', 'RelationshipInfo', 'DataTypeCategory', 'RelationshipType'
    ])

if GENERATOR_AVAILABLE:
    __all__.extend([
        'SemPyDAXGenerator', 'DAXQueryPlan', 'QueryAnalysis', 
        'QueryIntent', 'DAXPatternType'
    ])

if EXECUTOR_AVAILABLE:
    __all__.extend(['SemPyQueryExecutor', 'QueryResult', 'ExecutionContext'])

if ENGINE_AVAILABLE:
    __all__.extend(['SemPyDAXEngine', 'EngineSession'])

# Availability flags
COMPONENTS_AVAILABLE = {
    'connector': CONNECTOR_AVAILABLE,
    'analyzer': ANALYZER_AVAILABLE, 
    'generator': GENERATOR_AVAILABLE,
    'executor': EXECUTOR_AVAILABLE,
    'engine': ENGINE_AVAILABLE
}

def get_availability_status():
    """Get status of component availability"""
    return COMPONENTS_AVAILABLE

def check_requirements():
    """Check if all requirements are met for full functionality"""
    all_available = all(COMPONENTS_AVAILABLE.values())
    
    if all_available:
        return True, "All components available"
    else:
        missing = [comp for comp, available in COMPONENTS_AVAILABLE.items() if not available]
        return False, f"Missing components: {', '.join(missing)}"