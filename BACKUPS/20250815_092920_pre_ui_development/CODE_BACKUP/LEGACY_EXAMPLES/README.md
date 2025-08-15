# Legacy Examples and Reference Implementations

This directory contains example scripts, proof-of-concept implementations, and reference code that demonstrate various approaches to DAX/SQL query execution and Power BI integration.

## DAX Query Examples

### XMLA Endpoint Examples
- **`dax_xmla_query_example.py`** - Basic DAX query execution via XMLA endpoint
- **`dax_xmla_query_parsed.py`** - DAX query with result parsing and formatting

### Legacy Implementations
- **`dax_401_final_fix.py`** - Historical approach to resolving DAX 401 errors
- **`test_corrected_dax.py`** - Test script for DAX query correction and validation
- **`corrected_dax_query.dax`** - Example of a corrected DAX query file

## Comparison and Analysis Scripts

### Method Comparisons
- **`compare_dax_methods.py`** - Compare different DAX execution methods and performance
- **`compare_dax_sql.py`** - Side-by-side comparison of DAX vs SQL query results
- **`test_endpoint_comparison.py`** - Performance comparison of different API endpoints

### Alternative Approaches
- **`alternative_table_discovery.py`** - Alternative methods for discovering table structures

## Documentation and Guides

### Setup Guides
- **`diagnostic_summary.py`** - Legacy diagnostic summary generation
- **`enable_xmla_guide.py`** - Guide for enabling XMLA endpoints (reference implementation)

## Usage Notes

### Educational Purpose
These scripts serve as:
- **Learning Examples**: Understand different implementation approaches
- **Reference Code**: Copy patterns for new implementations
- **Historical Context**: See evolution of solutions over time
- **Troubleshooting Aid**: Compare working vs non-working implementations

### Common Patterns Demonstrated

1. **XMLA Connectivity**: Multiple approaches to connecting to Power BI via XMLA
2. **Error Handling**: Various strategies for handling authentication and query errors
3. **Result Processing**: Different methods for parsing and displaying query results
4. **Performance Optimization**: Techniques for improving query execution speed

### Implementation Evolution

The scripts in this directory show the evolution of the NL2DAX project:

1. **Early Implementations**: Basic DAX query execution
2. **Error Resolution**: Approaches to common issues like 401 errors
3. **Performance Improvements**: Optimized connection and query methods
4. **Cross-Platform Support**: Solutions for macOS/Linux compatibility

## Integration with Current Pipeline

While these are legacy examples, many patterns are still relevant:

- **Authentication Methods**: Token acquisition and management
- **Query Formatting**: DAX syntax validation and formatting
- **Error Handling**: Graceful failure and retry logic
- **Result Processing**: Table formatting and display

## When to Use These Examples

### For Learning
- Study different implementation approaches
- Understand historical context of current solutions
- Learn from past mistakes and solutions

### For Development
- Reference implementations when building new features
- Copy proven patterns for authentication and connectivity
- Use as starting point for custom implementations

### For Troubleshooting
- Compare current issues with historical solutions
- Understand why certain approaches were abandoned
- Find alternative methods when current approach fails

## Migration Notes

When updating the main pipeline, consider:

1. **Proven Patterns**: Extract successful patterns from legacy code
2. **Error Handling**: Incorporate robust error handling approaches
3. **Compatibility**: Maintain backward compatibility where possible
4. **Performance**: Apply performance optimizations discovered in examples

## Maintenance

These examples are:
- **Preserved for Reference**: Historical value and learning
- **Not Actively Maintained**: May use outdated dependencies
- **Documentation Purpose**: Serve as implementation guides
- **Starting Points**: Can be adapted for new requirements

## Security Considerations

Legacy examples may contain:
- **Outdated Authentication**: Review before using in production
- **Hardcoded Values**: Replace with environment variables
- **Deprecated APIs**: Update to current API versions
- **Security Vulnerabilities**: Audit before deployment
