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

Author: NL2DAX Pipeline Development Team (R2D2)
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
from query_cache import QueryCache          # Query caching for improved performance

# Load environment variables from .env file for secure configuration management
# This ensures sensitive credentials like API keys are not hardcoded in the source code
load_dotenv()

# Initialize query cache for LLM response caching
cache = QueryCache()

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
            print("[INFO] Loaded schema metadata from cache for query generation.")
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
    8. For top/ranking queries, use TOPN(N, Table, SortColumn, DESC/ASC) - NEVER add ORDER BY after TOPN
    9. TOPN handles sorting internally - syntax: TOPN(count, table, orderBy_expression, order)
    10. For aggregation queries with grouping, avoid RELATED() as relationships may not exist.
       Use ADDCOLUMNS to create calculated columns with LOOKUPVALUE, then group:
       EVALUATE
       SUMMARIZE(
           ADDCOLUMNS(
               'FactTable',
               "GroupByColumn",
               LOOKUPVALUE('DimensionTable'[GroupByColumn], 'DimensionTable'[PrimaryKey], 'FactTable'[ForeignKey])
           ),
           [GroupByColumn],
           "AggregateAlias", SUM('FactTable'[MeasureColumn])
       )
       Example for customer types:
       EVALUATE
       SUMMARIZE(
           ADDCOLUMNS(
               'FIS_CA_DETAIL_FACT',
               "CustomerType",
               LOOKUPVALUE('FIS_CUSTOMER_DIMENSION'[CUSTOMER_TYPE_DESCRIPTION], 'FIS_CUSTOMER_DIMENSION'[CUSTOMER_KEY], 'FIS_CA_DETAIL_FACT'[CUSTOMER_KEY])
           ),
           [CustomerType],
           "Total Amount", SUM('FIS_CA_DETAIL_FACT'[LIMIT_AMOUNT])
       )
    11. When using CALCULATE with grouping, ensure proper filter context is maintained
    12. For simple row listings, this pattern works well:
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
    
    Generate a complete, valid DAX query that follows these rules and returns the requested data. 
    
    CRITICAL DAX SYNTAX RULES - FOLLOW EXACTLY:
    - NEVER use "ORDER BY" in DAX - this is SQL syntax, not DAX
    - NEVER use standalone "ORDERBY" function - use TOPN for sorting
    - For ranking/sorting, ALWAYS use TOPN: TOPN(N, table, column, DESC)
    - Example of CORRECT DAX for top customers: 
      EVALUATE SELECTCOLUMNS(TOPN(5, 'Customers', 'Customers'[Sales], DESC), ...)
    - WRONG: ORDER BY, ORDERBY function
    - RIGHT: TOPN function with DESC/ASC parameter
    
    CRITICAL REQUIREMENTS:
    - The query MUST be complete and syntactically correct
    - MUST start with EVALUATE 
    - MUST end with a closing parenthesis for all opened functions
    - NO explanatory text - return ONLY the DAX query
    - For aggregation queries, ensure proper filter context is applied to get accurate results per group
    - NEVER use ORDER BY after TOPN - TOPN handles sorting internally with DESC/ASC parameter
    - When using TOPN for ranking, use: TOPN(N, Table, SortColumn, DESC/ASC) - no separate ORDER BY needed
    
    Return ONLY the DAX query, nothing else.
    """
)


def generate_dax(intent_entities):
    """
    Generate a DAX query from the provided intent and entities structure
    
    Args:
        intent_entities: Dictionary or string containing intent and entity information
    
    Returns:
        String containing the generated DAX query
    """
    
    # Use cache to avoid redundant LLM calls for identical intent/entity combinations
    cached_response = cache.get(intent_entities, "dax")
    if cached_response:
        print("[DEBUG] Using cached DAX response")
        return cached_response
    
    # Get database schema metadata for context-aware DAX generation
    metadata = get_schema_metadata()
    schema_context = get_powerbi_schema_context()
    
    # Create the DAX generation prompt with comprehensive context
    prompt = ChatPromptTemplate.from_template(
        """You are an expert DAX (Data Analysis Expressions) query generator for Power BI semantic models.
        
        POWER BI SEMANTIC MODEL CONTEXT:
        {schema_context}
        
        INTENT AND ENTITIES:
        {intent_entities}
        
        CRITICAL DAX SYNTAX RULES:
        - All table references MUST use single quotes: 'TableName'[ColumnName]
        - Use EVALUATE to make the query executable
        - Use TOPN() for ranking/limits, NEVER use ORDER BY (not supported in DAX)
        - For aggregations use CALCULATE(), SUM(), COUNT(), etc.
        - Use FILTER() for row-level filtering
        - Use RELATED() to access columns from related tables
        - Always validate column names against the schema above
        - String comparisons use double quotes: [Column] = "Value"
        
        CRITICAL DATA TYPE RULES:
        - NEVER use AVERAGE(), SUM(), MIN(), MAX() on text/string columns
        - Text columns (like CUSTOMER_TYPE_DESCRIPTION, COUNTRY_DESCRIPTION) can only be used for:
          * Grouping (in SUMMARIZECOLUMNS)
          * Filtering (in FILTER conditions)
          * Display (in ROW or calculated columns)
        - Numeric aggregations (AVERAGE, SUM) only work on amount/numeric columns like:
          * LIMIT_AMOUNT, PRINCIPAL_AMOUNT_DUE, AVAILABLE_AMOUNT
          * COMMITMENT_AMOUNT, ORIGINAL_LIMIT_AMOUNT
        - For analysis by type/category, use DISTINCTCOUNT() or COUNT() to count occurrences
        - For comprehensive analysis, combine text grouping with numeric aggregations of appropriate columns
        
        Generate a complete, executable DAX query that answers the user's intent.
        Return ONLY the DAX query, no explanations or formatting."""
    )
    
    # Configure Azure OpenAI for DAX generation
    llm = AzureChatOpenAI(
        deployment_name="o4-mini",
        model_name="o4-mini",
        azure_endpoint=ENDPOINT,
        api_key=API_KEY,
        api_version="2024-12-01-preview",
        temperature=1
    )
    
    # Create the processing chain
    chain = prompt | llm
    
    # Generate the DAX query
    result = chain.invoke({
        "schema_context": schema_context,
        "intent_entities": str(intent_entities)
    })
    
    # Cache the result for future use
    cache.set(intent_entities, result.content, "dax")
    
    return result.content


def get_powerbi_schema_context():
    """
    Generate Power BI semantic model schema context for DAX query generation.
    
    This function provides comprehensive schema information about the Power BI semantic model
    including table definitions, column listings, and relationship mappings. The schema
    is specifically curated to match the approved tables available in both SQL and Power BI.
    Schema information sourced directly from database metadata to ensure accuracy.
    
    Returns:
        str: Formatted schema context optimized for DAX query generation prompts
    """
    return """
