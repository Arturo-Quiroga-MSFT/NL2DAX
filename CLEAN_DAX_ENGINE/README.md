# Clean DAX Engine

A focused, clean implementation of DAX query generation, validation, and execution.

## Architecture

```
CLEAN_DAX_ENGINE/
├── core/
│   ├── schema_manager.py      # Schema caching and management
│   ├── dax_generator.py       # Clean DAX generation with best practices
│   ├── dax_validator.py       # DAX syntax and schema validation
│   └── dax_executor.py        # Power BI execution engine
├── config/
│   └── settings.py            # Configuration management
├── tests/
│   └── test_dax_engine.py     # Test suite
└── main.py                    # Demo and testing interface

```

## Design Principles

1. **Schema-First**: Always validate against actual schema before generation
2. **Best Practices**: Embedded DAX patterns proven to work
3. **Clean Separation**: Each component has single responsibility
4. **Fail Fast**: Validate early, execute only validated queries
5. **Testable**: Every component is unit testable

## Features

- ✅ Schema caching with validation
- ✅ DAX generation following proven patterns
- ✅ Multi-level validation (syntax, schema, best practices)
- ✅ Power BI execution with error handling
- ✅ Comprehensive logging and debugging