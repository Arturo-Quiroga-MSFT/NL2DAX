# NL2DAX Streamlit Web Interface

## Overview

A modern web-based interface for the NL2DAX pipeline that allows users to input natural language queries and view both SQL and DAX results in a side-by-side comparison format.

## Features

- 🔍 **Natural Language Query Input**: Simple text interface for entering queries
- 📊 **Side-by-Side Results**: Compare SQL and DAX query results 
- ⚡ **Real-time Execution**: Live query processing with progress indicators
- 📥 **Export Capabilities**: Download results as CSV files
- 📈 **Performance Metrics**: View execution times and row counts
- 🕒 **Query History**: Access to recent queries
- 💡 **Example Queries**: Pre-built query templates
- 🎨 **Modern UI**: Clean, responsive interface

## Quick Start

### Option 1: Using the Launcher Script (Recommended)
```bash
cd /Users/arturoquiroga/GITHUB/NL2DAX/CODE/NL2DAX_PIPELINE
python launch_streamlit.py
```

### Option 2: Direct Streamlit Launch
```bash
cd /Users/arturoquiroga/GITHUB/NL2DAX/CODE/NL2DAX_PIPELINE
streamlit run streamlit_ui.py
```

The application will open in your browser at: http://localhost:8501

## Environment Setup

Ensure your `.env` file contains all required variables:
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `SQL_SERVER_CONNECTION_STRING`
- `POWERBI_WORKSPACE_ID`
- `POWERBI_DATASET_ID`
- Additional Azure and Power BI authentication variables

## Interface Overview

### Main Query Interface
1. **Query Input**: Large text area for natural language queries
2. **Execute Button**: Runs the complete NL2DAX pipeline
3. **Clear Button**: Resets the interface

### Results Dashboard
- **Results Comparison Tab**: Side-by-side SQL vs DAX results with download buttons
- **Query Details Tab**: Shows generated SQL/DAX code and parsed intent/entities
- **Analysis Tab**: Basic data overview and visualization

### Sidebar
- **Query Examples**: Click-to-use example queries
- **Recent Queries**: History of your recent queries

## Example Queries

Try these example queries to get started:

```
Show me the top 5 customers by total credit amount
```

```
What is the average risk rating by customer type?
```

```
List customers with the highest exposure at default
```

```
Show me comprehensive customer analysis grouped by type
```

```
Which customers are located in the United States?
```

## Architecture

The Streamlit UI integrates seamlessly with your existing NL2DAX pipeline:

```
User Input → Intent Parsing → SQL Generation → DAX Generation → Execution → Results Display
     ↓              ↓               ↓              ↓             ↓            ↓
Streamlit UI → main.py → SQL Module → DAX Module → Executors → UI Display
```

## Files

- `streamlit_ui.py` - Main Streamlit application
- `streamlit_config.py` - Configuration and utility functions
- `launch_streamlit.py` - Application launcher with dependency checking
- `README_STREAMLIT.md` - This documentation

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables Not Set**
   - Check that your `.env` file exists and contains all required variables
   - Verify file is in the correct directory

3. **Port Already in Use**
   ```bash
   streamlit run streamlit_ui.py --server.port 8502
   ```

4. **Import Errors**
   - Ensure you're running from the correct directory
   - Check that all pipeline modules are in the same directory

### Debug Mode

Run with debug logging:
```bash
streamlit run streamlit_ui.py --logger.level debug
```

## Development

### Adding New Features

The UI is modular and extensible:

- Add new query examples in `streamlit_config.py`
- Customize styling in the `CUSTOM_CSS` section
- Add new visualization components in the Analysis tab
- Extend the sidebar with additional tools

### Custom Styling

Modify the `CUSTOM_CSS` in `streamlit_config.py` to customize the appearance.

## Performance

- Queries are cached to improve response times
- Results are stored in session state for quick access
- Progress indicators show real-time execution status
- Execution times are tracked and displayed

## Security

- Environment variables are used for sensitive configuration
- No credentials are exposed in the UI
- All authentication is handled by the existing pipeline modules
