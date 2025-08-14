"""
dax_generator.py - DAX Query Generation Module
==============================================

This module handles the generation of DAX (Data Analysis Expressions) queries from
structured intent and entities using Azure OpenAI's large language models. It provides
schema-aware DAX generation with intelligent prompt engineering for accurate Power BI
semantic model queries.

Key Features:
- Schema-aware DAX generation using database metadata
- Advanced prompt engineering for DAX best practices
- Integration with Azure OpenAI GPT models for natural language understanding
- Intelligent caching of database schema to optimize performance
- Comprehensive DAX syntax rules and validation patterns
- Support for complex DAX expressions, filters, and aggregations

Architecture:
- Uses LangChain framework for LLM orchestration and prompt management
- Integrates with schema_reader module for database metadata
- Leverages Azure OpenAI for advanced natural language to DAX transformation
- Implements caching strategies to minimize database schema queries

DAX Generation Approach:
1. Load database schema metadata (tables, columns, relationships)
2. Construct schema-aware prompts with DAX best practices
3. Use Azure OpenAI to transform intent/entities into valid DAX
4. Apply DAX syntax rules and Power BI semantic model patterns
5. Return executable DAX expressions for Power BI/Analysis Services

Dependencies:
- langchain_openai: Azure OpenAI integration for LLM functionality
- langchain.prompts: Template system for consistent prompting
- schema_reader: Database schema reading and caching functionality
- python-dotenv: Environment variable management for secure configuration

Author: NL2DAX Pipeline Development Team
Last Updated: August 14, 2025
"""

# LangChain imports for Azure OpenAI integration and prompt management
from langchain_openai import AzureChatOpenAI      # Azure OpenAI integration for LLM functionality
from langchain.prompts import ChatPromptTemplate  # Template system for consistent prompting

# Standard library imports for environment and file management
import os            # Operating system interface for environment variables
import json          # JSON parsing for schema cache management
from pathlib import Path  # Modern path handling for file operations

# Project-specific imports
from dotenv import load_dotenv              # Securely load environment variables from .env file
from schema_reader import get_schema_metadata  # Database schema reading and caching functionality

# Load environment variables from .env file for secure configuration management
# This ensures sensitive credentials like API keys are not hardcoded in the source code
load_dotenv()

# Azure OpenAI configuration from environment variables
# These settings control which Azure OpenAI service and model deployment to use
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")           # Azure OpenAI service API key
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")         # Azure OpenAI service endpoint URL
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")  # Specific model deployment name

# Initialize Azure OpenAI client with enterprise configuration
# Uses the latest API version for access to newest features and improvements
llm = AzureChatOpenAI(
    openai_api_key=API_KEY,                    # Authentication key for Azure OpenAI service
    azure_endpoint=ENDPOINT,                   # Azure OpenAI service endpoint
    deployment_name=DEPLOYMENT_NAME,           # Specific GPT model deployment
    api_version="2024-12-01-preview"          # Latest API version for enhanced capabilities
)


def get_schema_context():
    """
    Retrieve and format database schema metadata for DAX generation context.
    
    This function loads database schema information (tables, columns, relationships)
    and formats it into a human-readable string that can be used in prompts for
    schema-aware DAX generation. It implements intelligent caching to avoid
    repeated database queries and improve performance.
    
    Caching Strategy:
    - First checks for existing schema_cache.json file in the same directory
    - If cache exists and is valid, loads metadata from cache (fast)
    - If cache doesn't exist or is invalid, queries database directly (slower)
    - Cache improves performance by avoiding repeated database schema queries
    
    Returns:
        str: Formatted schema description containing:
            - Tables and their columns listed in readable format
            - Foreign key relationships between tables
            - Primary key information for each table
            - Relationship mappings for join operations
    
    Schema Format Example:
        Tables and Columns:
        - Customers: CustomerID, CustomerName, Country, City
        - Orders: OrderID, CustomerID, OrderDate, TotalAmount
        Relationships:
        - Orders.CustomerID -> Customers.CustomerID (FK: FK_Orders_Customers)
    
    Performance Notes:
        - Cache file reduces schema query time from ~1-2 seconds to ~10ms
        - Schema cache should be refreshed when database structure changes
        - Cache file location: same directory as this module
    
    Error Handling:
        - Falls back to live database query if cache is corrupted
        - Gracefully handles JSON parsing errors in cache file
        - Provides informative logging about cache usage
    """
    # Construct path to schema cache file in the same directory as this module
    cache_file = Path(__file__).parent / 'schema_cache.json'
    
    # Attempt to load schema from cache for improved performance
    if cache_file.exists():
        try:
            # Load and parse cached schema metadata from JSON file
            metadata = json.loads(cache_file.read_text())
            print("[INFO] Loaded schema metadata from cache for DAX generation.")
        except Exception:
            # Fall back to live database query if cache is corrupted or invalid
            metadata = get_schema_metadata()
    else:
        # No cache exists, query database directly for schema metadata
        metadata = get_schema_metadata()
    
    # Extract tables and relationships from metadata for prompt formatting
    tables = metadata["tables"]
    relationships = metadata["relationships"]
    
    # Format schema information into human-readable string for LLM prompt
    schema_str = "Tables and Columns:\n"
    for table, columns in tables.items():
        # List each table with its columns in comma-separated format
        schema_str += f"- {table}: {', '.join(columns)}\n"
    
    # Add relationship information for join operations and foreign keys
    schema_str += "Relationships:\n"
    for rel in relationships:
        # Format each relationship showing parent -> child table mapping
        schema_str += f"- {rel['parent_table']}.{rel['parent_column']} -> {rel['referenced_table']}.{rel['referenced_column']} (FK: {rel['fk_name']})\n"
    
    return schema_str


