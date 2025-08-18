"""
dax_query_validator.py - DAX Query Validation System
===================================================

This module provides comprehensive validation for generated DAX queries to ensure
they use correct syntax and reference existing tables, columns, and relationships
from the discovered database schema.

Key Features:
- DAX syntax validation (EVALUATE, table references, functions)
- Table and column existence validation against discovered schema
- Relationship validation for RELATED() functions
- DAX best practices checking
- Detailed error reporting with suggestions
- Performance optimization recommendations

Author: NL2DAX Pipeline Development Team
Last Updated: August 18, 2025
"""

import re
import json
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    ERROR = "error"          # Will prevent execution
    WARNING = "warning"      # May cause issues
    INFO = "info"           # Best practice suggestions

@dataclass
class ValidationIssue:
    """Represents a DAX validation issue"""
    severity: ValidationSeverity
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    
    def __str__(self) -> str:
        prefix = "❌" if self.severity == ValidationSeverity.ERROR else "⚠️" if self.severity == ValidationSeverity.WARNING else "💡"
        line_info = f" (Line {self.line_number})" if self.line_number else ""
        suggestion_info = f"\n   💡 Suggestion: {self.suggestion}" if self.suggestion else ""
        return f"{prefix} {self.severity.value.upper()}{line_info}: {self.message}{suggestion_info}"

@dataclass
class ValidationResult:
    """Result of DAX query validation"""
    is_valid: bool
    issues: List[ValidationIssue]
    corrected_query: Optional[str] = None
    
    @property
    def has_errors(self) -> bool:
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
    
    @property
    def has_warnings(self) -> bool:
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)
    
    def print_summary(self):
        """Print validation summary"""
        if self.is_valid:
            print("✅ DAX query validation passed")
        else:
            print("❌ DAX query validation failed")
        
        if self.issues:
            print("\nValidation Issues:")
            for issue in self.issues:
                print(f"  {issue}")
        
        if self.corrected_query and not self.is_valid:
            print("\n📝 Suggested corrected query:")
            print(self.corrected_query)


