print("[DEBUG] Script started")
import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dax_generator import generate_dax
from dax_formatter import format_and_validate_dax

from query_executor import execute_dax_query
from sql_executor import execute_sql_query

# NL2SQL prompt and function
from langchain.prompts import ChatPromptTemplate as SQLChatPromptTemplate

sql_prompt = SQLChatPromptTemplate.from_template(
    """
    You are an expert in SQL and Azure SQL DB. Given the following database schema and the intent/entities, generate a valid T-SQL query for querying the database.
    Schema:
    {schema}
    Intent and Entities:
    {intent_entities}
    """
)

def generate_sql(intent_entities):
    from dax_generator import get_schema_context
    schema = get_schema_context()
    chain = sql_prompt | llm
    result = chain.invoke({"schema": schema, "intent_entities": intent_entities})
    return result.content


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

prompt = ChatPromptTemplate.from_template(
    """
    You are an expert in translating natural language to database queries. Extract the intent and entities from the following user input:
    {input}
    """
)

def parse_nl_query(user_input):
    chain = prompt | llm
    result = chain.invoke({"input": user_input})
    return result.content

if __name__ == "__main__":
    import time
    start_time = time.time()
    print("[DEBUG] Starting NL2DAX pipeline...")
    query = input("Enter your natural language query: ")
    print(f"[DEBUG] User query: {query}")
    intent_entities = parse_nl_query(query)
    print("[DEBUG] Parsed intent/entities:")
    print(intent_entities)

    # Generate DAX
    dax = generate_dax(intent_entities)
    print("[DEBUG] Generated DAX expression:")
    print(dax)
    formatted_dax, _ = format_and_validate_dax(dax)
    print("[DEBUG] Formatted DAX:")
    print(formatted_dax)
    # Generate SQL
    sql = generate_sql(intent_entities)
    print("[DEBUG] Generated SQL query:")
    print(sql)

    # Extract only the SQL code from the generated output (remove explanations and code fences)
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
    sql_sanitized = sql_code.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')

    # Prepare output for .txt file
    output_lines = []
    banner = lambda title: f"\n{'='*10} {title} {'='*10}\n"

    # Print and record each section
    print(banner("NATURAL LANGUAGE QUERY"))
    print(query + "\n")
    output_lines.append(banner("NATURAL LANGUAGE QUERY"))
    output_lines.append(f"{query}\n")

    print(banner("GENERATED DAX"))
    print(dax + "\n")
    output_lines.append(banner("GENERATED DAX"))
    output_lines.append(f"{dax}\n")

    print(banner("FORMATTED DAX"))
    print(formatted_dax + "\n")
    output_lines.append(banner("FORMATTED DAX"))
    output_lines.append(f"{formatted_dax}\n")

    print(banner("GENERATED SQL"))
    print(sql + "\n")
    output_lines.append(banner("GENERATED SQL"))
    output_lines.append(f"{sql}\n")

    if sql != sql_sanitized:
        print(banner("SANITIZED SQL (FOR EXECUTION)"))
        print(sql_sanitized + "\n")
        output_lines.append(banner("SANITIZED SQL (FOR EXECUTION)"))
        output_lines.append(f"{sql_sanitized}\n")

    # --- DAX query execution is commented out ---
    # try:
    #     print("\n[DEBUG] Executing DAX query...")
    #     dax_results = execute_dax_query(dax)
    #     print("[DEBUG] DAX Query Results:")
    #     for row in dax_results:
    #         print(row)
    #     output_lines.append("DAX Query Results:\n" + "\n".join([str(row) for row in dax_results]) + "\n")
    # except RuntimeError as e:
    #     warn_msg = f"[WARN] Skipping DAX execution: {e}"
    #     print(warn_msg)
    #     print("Install Mono and pythonnet (`brew install mono`), then `pip install pyadomd pythonnet`.")
    #     output_lines.append(warn_msg + "\n")
    # except Exception as e:
    #     err_msg = f"[ERROR] Failed to execute DAX query: {e}"
    #     print(err_msg)
    #     output_lines.append(err_msg + "\n")

    # Execute the SQL query and show results in table format
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

    # Show and record run duration
    end_time = time.time()
    duration = end_time - start_time
    duration_str = f"Run duration: {duration:.2f} seconds"
    print(banner("RUN DURATION"))
    print(duration_str)
    output_lines.append(banner("RUN DURATION"))
    output_lines.append(duration_str + "\n")

    # Write output to .txt file
    from datetime import datetime
    safe_query = query.strip().replace(' ', '_')[:40]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_filename = f"nl2dax_run_{safe_query}_{timestamp}.txt"
    out_path = os.path.join(os.path.dirname(__file__), out_filename)
    with open(out_path, 'w') as f:
        f.writelines([line if line.endswith('\n') else line + '\n' for line in output_lines])
    print(f"[INFO] Run results written to {out_path}")
