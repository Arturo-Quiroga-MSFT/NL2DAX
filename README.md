
# NL2DAX & NL2SQL for Azure SQL DB

This project translates natural language queries into DAX or SQL for Azure SQL DB using LangChain and Azure OpenAI. It features schema awareness, robust error handling, and clear output formatting.


## Setup
- Configure your Azure OpenAI credentials and Azure SQL DB connection in `.env`.
- Install dependencies: `pip install -r requirements.txt`


## Features
- **NL2DAX**: Generate DAX queries from natural language.
- **NL2SQL**: Generate SQL queries from natural language.
- **SQL Execution**: Run generated SQL queries and display results as tables.
- **Schema Awareness**: Reads schema, relationships, and primary keys for accurate query generation.
- **Clear Output**: Results and sections are separated by ASCII banners for readability.
- **DAX Formatting**: Uses the public DAX Formatter API (no API key required).
- **Error Handling**: Robust error and exception handling throughout the pipeline.


## Usage

1. **Run the main pipeline:**
	 ```bash
	 python main.py
	 ```
	 - Input a natural language question. The system will generate DAX and SQL, execute SQL, and print results with clear banners.

2. **View schema summary:**
	 ```bash
	 python schema_reader.py
	 ```
	 - Prints a detailed summary of tables, columns, primary keys, and relationships.

3. **Update schema cache:**
	 ```bash
	 python schema_reader.py --cache
	 ```
	 - Refreshes the local schema cache from the database.

## DAX Formatter API

- The DAX Formatter API is used for formatting and validating DAX queries.
- **No API key is required.**
- If you receive HTTP 404 errors, the service may be temporarily unavailable or the endpoint may have changed. Check https://www.daxformatter.com/api/daxformatter/ in your browser to verify availability.

## Troubleshooting

- **DAX Formatter API errors:**
	- No API key is needed. If you get HTTP 404, check your internet connection and the DAX Formatter service status.
- **Azure SQL connection errors:**
	- Ensure your `.env` file is correctly configured with server, DB, user, and password.
- **Schema not updating:**
	- Run `python schema_reader.py --cache` to refresh the schema cache.

## License
MIT

# NL2DAX
Natural Language to DAX and SQL pipeline for Azure SQL DB with schema awareness, robust error handling, and clear output formatting.