class DAXQueryValidator:
    """Validates DAX queries against discovered database schema"""
    
    def __init__(self, schema_info: Dict[str, Any]):
        """
        Initialize DAX validator with schema information
        
        Args:
            schema_info: Discovered database schema with tables, columns, relationships
        """
        self.schema_info = schema_info
        self.tables = self._extract_table_info()
        self.relationships = self._extract_relationship_info()
        
        # DAX function patterns
        self.dax_functions = {
            'aggregation': ['SUM', 'COUNT', 'AVERAGE', 'MIN', 'MAX', 'COUNTROWS', 'DISTINCTCOUNT'],
            'filter': ['FILTER', 'CALCULATE', 'CALCULATETABLE', 'ALL', 'ALLEXCEPT'],
            'table': ['SUMMARIZE', 'ADDCOLUMNS', 'SELECTCOLUMNS', 'TOPN', 'EVALUATE'],
            'relationship': ['RELATED', 'RELATEDTABLE', 'USERELATIONSHIP'],
            'time': ['DATESYTD', 'DATEADD', 'SAMEPERIODLASTYEAR', 'TOTALYTD'],
            'logical': ['IF', 'SWITCH', 'AND', 'OR', 'NOT']
        }
    
    def _extract_table_info(self) -> Dict[str, Dict[str, Any]]:
        """Extract table and column information from schema"""
        tables_info = {}
        
        if isinstance(self.schema_info, dict) and 'tables' in self.schema_info:
            for table_name, table_data in self.schema_info['tables'].items():
                tables_info[table_name.upper()] = {
                    'original_name': table_name,
                    'columns': [col.upper() for col in table_data.get('columns', [])],
                    'original_columns': table_data.get('columns', []),
                    'table_type': table_data.get('table_type', 'unknown')
                }
        
        return tables_info
    
    def _extract_relationship_info(self) -> List[Dict[str, str]]:
        """Extract relationship information from schema"""
        relationships = []
        
        if isinstance(self.schema_info, dict) and 'relationships' in self.schema_info:
            for rel in self.schema_info['relationships']:
                relationships.append({
                    'from_table': rel.get('from_table', '').upper(),
                    'to_table': rel.get('to_table', '').upper(),
                    'from_column': rel.get('from_column', '').upper(),
                    'to_column': rel.get('to_column', '').upper()
                })
        
        return relationships
    
    def validate_dax_query(self, dax_query: str) -> ValidationResult:
        """
        Validate a DAX query against the schema
        
        Args:
            dax_query: DAX query string to validate
            
        Returns:
            ValidationResult with issues and suggestions
        """
        issues = []
        
        # Clean and normalize the query
        normalized_query = self._normalize_query(dax_query)
        
        # 1. Basic syntax validation
        issues.extend(self._validate_basic_syntax(normalized_query))
        
        # 2. Table reference validation
        issues.extend(self._validate_table_references(normalized_query))
        
        # 3. Column reference validation
        issues.extend(self._validate_column_references(normalized_query))
        
        # 4. Function usage validation
        issues.extend(self._validate_function_usage(normalized_query))
        
        # 5. Relationship validation
        issues.extend(self._validate_relationships(normalized_query))
        
        # 6. Customer aggregation pattern validation
        issues.extend(self._validate_customer_aggregation_patterns(normalized_query))
        
        # 7. Best practices check
        issues.extend(self._check_best_practices(normalized_query))
        
        # Determine if query is valid (no errors)
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        is_valid = not has_errors
        
        # Generate corrected query if there are fixable issues
        corrected_query = self._generate_corrected_query(normalized_query, issues) if not is_valid else None
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            corrected_query=corrected_query
        )
    
    def _normalize_query(self, query: str) -> str:
        """Normalize DAX query for analysis"""
        # Remove extra whitespace and normalize line endings
        normalized = re.sub(r'\s+', ' ', query.strip())
        return normalized
    
    def _validate_basic_syntax(self, query: str) -> List[ValidationIssue]:
        """Validate basic DAX syntax"""
        issues = []
        
        # Check if query starts with EVALUATE
        if not query.upper().startswith('EVALUATE'):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="DAX query must start with EVALUATE",
                suggestion="Add 'EVALUATE' at the beginning of your query"
            ))
        
        # Check for balanced parentheses
        open_parens = query.count('(')
        close_parens = query.count(')')
        if open_parens != close_parens:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Unbalanced parentheses: {open_parens} opening, {close_parens} closing",
                suggestion="Check that all parentheses are properly closed"
            ))
        
        # Check for proper table reference syntax
        invalid_table_refs = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\[[A-Za-z_][A-Za-z0-9_]*\]', query)
        if invalid_table_refs:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Table references must use single quotes: 'TableName'[ColumnName]",
                suggestion="Replace table[column] with 'table'[column]"
            ))
        
        return issues
    
    def _validate_table_references(self, query: str) -> List[ValidationIssue]:
        """Validate that referenced tables exist in the schema"""
        issues = []
        
        # Extract table references from query
        table_pattern = r"'([^']+)'"
        referenced_tables = set(re.findall(table_pattern, query))
        
        for table_ref in referenced_tables:
            table_upper = table_ref.upper()
            if table_upper not in self.tables:
                # Try to find close matches
                close_matches = [t for t in self.tables.keys() if t.replace('_', '').replace(' ', '') == table_upper.replace('_', '').replace(' ', '')]
                
                suggestion = f"Did you mean '{close_matches[0]}'?" if close_matches else "Check the available table names in your schema"
                
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Table '{table_ref}' not found in schema",
                    suggestion=suggestion
                ))
        
        return issues
    
    def _validate_column_references(self, query: str) -> List[ValidationIssue]:
        """Validate that referenced columns exist in their tables"""
        issues = []
        
        # Extract table.column references
        column_pattern = r"'([^']+)'\[([^\]]+)\]"
        column_references = re.findall(column_pattern, query)
        
        for table_ref, column_ref in column_references:
            table_upper = table_ref.upper()
            column_upper = column_ref.upper()
            
            if table_upper in self.tables:
                table_columns = self.tables[table_upper]['columns']
                if column_upper not in table_columns:
                    # Try to find close matches
                    close_matches = [c for c in table_columns if c.replace('_', '').replace(' ', '') == column_upper.replace('_', '').replace(' ', '')]
                    
                    suggestion = f"Did you mean '{close_matches[0]}'?" if close_matches else f"Available columns in '{table_ref}': {', '.join(self.tables[table_upper]['original_columns'][:5])}"
                    
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Column '{column_ref}' not found in table '{table_ref}'",
                        suggestion=suggestion
                    ))
        
        return issues
    
    def _validate_function_usage(self, query: str) -> List[ValidationIssue]:
        """Validate DAX function usage"""
        issues = []
        
        # Check for common mistakes
        if 'ORDER BY' in query.upper():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="ORDER BY is not supported in DAX. Use TOPN() for sorting",
                suggestion="Replace ORDER BY with TOPN(n, table, sort_column, direction)"
            ))
        
        if 'LIMIT' in query.upper():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="LIMIT is not supported in DAX. Use TOPN() for limiting results",
                suggestion="Use TOPN(n, table, sort_column) to limit results"
            ))
        
        # Check for SUMMARIZECOLUMNS with multiple tables (common mistake)
        if 'SUMMARIZECOLUMNS' in query.upper():
            # Count table references in SUMMARIZECOLUMNS
            summarize_pattern = r'SUMMARIZECOLUMNS\s*\([^)]+\)'
            summarize_matches = re.findall(summarize_pattern, query, re.IGNORECASE)
            for match in summarize_matches:
                table_refs = re.findall(r"'([^']+)'", match)
                unique_tables = set(table_refs)
                if len(unique_tables) > 1:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message="SUMMARIZECOLUMNS with multiple tables may cause cartesian products",
                        suggestion="Consider using ADDCOLUMNS(SUMMARIZE()) pattern instead"
                    ))
        
        return issues
    
    def _validate_relationships(self, query: str) -> List[ValidationIssue]:
        """Validate RELATED() function usage and relationships"""
        issues = []
        
        # Extract RELATED function calls
        related_pattern = r'RELATED\s*\(\s*\'([^\']+)\'\[([^\]]+)\]\s*\)'
        related_calls = re.findall(related_pattern, query, re.IGNORECASE)
        
        for table_ref, column_ref in related_calls:
            table_upper = table_ref.upper()
            
            # Check if the table exists
            if table_upper not in self.tables:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"RELATED() references non-existent table '{table_ref}'",
                    suggestion="Check table name spelling and schema"
                ))
                continue
            
            # Check if there's a relationship to this table
            has_relationship = any(
                rel['to_table'] == table_upper or rel['from_table'] == table_upper
                for rel in self.relationships
            )
            
            if not has_relationship and len(self.relationships) > 0:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"No relationship found to table '{table_ref}' for RELATED() function",
                    suggestion="Verify that a relationship exists between the tables"
                ))
        
        return issues
    
    def _check_best_practices(self, query: str) -> List[ValidationIssue]:
        """Check DAX best practices"""
        issues = []
        
        # Check query length (performance)
        if len(query) > 2000:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Very long DAX query may impact performance",
                suggestion="Consider breaking complex queries into smaller parts"
            ))
        
        # Check for nested CALCULATE functions
        nested_calculate = query.upper().count('CALCULATE(') > 1
        if nested_calculate:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Nested CALCULATE functions detected",
                suggestion="Consider simplifying the calculation logic for better performance"
            ))
        
        # Check if TOPN is used with proper sorting
        if 'TOPN(' in query.upper() and 'DESC' not in query.upper() and 'ASC' not in query.upper():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="TOPN without explicit sort direction",
                suggestion="Add DESC or ASC to TOPN for explicit sorting direction"
            ))
        
        return issues
    
    def _generate_corrected_query(self, query: str, issues: List[ValidationIssue]) -> Optional[str]:
        """Generate a corrected version of the query based on validation issues"""
        corrected = query
        
        # Simple corrections for common issues
        for issue in issues:
            if "must start with EVALUATE" in issue.message:
                if not corrected.upper().startswith('EVALUATE'):
                    corrected = f"EVALUATE\\n{corrected}"
            
            elif "ORDER BY is not supported" in issue.message:
                # This would require more complex parsing to fix properly
                pass
            
            elif "Table references must use single quotes" in issue.message:
                # Fix table reference syntax
                corrected = re.sub(r'\\b([A-Za-z_][A-Za-z0-9_]*)\\[', r"'\\1'[", corrected)
        
        return corrected if corrected != query else None
    
    def get_schema_summary(self) -> str:
        """Get a summary of the available schema for reference"""
        summary = ["Available Schema Information:", ""]
        
        summary.append(f"📊 Total Tables: {len(self.tables)}")
        summary.append("")
        
        for table_name, table_info in list(self.tables.items())[:10]:  # Show first 10 tables
            original_name = table_info['original_name']
            columns = table_info['original_columns'][:5]  # Show first 5 columns
            table_type = table_info.get('table_type', 'unknown')
            
            summary.append(f"🔹 '{original_name}' ({table_type})")
            summary.append(f"   Columns: {', '.join(columns)}")
            if len(table_info['original_columns']) > 5:
                summary.append(f"   ... and {len(table_info['original_columns']) - 5} more")
            summary.append("")
        
        if len(self.tables) > 10:
            summary.append(f"... and {len(self.tables) - 10} more tables")
        
        return "\\n".join(summary)

    def _validate_customer_aggregation_patterns(self, query: str) -> List[ValidationIssue]:
        """Validate customer aggregation patterns for context issues"""
        issues = []
        
        # Detect the problematic pattern: SUMMARIZE(dimension) + CALCULATE(SUM(fact))
        if 'SUMMARIZE' in query.upper() and 'CUSTOMER_DIMENSION' in query.upper():
            # Check if CALCULATE(SUM()) is used without proper filter context
            if 'CALCULATE(SUM(' in query and 'FACT' in query.upper():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Customer aggregation starting from dimension table may cause incorrect totals",
                    suggestion="Start aggregation from fact table and use RELATED() for dimension attributes, or ensure proper filter context in CALCULATE functions"
                ))
                
        # Check for VALUES() used in customer aggregation context
        if 'VALUES(' in query and 'CUSTOMER' in query.upper() and 'ADDCOLUMNS' in query.upper():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="VALUES() in customer aggregation may not provide proper row context",
                suggestion="Consider using SUMMARIZE() from fact table with RELATED() for dimension attributes"
            ))
            
        return issues


