
"""
main.py - NL2DAX & NL2SQL Pipeline Entrypoint

This script demonstrates how to build an end-to-end natural language to DAX and SQL pipeline using LangChain, Azure OpenAI, and schema-aware prompt engineering.
It is heavily commented for educational purposes, showing best practices for intent extraction, query generation, validation, and result handling.
"""

# --- Imports and Setup ---
import os
from dotenv import load_dotenv  # For loading environment variables from .env
from langchain_openai import AzureChatOpenAI  # Azure OpenAI LLM integration
from langchain.prompts import ChatPromptTemplate  # For prompt templating
from dax_generator import generate_dax  # DAX generation logic
from dax_formatter import format_and_validate_dax  # DAX formatting/validation
from query_executor import execute_dax_query  # (Optional) DAX execution
from sql_executor import execute_sql_query  # SQL execution

print("[DEBUG] Script started")

# --- NL2SQL Prompt Setup ---
from langchain.prompts import ChatPromptTemplate as SQLChatPromptTemplate

# This prompt instructs the LLM to generate a valid T-SQL query given schema and intent/entities.
sql_prompt = SQLChatPromptTemplate.from_template(
    """
    You are an expert in SQL and Azure SQL DB. Given the following database schema and the intent/entities, generate a valid T-SQL query for querying the database.
    Schema:
    {schema}
    Intent and Entities:
    {intent_entities}
    """
)


# --- NL2SQL Generation Function ---
def generate_sql(intent_entities):
    """
    Given extracted intent/entities, generate a SQL query using the LLM and schema context.
    This demonstrates prompt chaining and schema-aware query generation.
    """
    from dax_generator import get_schema_context
    schema = get_schema_context()
    chain = sql_prompt | llm
    result = chain.invoke({"schema": schema, "intent_entities": intent_entities})
    return result.content



# --- Load Environment Variables ---
load_dotenv()



# --- Azure OpenAI Configuration ---
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")


# --- LLM Initialization ---
# This LLM is used for both intent extraction and query generation.
llm = AzureChatOpenAI(
    openai_api_key=API_KEY,
    azure_endpoint=ENDPOINT,
    deployment_name=DEPLOYMENT_NAME,
    api_version="2024-12-01-preview"
)


# --- NL2Intent Prompt Setup ---
# This prompt extracts intent and entities from user input for downstream query generation.
prompt = ChatPromptTemplate.from_template(
    """
    You are an expert in translating natural language to database queries. Extract the intent and entities from the following user input:
    {input}
    """
)


# --- NL2Intent Extraction Function ---
def parse_nl_query(user_input):
    """
    Use the LLM to extract intent and entities from a natural language query.
    This is the first step in the NL2SQL/NL2DAX pipeline.
    """
    chain = prompt | llm
    result = chain.invoke({"input": user_input})
    return result.content


