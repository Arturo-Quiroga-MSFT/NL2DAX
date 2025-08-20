"""
NL2DAX Pipeline: Natural Language to DAX Query Generation and Execution
This module provides a complete pipeline for converting natural language queries
to DAX expressions and executing them against Power BI semantic models.
"""

import re
import json
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables from .env file
load_dotenv()

# Note: In production, you'd import these from actual libraries
from sempy import fabric
from azure.identity import DefaultAzureCredential

class QueryType(Enum):
    MEASURE = "measure"
    FILTER = "filter"
    AGGREGATION = "aggregation"
    TIME_SERIES = "time_series"
    COMPARISON = "comparison"

@dataclass
class SemanticModel:
    """Represents a Power BI semantic model schema"""
    name: str
    tables: Dict[str, List[str]]  # table_name: [column_names]
    measures: List[str]
    relationships: List[Dict[str, str]]

@dataclass
class NLQuery:
    """Natural language query with context"""
    text: str
    query_type: Optional[QueryType] = None
    confidence: float = 0.0
    tables_mentioned: List[str] = None
    measures_mentioned: List[str] = None

@dataclass
class DAXQuery:
    """Generated DAX query with metadata"""
    dax_expression: str
    confidence: float
    query_type: QueryType
    validation_errors: List[str] = None
    execution_plan: Optional[str] = None

class DAXValidator:
    """Validates DAX syntax and semantic correctness"""
    
    def __init__(self, semantic_model: SemanticModel):
        self.model = semantic_model
        self.dax_functions = [
            'SUM', 'AVERAGE', 'COUNT', 'COUNTROWS', 'MIN', 'MAX',
            'CALCULATE', 'FILTER', 'ALL', 'ALLEXCEPT', 'VALUES',
            'SUMX', 'AVERAGEX', 'COUNTX', 'MINX', 'MAXX',
            'RELATED', 'RELATEDTABLE', 'LOOKUPVALUE',
            'DATEADD', 'DATEDIFF', 'YEAR', 'MONTH', 'DAY',
            'IF', 'SWITCH', 'AND', 'OR', 'NOT'
        ]
    
    def validate_syntax(self, dax_query: str) -> List[str]:
        """Basic DAX syntax validation"""
        errors = []
        
        # Check for basic structure
        if not dax_query.strip().upper().startswith('EVALUATE'):
            errors.append("DAX query must start with EVALUATE statement")
        
        # Check parentheses balance
        if dax_query.count('(') != dax_query.count(')'):
            errors.append("Unbalanced parentheses in DAX expression")
        
        # Check for common syntax errors
        if ',,,' in dax_query:
            errors.append("Multiple consecutive commas found")
        
        return errors
    
    def validate_semantic(self, dax_query: str) -> List[str]:
        """Validate against semantic model schema"""
        errors = []
        
        # Extract table and column references
        table_column_pattern = r"'?(\w+)'?\[(\w+)\]"
        matches = re.findall(table_column_pattern, dax_query)
        
        for table, column in matches:
            if table not in self.model.tables:
                errors.append(f"Table '{table}' not found in semantic model")
            elif column not in self.model.tables[table]:
                errors.append(f"Column '{column}' not found in table '{table}'")
        
        # Validate measure references
        measure_pattern = r"\[(\w+)\]"
        measure_matches = re.findall(measure_pattern, dax_query)
        
        for measure in measure_matches:
            if measure not in self.model.measures:
                # Could be a column, check if it exists in any table
                found = any(measure in cols for cols in self.model.tables.values())
                if not found:
                    errors.append(f"Measure or column '{measure}' not found")
        
        return errors
    
    def validate(self, dax_query: str) -> Tuple[bool, List[str]]:
        """Complete validation of DAX query"""
        all_errors = []
        all_errors.extend(self.validate_syntax(dax_query))
        all_errors.extend(self.validate_semantic(dax_query))
        
        return len(all_errors) == 0, all_errors

