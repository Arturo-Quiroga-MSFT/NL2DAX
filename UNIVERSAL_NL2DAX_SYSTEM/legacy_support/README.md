# Legacy Support and Migration Guide

## Overview
This directory provides compatibility and migration support for transitioning from the original database-specific NL2DAX pipeline to the new universal architecture.

## Legacy System Location
The original system is located in: `/CODE/NL2DAX_PIPELINE/`

## Key Differences

### Original System (Legacy)
- Hardcoded table and column names
- Database-specific query templates
- Manual schema mapping required
- Limited to specific business domains
- Required code changes for different databases

### Universal System (New)
- AI-powered schema discovery
- Database-agnostic query generation
- Automatic schema pattern recognition
- Works with any business domain
- Zero code changes for different databases

## Migration Path

### 1. Environment Setup
The universal system requires the same basic environment as the legacy system:
- Azure OpenAI API access
- Database connectivity
- Python dependencies

### 2. Configuration Migration
Copy your existing `.env` configuration:
```bash
cp /path/to/legacy/.env ./config/.env
```

### 3. Testing Compatibility
Run both systems side-by-side to compare results:
```bash
# Legacy system
cd /CODE/NL2DAX_PIPELINE/
python main.py

# Universal system  
cd /UNIVERSAL_NL2DAX_SYSTEM/
python interfaces/main_universal.py
```

### 4. Feature Mapping

| Legacy Component | Universal Equivalent | Notes |
|-----------------|---------------------|-------|
| `schema_reader.py` | `core/schema_agnostic_analyzer.py` | Enhanced with AI discovery |
| `dax_generator.py` | `core/generic_dax_generator.py` | Database-agnostic patterns |
| `sql_generator.py` | `core/generic_sql_generator.py` | Universal SQL generation |
| `main.py` | `interfaces/main_universal.py` | Unified interface |
| `streamlit_ui.py` | `interfaces/streamlit_universal_ui.py` | Enhanced visualizations |

## Backward Compatibility

### Execution Modules
The universal system still requires these legacy modules for query execution:
- `sql_executor.py` - For executing SQL queries
- `query_executor.py` - For executing DAX queries

These modules are automatically imported when available.

### Data Formats
- Query results maintain the same structure
- Output file formats remain compatible
- API interfaces preserve existing contracts

## Deprecation Timeline

### Phase 1: Parallel Operation (Current)
- Both systems operational
- Universal system recommended for new deployments
- Legacy system maintained for existing users

### Phase 2: Migration Period (Future)
- Active migration support
- Feature parity verification
- User training and documentation

### Phase 3: Legacy Retirement (Future)
- Legacy system marked as deprecated
- Universal system becomes primary
- Legacy code archived

## Support and Troubleshooting

### Common Migration Issues

**Issue: Schema reader dependency**
```python
# Legacy import
from schema_reader import get_schema_metadata

# Universal equivalent
from core.schema_agnostic_analyzer import SchemaAgnosticAnalyzer
analyzer = SchemaAgnosticAnalyzer()
schema_info = analyzer.analyze_schema_structure()
```

**Issue: Query generation interface**
```python
# Legacy approach
from dax_generator import generate_dax_query
result = generate_dax_query(user_input, schema_info)

# Universal approach
from core.universal_query_interface import UniversalQueryInterface, QueryType
interface = UniversalQueryInterface()
result = interface.generate_query_from_intent(user_input, QueryType.DAX)
```

### Performance Comparison
- Universal system: ~2-3 seconds for schema discovery
- Legacy system: ~1 second with hardcoded schema
- Universal system: Better query quality through AI analysis
- Legacy system: Faster but limited to specific schemas

### Feature Gaps
Features available in legacy but not yet in universal:
- None identified - universal system is feature-complete

Features available in universal but not in legacy:
- Automatic schema discovery
- Business concept identification
- Database-agnostic operation
- AI-powered query suggestions
- Enhanced error handling

## Migration Best Practices

### 1. Gradual Migration
- Start with test/development environments
- Run parallel systems during transition
- Validate query quality and performance
- Train users on new interface

### 2. Data Validation
- Compare query results between systems
- Verify schema discovery accuracy
- Test with representative user queries
- Validate visualization outputs

### 3. User Training
- Demonstrate new capabilities
- Highlight improved features
- Provide migration guides
- Support during transition

## Legacy Code Archive

When ready to retire legacy system:
1. Archive legacy code in `legacy_archive/` directory
2. Document final version and dependencies
3. Preserve configuration examples
4. Maintain access for reference

## Contact and Support

For migration assistance:
- Review universal system documentation
- Test with demo scripts
- Compare outputs with legacy system
- Report any compatibility issues

The universal system is designed to be a drop-in replacement with enhanced capabilities while maintaining compatibility with existing workflows.