# --- Main Pipeline Execution ---
if __name__ == "__main__":
    import time
    start_time = time.time()
    print("[DEBUG] Starting NL2DAX pipeline...")


    # --- Step 1: Get User Query ---
    # Accept a natural language question from the user.
    query = input("Enter your natural language query: ")
    print(f"[DEBUG] User query: {query}")

    # --- Step 2: Intent & Entity Extraction ---
    # Use the LLM to extract intent and entities from the user's question.
    intent_entities = parse_nl_query(query)
    print("[DEBUG] Parsed intent/entities:")
    print(intent_entities)

    # --- Step 3: SQL Generation ---
    # Generate a SQL query from the extracted intent/entities.
    sql = generate_sql(intent_entities)
    print("[DEBUG] Generated SQL query:")
    print(sql)

    # --- Step 4: SQL Code Extraction & Sanitization ---
    # Extract only the SQL code from the LLM output (removing explanations and code fences).
    import re
    sql_code = sql
    code_block = re.search(r"```sql\s*([\s\S]+?)```", sql, re.IGNORECASE)
    if not code_block:
        code_block = re.search(r"```([\s\S]+?)```", sql)
    if code_block:
        sql_code = code_block.group(1).strip()
    else:
        select_match = re.search(r'(SELECT[\s\S]+)', sql, re.IGNORECASE)
        if select_match:
            sql_code = select_match.group(1).strip()
    # Replace smart quotes with standard quotes for SQL execution.
    sql_sanitized = sql_code.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')

    # --- Step 5: Output Preparation ---
    # Prepare output for .txt file and for printing, using ASCII banners for clarity.
    output_lines = []
    banner = lambda title: f"\n{'='*10} {title} {'='*10}\n"

    # Print and record each section for both console and file output.
    print(banner("NATURAL LANGUAGE QUERY"))
    print(query + "\n")
    output_lines.append(banner("NATURAL LANGUAGE QUERY"))
    output_lines.append(f"{query}\n")

    print(banner("GENERATED SQL"))
    print(sql + "\n")
    output_lines.append(banner("GENERATED SQL"))
    output_lines.append(f"{sql}\n")

    if sql != sql_sanitized:
        print(banner("SANITIZED SQL (FOR EXECUTION)"))
        print(sql_sanitized + "\n")
        output_lines.append(banner("SANITIZED SQL (FOR EXECUTION)"))
        output_lines.append(f"{sql_sanitized}\n")

    # --- Step 6: SQL Query Execution & Table Output ---
    # Execute the sanitized SQL query and print results in a table format.
    try:
        print(banner("EXECUTING SQL QUERY"))
        sql_results = execute_sql_query(sql_sanitized)
        if sql_results:
            columns = sql_results[0].keys()
            col_widths = {col: max(len(col), max(len(str(row[col])) for row in sql_results)) for col in columns}
            header = " | ".join([col.ljust(col_widths[col]) for col in columns])
            sep = "-+-".join(['-' * col_widths[col] for col in columns])
            print(banner("SQL QUERY RESULTS (TABLE)"))
            print(header)
            print(sep)
            for row in sql_results:
                print(" | ".join([str(row[col]).ljust(col_widths[col]) for col in columns]))
            output_lines.append(banner("SQL QUERY RESULTS (TABLE)"))
            output_lines.append(header + "\n")
            output_lines.append(sep + "\n")
            for row in sql_results:
                output_lines.append(" | ".join([str(row[col]).ljust(col_widths[col]) for col in columns]) + "\n")
        else:
            print(banner("SQL QUERY RESULTS"))
            print("No results returned.")
            output_lines.append(banner("SQL QUERY RESULTS"))
            output_lines.append("No results returned.\n")
    except Exception as e:
        err_msg = f"[ERROR] Failed to execute SQL query: {e}"
        print(banner("SQL QUERY ERROR"))
        print(err_msg)
        output_lines.append(banner("SQL QUERY ERROR"))
        output_lines.append(err_msg + "\n")

    # --- Step 7: DAX Generation ---
    # Generate a DAX expression from the extracted intent/entities.
    dax = generate_dax(intent_entities)
    print("[DEBUG] Generated DAX expression:")
    print(dax)

    # --- Step 8: DAX Formatting & Validation ---
    # Format and validate the generated DAX using the DAX Formatter API.
    formatted_dax, _ = format_and_validate_dax(dax)
    print("[DEBUG] Formatted DAX:")
    print(formatted_dax)

    print(banner("GENERATED DAX"))
    print(dax + "\n")
    output_lines.append(banner("GENERATED DAX"))
    output_lines.append(f"{dax}\n")

    print(banner("FORMATTED DAX"))
    print(formatted_dax + "\n")
    output_lines.append(banner("FORMATTED DAX"))
    output_lines.append(f"{formatted_dax}\n")

    # --- Step 9: DAX Query Execution (macOS/Mono) ---
    # This will attempt to execute the generated DAX query using pyadomd and a Tabular XMLA endpoint.
    try:
        print(banner("EXECUTING DAX QUERY"))
        dax_results = execute_dax_query(dax)
        if dax_results:
            dax_columns = dax_results[0].keys()
            dax_col_widths = {col: max(len(col), max(len(str(row[col])) for row in dax_results)) for col in dax_columns}
            dax_header = " | ".join([col.ljust(dax_col_widths[col]) for col in dax_columns])
            dax_sep = "-+-".join(['-' * dax_col_widths[col] for col in dax_columns])
            print(banner("DAX QUERY RESULTS (TABLE)"))
            print(dax_header)
            print(dax_sep)
            for row in dax_results:
                print(" | ".join([str(row[col]).ljust(dax_col_widths[col]) for col in dax_columns]))
            output_lines.append(banner("DAX QUERY RESULTS (TABLE)"))
            output_lines.append(dax_header + "\n")
            output_lines.append(dax_sep + "\n")
            for row in dax_results:
                output_lines.append(" | ".join([str(row[col]).ljust(dax_col_widths[col]) for col in dax_columns]) + "\n")
        else:
            print(banner("DAX QUERY RESULTS"))
            print("No results returned.")
            output_lines.append(banner("DAX QUERY RESULTS"))
            output_lines.append("No results returned.\n")
    except RuntimeError as e:
        warn_msg = f"[WARN] Skipping DAX execution: {e}"
        print(banner("DAX EXECUTION WARNING"))
        print(warn_msg)
        print("Install Mono and pythonnet (`brew install mono`), then `pip install pyadomd pythonnet`.")
        output_lines.append(banner("DAX EXECUTION WARNING"))
        output_lines.append(warn_msg + "\n")
    except Exception as e:
        err_msg = f"[ERROR] Failed to execute DAX query: {e}"
        print(banner("DAX EXECUTION ERROR"))
        print(err_msg)
        output_lines.append(banner("DAX EXECUTION ERROR"))
        output_lines.append(err_msg + "\n")

    # --- Step 10: Show Run Duration ---
    # Print and record the total run duration for performance awareness.
    end_time = time.time()
    duration = end_time - start_time
    duration_str = f"Run duration: {duration:.2f} seconds"
    print(banner("RUN DURATION"))
    print(duration_str)
    output_lines.append(banner("RUN DURATION"))
    output_lines.append(duration_str + "\n")

    # --- Step 11: Write Output to File ---
    # Save all output sections to a timestamped .txt file for reproducibility and sharing.
    from datetime import datetime
    safe_query = query.strip().replace(' ', '_')[:40]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_filename = f"nl2dax_run_{safe_query}_{timestamp}.txt"
    out_path = os.path.join(os.path.dirname(__file__), out_filename)
    with open(out_path, 'w') as f:
        f.writelines([line if line.endswith('\n') else line + '\n' for line in output_lines])
    print(f"[INFO] Run results written to {out_path}")