class NLQueryAnalyzer:
    """Analyzes natural language queries to extract intent and entities"""
    
    def __init__(self, semantic_model: SemanticModel):
        self.model = semantic_model
        self.query_patterns = {
            QueryType.MEASURE: [
                r'\b(total|sum|average|count|revenue|sales|profit)\b',
                r'\b(how much|what is the)\b'
            ],
            QueryType.FILTER: [
                r'\b(where|filter|only|exclude)\b',
                r'\b(in|for|during)\b'
            ],
            QueryType.TIME_SERIES: [
                r'\b(over time|by month|by year|trend|timeline)\b',
                r'\b(last|this|previous)\s+(month|year|quarter)\b'
            ],
            QueryType.COMPARISON: [
                r'\b(compare|vs|versus|difference|better|worse)\b',
                r'\b(top|bottom|highest|lowest)\b'
            ]
        }
    
    def extract_entities(self, query_text: str) -> Dict[str, List[str]]:
        """Extract table and measure names from query"""
        entities = {'tables': [], 'measures': []}
        query_lower = query_text.lower()
        
        # Find mentioned tables
        for table in self.model.tables.keys():
            if table.lower() in query_lower:
                entities['tables'].append(table)
        
        # Find mentioned measures
        for measure in self.model.measures:
            if measure.lower() in query_lower:
                entities['measures'].append(measure)
        
        return entities
    
    def classify_query(self, query_text: str) -> Tuple[QueryType, float]:
        """Classify the type of query based on patterns"""
        query_lower = query_text.lower()
        scores = {}
        
        for query_type, patterns in self.query_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query_lower))
                score += matches
            scores[query_type] = score
        
        if not any(scores.values()):
            return QueryType.MEASURE, 0.5  # Default assumption
        
        best_type = max(scores, key=scores.get)
        confidence = min(scores[best_type] / len(self.query_patterns[best_type]), 1.0)
        
        return best_type, confidence
    
    def analyze(self, query_text: str) -> NLQuery:
        """Complete analysis of natural language query"""
        query_type, confidence = self.classify_query(query_text)
        entities = self.extract_entities(query_text)
        
        return NLQuery(
            text=query_text,
            query_type=query_type,
            confidence=confidence,
            tables_mentioned=entities['tables'],
            measures_mentioned=entities['measures']
        )

class DAXGenerator:
    """Generates DAX queries from analyzed natural language queries"""
    
    def __init__(self, semantic_model: SemanticModel, azure_openai_client=None):
        self.model = semantic_model
        self.client = azure_openai_client
        self.templates = self._load_dax_templates()
    
    def _load_dax_templates(self) -> Dict[QueryType, str]:
        """Load DAX query templates for different query types"""
        return {
            QueryType.MEASURE: """
EVALUATE
SUMMARIZE(
    {table},
    {measure}
)
            """.strip(),
            
            QueryType.FILTER: """
EVALUATE
FILTER(
    {table},
    {condition}
)
            """.strip(),
            
            QueryType.AGGREGATION: """
EVALUATE
SUMMARIZE(
    {table},
    {group_by_columns},
    "{measure_name}", {aggregation}
)
            """.strip(),
            
            QueryType.TIME_SERIES: """
EVALUATE
SUMMARIZE(
    {table},
    {date_column},
    "{measure_name}", {measure}
)
ORDER BY {date_column}
            """.strip()
        }
    
    def _create_few_shot_prompt(self, nl_query: NLQuery) -> str:
        """Create a few-shot prompt for GPT with DAX examples"""
        schema_info = self._get_schema_context()
        
        prompt = f"""
You are an expert at converting natural language queries to DAX expressions for Power BI.

SEMANTIC MODEL SCHEMA:
{schema_info}

EXAMPLES:
Natural Language: "What is the total sales?"
DAX: EVALUATE {{ [Total Sales] }}

Natural Language: "Show sales by product category"
DAX: EVALUATE SUMMARIZE(Products, Products[Category], "Total Sales", [Total Sales])

Natural Language: "Filter customers where city is Seattle"
DAX: EVALUATE FILTER(Customers, Customers[City] = "Seattle")

Natural Language: "Sales trend by month"
DAX: EVALUATE SUMMARIZE(Sales, YEAR(Sales[Date]), MONTH(Sales[Date]), "Monthly Sales", [Total Sales])

QUERY TO CONVERT:
Natural Language: "{nl_query.text}"
Query Type: {nl_query.query_type.value if nl_query.query_type else 'unknown'}
Mentioned Tables: {nl_query.tables_mentioned or 'none'}
Mentioned Measures: {nl_query.measures_mentioned or 'none'}

Generate a DAX query that starts with EVALUATE. Be precise and use only tables/columns/measures that exist in the schema.

DAX:"""
        return prompt
    
    def _get_schema_context(self) -> str:
        """Generate schema context for the prompt"""
        schema_lines = []
        schema_lines.append("TABLES:")
        for table, columns in self.model.tables.items():
            schema_lines.append(f"  {table}: {', '.join(columns)}")
        
        schema_lines.append("\nMEASURES:")
        for measure in self.model.measures:
            schema_lines.append(f"  [{measure}]")
        
        return "\n".join(schema_lines)
    
    def generate_with_template(self, nl_query: NLQuery) -> DAXQuery:
        """Generate DAX using predefined templates"""
        template = self.templates.get(nl_query.query_type)
        if not template:
            template = self.templates[QueryType.MEASURE]
        
        # Simple template substitution (would be more sophisticated in practice)
        dax_expression = template
        if nl_query.tables_mentioned:
            dax_expression = dax_expression.replace('{table}', nl_query.tables_mentioned[0])
        if nl_query.measures_mentioned:
            dax_expression = dax_expression.replace('{measure}', f'[{nl_query.measures_mentioned[0]}]')
        
        return DAXQuery(
            dax_expression=dax_expression,
            confidence=0.7,
            query_type=nl_query.query_type or QueryType.MEASURE,
            validation_errors=[]
        )
    
    def generate_with_llm(self, nl_query: NLQuery) -> DAXQuery:
        """Generate DAX using Azure OpenAI GPT-5"""
        if not self.client:
            raise ValueError("Azure OpenAI client not configured")
        
        prompt = self._create_few_shot_prompt(nl_query)
        
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5"),  # GPT-5 deployment name
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert DAX developer for Power BI. Generate syntactically correct DAX queries that start with EVALUATE."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=800,
                top_p=0.9
            )
            
            dax_expression = response.choices[0].message.content.strip()
            
            # Extract DAX from response if needed
            if "DAX:" in dax_expression:
                dax_expression = dax_expression.split("DAX:")[-1].strip()
            
            # Clean up any markdown code blocks
            if "```" in dax_expression:
                dax_expression = re.sub(r'```[\w]*\n?', '', dax_expression)
                dax_expression = dax_expression.strip()
            
            return DAXQuery(
                dax_expression=dax_expression,
                confidence=0.95,  # Higher confidence for GPT-5
                query_type=nl_query.query_type or QueryType.MEASURE,
                validation_errors=[]
            )
            
        except Exception as e:
            logging.error(f"Azure OpenAI generation failed: {e}")
            return self.generate_with_template(nl_query)
    
    def generate(self, nl_query: NLQuery, use_llm: bool = True) -> DAXQuery:
        """Generate DAX query from natural language"""
        if use_llm and self.client:
            return self.generate_with_llm(nl_query)
        else:
            return self.generate_with_template(nl_query)