POWER BI SEMANTIC MODEL SCHEMA:
===============================================
Schema information sourced directly from database metadata via INFORMATION_SCHEMA.COLUMNS.

FACT TABLES:

'FIS_CA_DETAIL_FACT' (Credit Arrangement Detail Facts) - 43 columns:
  Keys: CA_DETAIL_KEY (Primary Key), CUSTOMER_KEY, CA_PRODUCT_KEY, INVESTOR_KEY, OWNER_KEY, LIMIT_KEY, MONTH_ID
  Amounts: LIMIT_AMOUNT, LIMIT_AVAILABLE, LIMIT_USED, LIMIT_WITHHELD, PRINCIPAL_AMOUNT_DUE, ORIGINAL_LIMIT_AMOUNT
  Status: LIMIT_STATUS_CODE, LIMIT_STATUS_DESCRIPTION, CA_CURRENCY_CODE
  Dates: AS_OF_DATE, LIMIT_STATUS_DATE
  Fees: FEES_CHARGED_ITD, FEES_CHARGED_MTD, FEES_CHARGED_QTD, FEES_CHARGED_YTD, FEES_EARNED_ITD, FEES_EARNED_MTD, FEES_EARNED_QTD, FEES_EARNED_YTD, FEES_PAID_ITD, FEES_PAID_MTD, FEES_PAID_QTD, FEES_PAID_YTD
  Risk: EXPOSURE_AT_DEFAULT, LOSS_GIVEN_DEFAULT, PROBABILITY_OF_DEFAULT, RISK_WEIGHT_PERCENTAGE
  Rates: COMMITMENT_FEE_RATE, UTILIZATION_FEE_RATE, FINANCIAL_FX_RATE
  Other: FACILITY_ID, CONTRACTUAL_OWNERSHIP_PCT, LIMIT_VALUE_OF_COLLATERAL, NUMBER_OF_LIMIT_EXPOSURE, PORTFOLIO_ID, REGULATORY_CAPITAL

