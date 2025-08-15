# NL2DAX Project - Reorganized Code Structure

This directory has been reorganized for better maintainability, clearer separation of concerns, and easier navigation. Each subdirectory contains focused functionality with detailed documentation.

## Directory Structure

```
CODE/
├── NL2DAX_PIPELINE/              # 🎯 Main Pipeline & Core Dependencies
├── DATABASE_SETUP/               # 🛠️ Database Setup & Configuration
├── DIAGNOSTICS_TROUBLESHOOTING/  # 🔍 Diagnostic & Troubleshooting Tools
├── LEGACY_EXAMPLES/              # 📚 Examples & Reference Implementations
└── SHARED/                       # 🔧 Shared Resources & Configuration
```

## Quick Start Guide

### 1. Set Up the Main Pipeline
```bash
cd NL2DAX_PIPELINE/
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python main.py
```

### 2. Configure Your Environment
```bash
cd DATABASE_SETUP/
python db_connection_check.py
# Follow setup scripts as needed
```

### 3. Run Diagnostics (if needed)
```bash
cd DIAGNOSTICS_TROUBLESHOOTING/
python status_report_aug14.py
python smoke_test_xmla.py
```

## Directory Details

### 🎯 [NL2DAX_PIPELINE/](./NL2DAX_PIPELINE/)
**Core natural language to DAX/SQL pipeline**
- Main entry point (`main.py`)
- Query generation and execution modules
- All essential dependencies for the pipeline
- Complete environment configuration
- **Start here for main functionality**

### 🛠️ [DATABASE_SETUP/](./DATABASE_SETUP/)
**Database and service principal configuration**
- Service principal setup scripts
- Database connection validation
- Power BI workspace configuration
- Security group management
- **Use for initial environment setup**

### 🔍 [DIAGNOSTICS_TROUBLESHOOTING/](./DIAGNOSTICS_TROUBLESHOOTING/)
**Comprehensive diagnostic and troubleshooting tools**
- System health checks and status reports
- Permission and authentication diagnostics
- Fabric mirrored database troubleshooting
- Performance analysis and optimization
- **Use when issues arise or for monitoring**

### 📚 [LEGACY_EXAMPLES/](./LEGACY_EXAMPLES/)
**Reference implementations and examples**
- Historical implementations and approaches
- Comparison scripts and analysis tools
- Educational examples and proof-of-concepts
- **Use for learning and reference**

### 🔧 [SHARED/](./SHARED/)
**Common resources and configuration**
- Git configuration and ignore patterns
- Export directory for generated files
- Shared utilities and templates
- **Supporting infrastructure**

## Migration Benefits

### ✅ **Improved Organization**
- Clear separation of production vs diagnostic code
- Easy to find relevant scripts for specific tasks
- Reduced cognitive load when navigating codebase

### ✅ **Better Maintenance**
- Core pipeline isolated from troubleshooting code
- Independent dependency management per component
- Easier testing and deployment of main pipeline

### ✅ **Enhanced Development Experience**
- Focused development environments
- Clear documentation for each component
- Easier onboarding for new developers

### ✅ **Operational Excellence**
- Diagnostic tools organized by function
- Clear separation of setup vs runtime components
- Better change management and version control

## Common Workflows

### Development Workflow
1. Work primarily in `NL2DAX_PIPELINE/`
2. Use `DIAGNOSTICS_TROUBLESHOOTING/` when issues arise
3. Reference `LEGACY_EXAMPLES/` for implementation patterns
4. Update `DATABASE_SETUP/` for environment changes

### Troubleshooting Workflow
1. Start with status reports in `DIAGNOSTICS_TROUBLESHOOTING/`
2. Use specific diagnostic tools based on error type
3. Apply fixes using appropriate fix scripts
4. Validate with pipeline tests in `NL2DAX_PIPELINE/`

### New Environment Setup
1. Follow setup guides in `DATABASE_SETUP/`
2. Configure pipeline in `NL2DAX_PIPELINE/`
3. Validate with diagnostics in `DIAGNOSTICS_TROUBLESHOOTING/`
4. Reference examples in `LEGACY_EXAMPLES/` as needed

## Environment Variables

Each component may require different environment variables. Check the README in each directory for specific requirements. Common variables include:

```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment

# Power BI
PBI_TENANT_ID=your_tenant_id
PBI_CLIENT_ID=your_client_id
PBI_CLIENT_SECRET=your_client_secret
PBI_XMLA_ENDPOINT=your_xmla_endpoint
PBI_DATASET_NAME=your_dataset_name

# Azure SQL
AZURE_SQL_SERVER=your_server
AZURE_SQL_DB=your_database
AZURE_SQL_USER=your_username
AZURE_SQL_PASSWORD=your_password
```

## Support and Documentation

- Each directory contains detailed README.md with component-specific information
- Main pipeline documentation in `NL2DAX_PIPELINE/README.md`
- Troubleshooting guides in `DIAGNOSTICS_TROUBLESHOOTING/README.md`
- Setup instructions in `DATABASE_SETUP/README.md`

## Contributing

When adding new functionality:
1. **Core Pipeline Features**: Add to `NL2DAX_PIPELINE/`
2. **Setup/Configuration**: Add to `DATABASE_SETUP/`
3. **Diagnostic Tools**: Add to `DIAGNOSTICS_TROUBLESHOOTING/`
4. **Examples/Demos**: Add to `LEGACY_EXAMPLES/`
5. **Shared Resources**: Add to `SHARED/`

Follow the existing patterns and update documentation accordingly.

---

## Original File Organization

The original flat structure has been preserved in the respective directories. If you need to reference the old structure or migrate additional files, all original files remain accessible in their new organized locations.

**Migration Date**: August 14, 2025
**Reorganization Completed**: ✅
**Documentation Status**: Complete with comprehensive README files for each directory