class DAXExecutor:
    """Executes DAX queries against Power BI semantic models"""
    
    def __init__(self, workspace_id: str = None):
        self.workspace_id = workspace_id
        # In practice, you'd initialize the SemPy fabric client here
        # self.fabric_client = fabric.FabricRestClient()
    
    def execute_query(self, dax_query: str, dataset_id: str) -> Dict[str, Any]:
        """Execute DAX query and return results"""
        # Placeholder for actual execution
        # In practice, this would use SemPy:
        # result = fabric.evaluate_dax(
        #     dataset=dataset_id,
        #     dax_string=dax_query,
        #     workspace=self.workspace_id
        # )
        
        # Mock response for demonstration
        return {
            'status': 'success',
            'data': [
                {'Column1': 'Value1', 'Measure1': 100},
                {'Column1': 'Value2', 'Measure1': 200}
            ],
            'execution_time': 0.5,
            'row_count': 2
        }
    
    def execute_with_error_handling(self, dax_query: str, dataset_id: str) -> Dict[str, Any]:
        """Execute with comprehensive error handling"""
        try:
            result = self.execute_query(dax_query, dataset_id)
            return result
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'data': None
            }

class NL2DAXPipeline:
    """Complete NL2DAX pipeline orchestrator"""
    
    def __init__(self, semantic_model: SemanticModel, azure_openai_client=None, workspace_id: str = None):
        self.semantic_model = semantic_model
        self.analyzer = NLQueryAnalyzer(semantic_model)
        self.generator = DAXGenerator(semantic_model, azure_openai_client)
        self.validator = DAXValidator(semantic_model)
        self.executor = DAXExecutor(workspace_id)
    
    def process_query(self, natural_language_query: str, dataset_id: str, 
                     use_llm: bool = True, validate_only: bool = False) -> Dict[str, Any]:
        """Process complete NL2DAX pipeline"""
        
        # Step 1: Analyze natural language query
        nl_query = self.analyzer.analyze(natural_language_query)
        
        # Step 2: Generate DAX query
        dax_query = self.generator.generate(nl_query, use_llm=use_llm)
        
        # Step 3: Validate DAX query
        is_valid, validation_errors = self.validator.validate(dax_query.dax_expression)
        dax_query.validation_errors = validation_errors
        
        result = {
            'natural_language': natural_language_query,
            'analyzed_query': {
                'type': nl_query.query_type.value if nl_query.query_type else None,
                'confidence': nl_query.confidence,
                'entities': {
                    'tables': nl_query.tables_mentioned,
                    'measures': nl_query.measures_mentioned
                }
            },
            'generated_dax': dax_query.dax_expression,
            'dax_confidence': dax_query.confidence,
            'validation': {
                'is_valid': is_valid,
                'errors': validation_errors
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Step 4: Execute if valid and not validation-only
        if is_valid and not validate_only:
            execution_result = self.executor.execute_with_error_handling(
                dax_query.dax_expression, dataset_id
            )
            result['execution'] = execution_result
        
        return result

# Azure OpenAI Configuration and Utilities
def create_azure_openai_client() -> AzureOpenAI:
    """Create Azure OpenAI client using environment variables"""
    required_env_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    return AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    )

def validate_environment() -> Dict[str, str]:
    """Validate all required environment variables are set"""
    env_status = {
        "AZURE_OPENAI_ENDPOINT": "✓" if os.getenv("AZURE_OPENAI_ENDPOINT") else "✗",
        "AZURE_OPENAI_API_KEY": "✓" if os.getenv("AZURE_OPENAI_API_KEY") else "✗",
        "AZURE_OPENAI_API_VERSION": "✓" if os.getenv("AZURE_OPENAI_API_VERSION") else "✗",
        "AZURE_OPENAI_DEPLOYMENT_NAME": "✓" if os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") else "✗",
        "FABRIC_WORKSPACE_ID": "✓" if os.getenv("FABRIC_WORKSPACE_ID") else "⚠" 
    }
    return env_status

# Example usage and testing
def create_sample_semantic_model() -> SemanticModel:
    """Create a sample semantic model for testing"""
    return SemanticModel(
        name="Sales Model",
        tables={
            "Sales": ["Date", "ProductID", "CustomerID", "Amount", "Quantity"],
            "Products": ["ProductID", "ProductName", "Category", "Price"],
            "Customers": ["CustomerID", "CustomerName", "City", "Country"],
            "DateDim": ["Date", "Year", "Month", "Quarter"]
        },
        measures=["Total Sales", "Total Quantity", "Average Sale Amount", "Customer Count"],
        relationships=[
            {"from": "Sales[ProductID]", "to": "Products[ProductID]"},
            {"from": "Sales[CustomerID]", "to": "Customers[CustomerID]"},
            {"from": "Sales[Date]", "to": "DateDim[Date]"}
        ]
    )

# Demo function
def demo_nl2dax_pipeline():
    """Demonstrate the NL2DAX pipeline with Azure OpenAI"""
    print("=== Environment Validation ===")
    env_status = validate_environment()
    for var, status in env_status.items():
        print(f"{var}: {status}")
    
    # Check if Azure OpenAI is properly configured
    azure_client = None
    try:
        azure_client = create_azure_openai_client()
        print("✓ Azure OpenAI client created successfully")
    except ValueError as e:
        print(f"⚠ Azure OpenAI not configured: {e}")
        print("  Will use template-based generation")
    
    print("\n=== NL2DAX Pipeline Demo ===\n")
    
    # Create sample model
    model = create_sample_semantic_model()
    
    # Initialize pipeline with Azure OpenAI
    pipeline = NL2DAXPipeline(
        model, 
        azure_openai_client=azure_client,
        workspace_id=os.getenv("FABRIC_WORKSPACE_ID")
    )
    
    # Test queries
    test_queries = [
        "What is the total sales?",
        "Show me sales by product category",
        "Filter customers from Seattle",
        "Sales trend over time by month",
        "Compare this year's sales to last year",
        "Top 10 products by revenue"
    ]
    
    for query in test_queries:
        print(f"Query: {query}")
        result = pipeline.process_query(
            query, 
            dataset_id=os.getenv("POWER_BI_DATASET_ID", "sample-dataset"), 
            use_llm=azure_client is not None,
            validate_only=True
        )
        
        print(f"Query Type: {result['analyzed_query']['type']}")
        print(f"Confidence: {result['analyzed_query']['confidence']:.2f}")
        print(f"Generated DAX:\n{result['generated_dax']}")
        print(f"Valid: {result['validation']['is_valid']}")
        if result['validation']['errors']:
            print(f"Errors: {', '.join(result['validation']['errors'])}")
        print("-" * 80)

def create_env_template():
    """Create a template .env file for users"""
    env_template = """# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5

# Microsoft Fabric Configuration (Optional)
FABRIC_WORKSPACE_ID=your-workspace-id
POWER_BI_DATASET_ID=your-dataset-id

# Logging Configuration (Optional)
LOG_LEVEL=INFO
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_template)
        print("✓ Created .env template file. Please update with your actual values.")
    else:
        print("⚠ .env file already exists")

if __name__ == "__main__":
    # Create .env template if it doesn't exist
    create_env_template()
    
    # Run demo
    demo_nl2dax_pipeline()