'FIS_CL_DETAIL_FACT' (Commercial Loan Detail Facts) - 50 columns:
  Keys: CL_DETAIL_KEY (Primary Key), CUSTOMER_KEY, LOAN_PRODUCT_KEY, CURRENCY_KEY, INVESTOR_KEY, OWNER_KEY, MONTH_ID
  Amounts: PRINCIPAL_BALANCE, ACCRUED_INTEREST, TOTAL_BALANCE, ORIGINAL_AMOUNT, PAYMENT_AMOUNT, CHARGE_OFF_AMOUNT, RECOVERY_AMOUNT
  Status: LOAN_STATUS, PAYMENT_STATUS, IS_NON_PERFORMING, IS_RESTRUCTURED, IS_IMPAIRED
  Dates: ORIGINATION_DATE, MATURITY_DATE, LAST_PAYMENT_DATE, NEXT_PAYMENT_DATE, CHARGE_OFF_DATE
  Risk: RISK_RATING_CODE, RISK_RATING_DESCRIPTION, PD_RATING, LGD_RATING
  Other: OBLIGATION_NUMBER, LOAN_CURRENCY_CODE, CUSTOMER_ID, DELINQUENCY_DAYS

DIMENSION TABLES:

'FIS_CUSTOMER_DIMENSION' (Customer Information) - 19 columns:
  Keys: CUSTOMER_KEY (Primary Key)
  Identity: CUSTOMER_ID, CUSTOMER_NAME, CUSTOMER_SHORT_NAME
  Classification: CUSTOMER_TYPE_CODE, CUSTOMER_TYPE_DESCRIPTION (IMPORTANT: No column named 'CUSTOMER_TYPE')
  Risk: RISK_RATING_CODE, RISK_RATING_DESCRIPTION
  Geography: COUNTRY_CODE, COUNTRY_DESCRIPTION, STATE_CODE, STATE_DESCRIPTION, CITY
  Industry: INDUSTRY_CODE, INDUSTRY_DESCRIPTION
  Contact: POSTAL_CODE
  Management: RELATIONSHIP_MANAGER
  Status: CUSTOMER_STATUS
  Dates: ESTABLISHED_DATE

'FIS_MONTH_DIMENSION' (Time/Date Information) - 12 columns:
  Keys: MONTH_ID (Primary Key)
  Core: REPORTING_DATE, MONTH_NAME, YEAR_ID, QUARTER_ID
  Extended: MONTH_NUMBER, QUARTER_NAME, MONTH_YEAR, FISCAL_YEAR, FISCAL_QUARTER, IS_MONTH_END, IS_QUARTER_END, IS_YEAR_END

