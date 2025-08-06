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
    Schema:
    {schema}
    Intent and Entities:
    {intent_entities}
    """
)

def generate_dax(intent_entities):
    schema = get_schema_context()
    chain = dax_prompt | llm
    result = chain.invoke({"schema": schema, "intent_entities": intent_entities})
    return result.content