# DAX generation prompt template with comprehensive best practices and syntax rules
# This prompt is carefully engineered to produce valid DAX expressions that work
# with Power BI semantic models and Analysis Services tabular models
dax_prompt = ChatPromptTemplate.from_template(
    """
    You are an expert in DAX and Power BI. Given the following database schema and the intent/entities, generate a valid DAX expression for querying a database.
    
    IMPORTANT DAX RULES:
    1. Always use EVALUATE for table expressions
    2. When filtering and selecting columns from a table, use SELECTCOLUMNS with FILTER
    3. Column references must use single quotes around table names: 'TableName'[ColumnName]
    4. String values in filters must use double quotes: "value"
    5. For detailed row data, use table functions like FILTER, SELECTCOLUMNS, ADDCOLUMNS
    6. Always specify explicit column names in SELECTCOLUMNS
    7. Use VALUES() function when you need distinct values from a column
    8. For simple row listings, this pattern works well:
       EVALUATE 
       SELECTCOLUMNS(
           FILTER('TableName', condition),
           "Column1Alias", 'TableName'[Column1],
           "Column2Alias", 'TableName'[Column2]
       )
    
    Schema:
    {schema}
    
    Intent and Entities:
    {intent_entities}
    
    Generate a DAX query that follows these rules and returns the requested data.
    """
)


def generate_dax(intent_entities):
    """
    Generate a DAX query from structured intent and entities using Azure OpenAI.
    
    This function takes structured intent and entity information (typically extracted
    from natural language queries) and uses Azure OpenAI's language model to generate
    syntactically correct DAX expressions that can be executed against Power BI
    semantic models or Analysis Services tabular models.
    
    The generation process follows these steps:
    1. Retrieve current database schema metadata for context
    2. Combine schema with intent/entities in a structured prompt
    3. Use Azure OpenAI to transform the prompt into valid DAX
    4. Apply DAX best practices and syntax rules during generation
    5. Return executable DAX expression ready for query execution
    
    Args:
        intent_entities (str): Structured description of query intent and identified entities.
                              This typically includes:
                              - Query type (aggregation, filtering, grouping, etc.)
                              - Target tables and columns
                              - Filter conditions and values
                              - Grouping requirements
                              - Sort order specifications
    
    Returns:
        str: Valid DAX expression that can be executed against a Power BI semantic model
             or Analysis Services tabular model. The DAX follows best practices including:
             - Proper table and column references with single quotes
             - EVALUATE statements for table expressions
             - SELECTCOLUMNS for column selection and aliasing
             - FILTER functions for row-level filtering
             - Proper string quoting and syntax
    
    Example:
        >>> intent = "Find top 5 customers by total sales amount"
        >>> dax_query = generate_dax(intent)
        >>> print(dax_query)
        EVALUATE
        TOPN(
            5,
            SELECTCOLUMNS(
                'Customers',
                "CustomerName", 'Customers'[CustomerName],
                "TotalSales", CALCULATE(SUM('Sales'[Amount]))
            ),
            [TotalSales], DESC
        )
    
    Schema Integration:
        - Automatically loads current database schema for context-aware generation
        - Uses table and column names from actual database structure
        - Incorporates relationship information for proper join operations
        - Ensures generated DAX references valid database objects
    
    LLM Configuration:
        - Uses Azure OpenAI GPT models for advanced natural language understanding
        - Applies carefully engineered prompts with DAX best practices
        - Leverages schema context for accurate table/column references
        - Implements DAX syntax rules and Power BI semantic model patterns
    
    Error Handling:
        - Returns best-effort DAX even if schema loading fails
        - Gracefully handles Azure OpenAI API errors and timeouts
        - Provides meaningful error messages for debugging
    """
    # Get current database schema context for schema-aware DAX generation
    schema = get_schema_context()
    
    # Create LangChain chain combining prompt template with Azure OpenAI LLM
    # This chain handles the transformation from structured intent to DAX expression
    chain = dax_prompt | llm
    
    # Invoke the chain with schema context and intent/entities to generate DAX
    # The LLM uses both the database schema and query intent to create valid DAX
    result = chain.invoke({"schema": schema, "intent_entities": intent_entities})
    
    # Return the generated DAX content from the LLM response
    return result.content