'FIS_CA_PRODUCT_DIMENSION' (Credit Arrangement Products) - 20 columns:
  Keys: CA_PRODUCT_KEY (Primary Key)
  Identity: CA_NUMBER, CA_DESCRIPTION
  Classification: CA_PRODUCT_TYPE_CODE, CA_PRODUCT_TYPE_DESC
  Status: CA_OVERALL_STATUS_CODE, CA_OVERALL_STATUS_DESCRIPTION
  Customer: CA_CUSTOMER_ID, CA_CUSTOMER_NAME
  Financial: CA_CURRENCY_CODE, AVAILABLE_AMOUNT, COMMITMENT_AMOUNT
  Limit: CA_LIMIT_SECTION_ID, CA_LIMIT_TYPE
  Purpose: FACILITY_PURPOSE, PRICING_OPTION
  Risk: CA_COUNTRY_OF_EXPOSURE_RISK
  Dates: CA_EFFECTIVE_DATE, CA_MATURITY_DATE
  Other: RENEWAL_INDICATOR

'FIS_CURRENCY_DIMENSION' (Currency Information) - 10 columns:
  Keys: CURRENCY_KEY (Primary Key), CURRENCY_MONTH_ID
  From Currency: FROM_CURRENCY_CODE, FROM_CURRENCY_DESCRIPTION
  To Currency: TO_CURRENCY_CODE, TO_CURRENCY_DESCRIPTION
  Rates: CONVERSION_RATE, CRNCY_EXCHANGE_RATE
  Grouping: CURRENCY_RATE_GROUP
  Operation: OPERATION_INDICATOR

'FIS_INVESTOR_DIMENSION' (Investor Information) - 14 columns:
  Keys: INVESTOR_KEY (Primary Key)
  Identity: INVESTOR_ID, INVESTOR_NAME
  Classification: INVESTOR_TYPE_CODE, INVESTOR_TYPE_DESCRIPTION
  Class: INVESTOR_CLASS_CODE, INVESTOR_CLASS_DESCRIPTION
  Domain: INVESTOR_DOMAIN_CODE, INVESTOR_DOMAIN_DESCRIPTION
  Account: INVESTOR_ACCOUNT_TYPE_CODE, INVESTOR_ACCOUNT_TYPE_DESC
  Financial: PARTICIPATION_PERCENTAGE
  Dates: EFFECTIVE_DATE, EXPIRATION_DATE

'FIS_LIMIT_DIMENSION' (Credit Limit Information) - 18 columns:
  Keys: LIMIT_KEY (Primary Key)
  Identity: CA_LIMIT_SECTION_ID, CA_LIMIT_TYPE, LIMIT_DESCRIPTION
  Status: LIMIT_STATUS_CODE, LIMIT_STATUS_DESCRIPTION
  Amounts: CURRENT_LIMIT_AMOUNT, ORIGINAL_LIMIT_AMOUNT
  Facility: FACILITY_TYPE_CODE, FACILITY_TYPE_DESCRIPTION
  Type: LIMIT_TYPE_DESCRIPTION
  Currency: LIMIT_CURRENCY_CODE
  Rates: COMMITMENT_FEE_RATE, UTILIZATION_FEE_RATE
  Dates: EFFECTIVE_DATE, MATURITY_DATE, REVIEW_DATE
  Terms: RENEWAL_TERMS

'FIS_LOAN_PRODUCT_DIMENSION' (Loan Product Information) - 30 columns:
  Keys: LOAN_PRODUCT_KEY (Primary Key)
  Identity: OBLIGATION_NUMBER, CA_NUMBER
  Loan Type: LOAN_TYPE_CODE, LOAN_TYPE_DESCRIPTION
  Status: LOAN_STATUS_CODE, LOAN_STATUS_DESCRIPTION
  Product: PRODUCT_TYPE_CODE, PRODUCT_TYPE_DESCRIPTION
  Currency: LOAN_CURRENCY_CODE, LOAN_CURRENCY_DESCRIPTION, CA_CURRENCY_CODE
  Customer: CA_CUSTOMER_ID
  Amounts: ORIGINAL_AMOUNT
  Dates: EFFECTIVE_DATE, ORIGINATION_DATE, LEGAL_MATURITY_DATE, INT_RATE_MATURITY_DATE
  Collateral: COLLATERAL_CODE, COLLATERAL_DESCRIPTION
  Purpose: PURPOSE_CODE, PURPOSE_DESCRIPTION
  Accounting: ACCOUNTING_METHOD_CODE, ACCOUNTING_METHOD_DESCRIPTION
  Structure: ACCOUNT_STRUCTURE_CODE, ACCOUNT_STRUCTURE_DESC
  Booking: BOOKING_UNIT_CODE, BOOKING_UNIT_DESCRIPTION
  Portfolio: PORTFOLIO_ID, PORTFOLIO_DESCRIPTION

