from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from schema_reader import get_schema_metadata

load_dotenv()

API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

llm = AzureChatOpenAI(
    openai_api_key=API_KEY,
    azure_endpoint=ENDPOINT,
    deployment_name=DEPLOYMENT_NAME,
    api_version="2024-12-01-preview"
)


def get_schema_context():
    # Load schema from cache if available to avoid live DB calls
    cache_file = Path(__file__).parent / 'schema_cache.json'
    if cache_file.exists():
        try:
            metadata = json.loads(cache_file.read_text())
            print("[INFO] Loaded schema metadata from cache for DAX generation.")
        except Exception:
            metadata = get_schema_metadata()
    else:
        metadata = get_schema_metadata()
    tables = metadata["tables"]
    relationships = metadata["relationships"]
    schema_str = "Tables and Columns:\n"
    for table, columns in tables.items():
        schema_str += f"- {table}: {', '.join(columns)}\n"
    schema_str += "Relationships:\n"
    for rel in relationships:
        schema_str += f"- {rel['parent_table']}.{rel['parent_column']} -> {rel['referenced_table']}.{rel['referenced_column']} (FK: {rel['fk_name']})\n"
    return schema_str

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
    schema = get_schema_context()
    chain = dax_prompt | llm
    result = chain.invoke({"schema": schema, "intent_entities": intent_entities})
    return result.content