# Utility functions
def validate_dax_with_schema(dax_query: str, schema_info: Dict[str, Any]) -> ValidationResult:
    """
    Convenience function to validate a DAX query with schema
    
    Args:
        dax_query: DAX query to validate
        schema_info: Schema information from discovery
        
    Returns:
        ValidationResult
    """
    validator = DAXQueryValidator(schema_info)
    return validator.validate_dax_query(dax_query)


def validate_single_dax_query(dax_query: str, schema_info: Dict[str, Any]) -> ValidationResult:
    """
    Standalone function to validate a single DAX query
    
    Args:
        dax_query: DAX query string to validate
        schema_info: Schema information dictionary
        
    Returns:
        ValidationResult with validation details
    """
    validator = DAXQueryValidator(schema_info)
    return validator.validate_dax_query(dax_query)


# Example usage and testing
if __name__ == "__main__":
    print("DAX Query Validator Test")
    print("=" * 40)
    
    # Example schema for testing
    test_schema = {
        'tables': {
            'FIS_CUSTOMER_DIMENSION': {
                'columns': ['CUSTOMER_KEY', 'CUSTOMER_NAME', 'COUNTRY_CODE'],
                'table_type': 'dimension'
            },
            'FIS_CA_DETAIL_FACT': {
                'columns': ['CUSTOMER_KEY', 'EXPOSURE_AT_DEFAULT', 'LIMIT_AMOUNT'],
                'table_type': 'fact'
            }
        },
        'relationships': [
            {
                'from_table': 'FIS_CA_DETAIL_FACT',
                'to_table': 'FIS_CUSTOMER_DIMENSION',
                'from_column': 'CUSTOMER_KEY',
                'to_column': 'CUSTOMER_KEY'
            }
        ]
    }
    
    # Test DAX queries
    test_queries = [
        # Valid query
        """EVALUATE
        TOPN(
            5,
            ADDCOLUMNS(
                'FIS_CUSTOMER_DIMENSION',
                "TotalExposure", CALCULATE(SUM('FIS_CA_DETAIL_FACT'[EXPOSURE_AT_DEFAULT]))
            ),
            [TotalExposure], DESC
        )""",
        
        # Invalid query with errors
        """SELECTCOLUMNS(
            FIS_CUSTOMER_DIMENSION,
            "Name", FIS_CUSTOMER_DIMENSION[CUSTOMER_NAME]
        )
        ORDER BY CUSTOMER_NAME"""
    ]
    
    validator = DAXQueryValidator(test_schema)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\\nTest Query {i}:")
        print("-" * 20)
        result = validator.validate_dax_query(query)
        result.print_summary()