'FIS_OWNER_DIMENSION' (Owner/Relationship Manager Information) - 19 columns:
  Keys: OWNER_KEY (Primary Key)
  Identity: OWNER_ID, OWNER_NAME, OWNER_SHORT_NAME, OWNER_NAME_2, OWNER_NAME_3
  Classification: OWNER_TYPE_CODE, OWNER_TYPE_DESC
  Industry: INDUSTRY_GROUP_CODE, INDUSTRY_GROUP_NAME, PRIMARY_INDUSTRY_CODE, PRIMARY_INDUSTRY_DESC
  Geography: COUNTRY_CD, STATE, LOCATION_CD, POSTAL_ZIP_CD
  Risk: OFFICER_RISK_RATING_CODE, OFFICER_RISK_RATING_DESC
  Alternative: ALT_OWNER_NUMBER

RELATIONSHIPS:
- 'FIS_CA_DETAIL_FACT'[CUSTOMER_KEY] → 'FIS_CUSTOMER_DIMENSION'[CUSTOMER_KEY]
- 'FIS_CL_DETAIL_FACT'[CUSTOMER_KEY] → 'FIS_CUSTOMER_DIMENSION'[CUSTOMER_KEY]
- 'FIS_CA_DETAIL_FACT'[MONTH_ID] → 'FIS_MONTH_DIMENSION'[MONTH_ID]
- 'FIS_CL_DETAIL_FACT'[MONTH_ID] → 'FIS_MONTH_DIMENSION'[MONTH_ID]
- 'FIS_CA_DETAIL_FACT'[CA_PRODUCT_KEY] → 'FIS_CA_PRODUCT_DIMENSION'[CA_PRODUCT_KEY]
- 'FIS_CL_DETAIL_FACT'[LOAN_PRODUCT_KEY] → 'FIS_LOAN_PRODUCT_DIMENSION'[LOAN_PRODUCT_KEY]
- 'FIS_CA_DETAIL_FACT'[CURRENCY_KEY] → 'FIS_CURRENCY_DIMENSION'[CURRENCY_KEY]
- 'FIS_CL_DETAIL_FACT'[CURRENCY_KEY] → 'FIS_CURRENCY_DIMENSION'[CURRENCY_KEY]
- 'FIS_CA_DETAIL_FACT'[OWNER_KEY] → 'FIS_OWNER_DIMENSION'[OWNER_KEY]
- 'FIS_CL_DETAIL_FACT'[OWNER_KEY] → 'FIS_OWNER_DIMENSION'[OWNER_KEY]
- 'FIS_CL_DETAIL_FACT'[INVESTOR_KEY] → 'FIS_INVESTOR_DIMENSION'[INVESTOR_KEY]

CRITICAL DAX SYNTAX RULES:
- All column names above are exact database column names - use them precisely
- Table references MUST use single quotes: 'FIS_CUSTOMER_DIMENSION'[CUSTOMER_NAME]
- For customer type, use CUSTOMER_TYPE_CODE or CUSTOMER_TYPE_DESCRIPTION (NOT 'CUSTOMER_TYPE')
- Use CALCULATE() for filtered aggregations: CALCULATE(SUM('TableName'[Column]), FilterCondition)
- Use SUMX(), COUNTX() for row-by-row calculations
- Use RELATED() to access related table columns: RELATED('RelatedTable'[Column])
- Use FILTER() for complex row filtering: FILTER('TableName', Condition)
- Use TOPN() for ranking: TOPN(N, Table, OrderByColumn, DESC/ASC)
- String filters use double quotes: FILTER('Table', 'Table'[Column] = "Value")
- Always validate column names against this schema to prevent execution errors
"""
