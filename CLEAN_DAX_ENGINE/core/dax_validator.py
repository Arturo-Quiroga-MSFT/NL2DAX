"""
Clean DAX Validator - Comprehensive DAX validation
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from schema_manager import SchemaManager

class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    ERROR = "ERROR"
    WARNING = "WARNING" 
    INFO = "INFO"

@dataclass
class ValidationIssue:
    """A validation issue found in DAX query"""
    severity: ValidationSeverity
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None

@dataclass
class ValidationResult:
    """Result of DAX validation"""
    is_valid: bool
    issues: List[ValidationIssue]
    tables_referenced: List[str]
    columns_referenced: List[str]
    
    @property
    def has_errors(self) -> bool:
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
    
    @property
    def has_warnings(self) -> bool:
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)

class CleanDAXValidator:
    """Clean DAX validator with comprehensive checks"""
    
    def __init__(self, schema_manager: SchemaManager):
        self.schema_manager = schema_manager
    
    def validate(self, dax_query: str) -> ValidationResult:
        """Perform comprehensive DAX validation"""
        issues = []
        tables_referenced = []
        columns_referenced = []
        
        # Basic syntax validation
        issues.extend(self._validate_syntax(dax_query))
        
        # Extract references
        tables_referenced = self._extract_table_references(dax_query)
        columns_referenced = self._extract_column_references(dax_query)
        
        # Schema validation
        issues.extend(self._validate_schema_references(tables_referenced, columns_referenced))
        
        # Best practices validation
        issues.extend(self._validate_best_practices(dax_query))
        
        # DAX pattern validation
        issues.extend(self._validate_dax_patterns(dax_query))
        
        is_valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            tables_referenced=tables_referenced,
            columns_referenced=columns_referenced
        )
    
    def _validate_syntax(self, dax_query: str) -> List[ValidationIssue]:
        """Validate basic DAX syntax"""
        issues = []
        
        # Check for EVALUATE statement
        if not dax_query.strip().upper().startswith('EVALUATE'):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="DAX query must start with EVALUATE",
                suggestion="Add 'EVALUATE' at the beginning of your query"
            ))
        
        # Check for balanced parentheses
        open_parens = dax_query.count('(')
        close_parens = dax_query.count(')')
        if open_parens != close_parens:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Unbalanced parentheses: {open_parens} open, {close_parens} close",
                suggestion="Check for missing opening or closing parentheses"
            ))
        
        # Check for valid table reference syntax
        if "'" in dax_query:
            # Check for properly quoted table names
            table_pattern = r"'([^']+)'"
            matches = re.findall(table_pattern, dax_query)
            for match in matches:
                if not match.strip():
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message="Empty table name in quotes",
                        suggestion="Ensure table names are not empty"
                    ))
        
        return issues
    
    def _extract_table_references(self, dax_query: str) -> List[str]:
        """Extract all table references from DAX query"""
        # Pattern to match table references like 'TableName'
        table_pattern = r"'([^']+)'"
        matches = re.findall(table_pattern, dax_query)
        
        # Filter out obvious non-table references (columns with brackets)
        tables = []
        for match in matches:
            if '[' not in match and ']' not in match:
                tables.append(match)
        
        return list(set(tables))  # Remove duplicates
    
    def _extract_column_references(self, dax_query: str) -> List[str]:
        """Extract all column references from DAX query"""
        # Pattern to match column references like 'TableName'[ColumnName] or [ColumnName]
        column_pattern = r"(?:'[^']+')?\[([^\]]+)\]"
        matches = re.findall(column_pattern, dax_query)
        
        return list(set(matches))  # Remove duplicates
    
    def _validate_schema_references(self, tables: List[str], columns: List[str]) -> List[ValidationIssue]:
        """Validate that referenced tables and columns exist in schema"""
        issues = []
        schema = self.schema_manager.get_schema()
        
        # Validate table references
        for table in tables:
            if not self.schema_manager.validate_table_exists(table):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Table '{table}' not found in schema",
                    suggestion="Check the available table names in your schema"
                ))
        
        # Validate column references (basic check - would need more context for table-specific validation)
        known_columns = set()
        for table_info in schema.tables.values():
            known_columns.update(table_info.columns)
        
        for column in columns:
            if column not in known_columns:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Column '{column}' not found in any table",
                    suggestion="Verify column name spelling and availability"
                ))
        
        return issues
    
    def _validate_best_practices(self, dax_query: str) -> List[ValidationIssue]:
        """Validate DAX best practices"""
        issues = []
        
        # Check for customer aggregation patterns
        if 'customer' in dax_query.lower() and 'summarize' in dax_query.upper():
            # Check if starting from dimension table
            if re.search(r"SUMMARIZE\s*\(\s*'[^']*DIMENSION[^']*'", dax_query, re.IGNORECASE):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="Customer aggregation starting from dimension table may cause incorrect totals",
                    suggestion="Start aggregation from fact table and use RELATED() for dimension attributes"
                ))
        
        # Check for ORDER BY usage (not supported in DAX)
        if 'ORDER BY' in dax_query.upper():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="ORDER BY is not supported in DAX",
                suggestion="Use TOPN() function for ranking instead"
            ))
        
        # Check for nested CALCULATE functions
        calculate_count = len(re.findall(r'CALCULATE\s*\(', dax_query, re.IGNORECASE))
        if calculate_count > 2:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Multiple CALCULATE functions detected",
                suggestion="Consider simplifying the calculation logic for better performance"
            ))
        
        return issues
    
    def _validate_dax_patterns(self, dax_query: str) -> List[ValidationIssue]:
        """Validate specific DAX patterns and structures"""
        issues = []
        
        # Check for TOPN with proper structure
        if 'TOPN' in dax_query.upper():
            # TOPN should have proper parameters
            topn_pattern = r'TOPN\s*\(\s*\d+\s*,'
            if not re.search(topn_pattern, dax_query, re.IGNORECASE):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="TOPN function should have a numeric limit as first parameter",
                    suggestion="Use TOPN(N, table, sort_column, DESC/ASC) syntax"
                ))
        
        # Check for RELATED usage in proper context
        if 'RELATED(' in dax_query.upper():
            # RELATED should be used within row context
            if 'SUMMARIZE' not in dax_query.upper() and 'ADDCOLUMNS' not in dax_query.upper():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="RELATED() function used outside of row context",
                    suggestion="RELATED() should be used within SUMMARIZE() or ADDCOLUMNS() context"
                ))
        
        return issues