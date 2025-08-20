# Demo function
def demo_nl2dax_pipeline():
    """Demonstrate the NL2DAX pipeline with real Fabric integration"""
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
    
    print("\n=== Fabric Integration Test ===")
    
    # Test with real dataset if available
    dataset_id = os.getenv("POWER_BI_DATASET_ID")
    workspace_id = os.getenv("FABRIC_WORKSPACE_ID")
    
    if dataset_id:
        print(f"Testing with real dataset: {dataset_id}")
        try:
            # Create pipeline directly from Fabric dataset
            pipeline = NL2DAXPipeline.from_dataset(
                dataset_id=dataset_id,
                workspace_id=workspace_id,
                azure_openai_client=azure_client,
                use_fabric=True
            )
            
            # Get pipeline stats
            stats = pipeline.get_pipeline_stats()
            print(f"Pipeline stats: {json.dumps(stats, indent=2)}")
            
            # Test queries with real data
            test_queries = [
                "What are the total sales?",
                "Show me revenue by product category",
                "What was the performance last month?",
            ]
            
            print("\n=== Real Dataset Query Tests ===")
            for query in test_queries:
                print(f"\nQuery: {query}")
                try:
                    result = pipeline.process_query(query, dataset_id, use_llm=True, validate_only=False)
                    print(f"Status: {'✓' if result.get('validation', {}).get('is_valid') else '✗'}")
                    print(f"DAX: {result.get('generated_dax', 'N/A')}")
                    
                    if result.get('execution'):
                        exec_result = result['execution']
                        print(f"Execution: {exec_result.get('status')} ({execclass QueryType(Enum):"""
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
import pandas as pd
import sempy.fabric as fabric
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
import requests
from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FabricAuthManager:
    """Manages authentication for Microsoft Fabric"""
    
    def __init__(self):
        self.credential = None
        self._initialize_auth()
    
    def _initialize_auth(self):
        """Initialize Azure authentication"""
        auth_method = os.getenv("AZURE_AUTH_METHOD", "default")
        
        try:
            if auth_method == "interactive":
                self.credential = InteractiveBrowserCredential()
                logger.info("Using interactive browser authentication")
            else:
                self.credential = DefaultAzureCredential()
                logger.info("Using default Azure credential chain")
                
            # Test authentication
            token = self.credential.get_token("https://analysis.windows.net/powerbi/api/.default")
            logger.info("Authentication successful")
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    def get_access_token(self) -> str:
        """Get access token for Power BI API"""
        try:
            token = self.credential.get_token("https://analysis.windows.net/powerbi/api/.default")
            return token.token
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise

class PowerBIAPIClient:
    """Client for Power BI REST API operations"""
    
    def __init__(self, auth_manager: FabricAuthManager):
        self.auth_manager = auth_manager
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authorization token"""
        token = self.auth_manager.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def get_workspaces(self) -> List[Dict]:
        """Get list of available workspaces"""
        try:
            response = self.session.get(
                f"{self.base_url}/groups",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json().get("value", [])
        except Exception as e:
            logger.error(f"Failed to get workspaces: {e}")
            return []
    
    def get_datasets(self, workspace_id: str = None) -> List[Dict]:
        """Get datasets from workspace"""
        try:
            url = f"{self.base_url}/datasets"
            if workspace_id:
                url = f"{self.base_url}/groups/{workspace_id}/datasets"
            
            response = self.session.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json().get("value", [])
        except Exception as e:
            logger.error(f"Failed to get datasets: {e}")
            return []
    
    def execute_dax_query(self, dataset_id: str, dax_query: str, workspace_id: str = None) -> Dict:
        """Execute DAX query via Power BI REST API"""
        try:
            url = f"{self.base_url}/datasets/{dataset_id}/executeQueries"
            if workspace_id:
                url = f"{self.base_url}/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
            
            payload = {
                "queries": [
                    {
                        "query": dax_query
                    }
                ],
                "serializerSettings": {
                    "includeNulls": True
                }
            }
            
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=300  # 5 minute timeout
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"DAX query execution failed: {e}")
            raise
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
    dataset_id: Optional[str] = None
    workspace_id: Optional[str] = None
    
    @classmethod
    def from_fabric_dataset(cls, dataset_id: str, workspace_id: str = None):
        """Create SemanticModel from Fabric dataset metadata"""
        try:
            # Get dataset metadata using SemPy
            tables_df = fabric.list_tables(dataset=dataset_id, workspace=workspace_id)
            measures_df = fabric.list_measures(dataset=dataset_id, workspace=workspace_id)
            relationships_df = fabric.list_relationships(dataset=dataset_id, workspace=workspace_id)
            
            # Extract tables and columns
            tables = {}
            for _, row in tables_df.iterrows():
                table_name = row['Name']
                columns_df = fabric.list_columns(
                    dataset=dataset_id, 
                    workspace=workspace_id, 
                    table=table_name
                )
                tables[table_name] = columns_df['Name'].tolist()
            
            # Extract measures
            measures = measures_df['Name'].tolist() if not measures_df.empty else []
            
            # Extract relationships
            relationships = []
            if not relationships_df.empty:
                for _, rel in relationships_df.iterrows():
                    relationships.append({
                        'from': f"{rel['FromTable']}[{rel['FromColumn']}]",
                        'to': f"{rel['ToTable']}[{rel['ToColumn']}]",
                        'type': rel.get('CrossFilteringBehavior', 'OneDirection')
                    })
            
            return cls(
                name=f"Dataset_{dataset_id}",
                tables=tables,
                measures=measures,
                relationships=relationships,
                dataset_id=dataset_id,
                workspace_id=workspace_id
            )
            
        except Exception as e:
            logger.error(f"Failed to load semantic model from Fabric: {e}")
            raise

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
    """Executes DAX queries against Power BI semantic models using real Fabric APIs"""
    
    def __init__(self, workspace_id: str = None, use_fabric: bool = True):
        self.workspace_id = workspace_id
        self.use_fabric = use_fabric
        self.auth_manager = None
        self.powerbi_client = None
        
        if use_fabric:
            try:
                self.auth_manager = FabricAuthManager()
                self.powerbi_client = PowerBIAPIClient(self.auth_manager)
                logger.info("Fabric integration initialized successfully")
            except Exception as e:
                logger.warning(f"Fabric integration failed, falling back to mock: {e}")
                self.use_fabric = False
    
    @lru_cache(maxsize=100)
    def _get_dataset_info(self, dataset_id: str) -> Dict:
        """Get cached dataset information"""
        if not self.use_fabric:
            return {"name": "Mock Dataset", "tables": []}
        
        try:
            datasets = self.powerbi_client.get_datasets(self.workspace_id)
            for dataset in datasets:
                if dataset.get("id") == dataset_id:
                    return dataset
            return None
        except Exception as e:
            logger.error(f"Failed to get dataset info: {e}")
            return None
    
    def execute_query_fabric(self, dax_query: str, dataset_id: str) -> Dict[str, Any]:
        """Execute DAX query using SemPy Fabric client"""
        try:
            start_time = time.time()
            
            # Execute using SemPy evaluate_dax
            result_df = fabric.evaluate_dax(
                dataset=dataset_id,
                dax_string=dax_query,
                workspace=self.workspace_id
            )
            
            execution_time = time.time() - start_time
            
            # Convert DataFrame to dictionary format
            result_data = result_df.to_dict('records') if not result_df.empty else []
            
            return {
                'status': 'success',
                'data': result_data,
                'execution_time': round(execution_time, 3),
                'row_count': len(result_data),
                'columns': list(result_df.columns) if not result_df.empty else [],
                'method': 'fabric_sempy'
            }
            
        except Exception as e:
            logger.error(f"SemPy execution failed: {e}")
            raise
    
    def execute_query_rest_api(self, dax_query: str, dataset_id: str) -> Dict[str, Any]:
        """Execute DAX query using Power BI REST API"""
        try:
            start_time = time.time()
            
            result = self.powerbi_client.execute_dax_query(
                dataset_id=dataset_id,
                dax_query=dax_query,
                workspace_id=self.workspace_id
            )
            
            execution_time = time.time() - start_time
            
            # Parse Power BI API response
            if result.get("results"):
                tables = result["results"][0].get("tables", [])
                if tables:
                    table_data = tables[0]
                    rows = table_data.get("rows", [])
                    
                    return {
                        'status': 'success',
                        'data': rows,
                        'execution_time': round(execution_time, 3),
                        'row_count': len(rows),
                        'method': 'rest_api'
                    }
            
            return {
                'status': 'success',
                'data': [],
                'execution_time': round(execution_time, 3),
                'row_count': 0,
                'method': 'rest_api'
            }
            
        except Exception as e:
            logger.error(f"REST API execution failed: {e}")
            raise
    
    def execute_query(self, dax_query: str, dataset_id: str) -> Dict[str, Any]:
        """Execute DAX query with automatic method selection"""
        if not self.use_fabric:
            return self._mock_execute_query(dax_query, dataset_id)
        
        # Try SemPy first, fall back to REST API
        try:
            return self.execute_query_fabric(dax_query, dataset_id)
        except Exception as e:
            logger.warning(f"SemPy execution failed, trying REST API: {e}")
            try:
                return self.execute_query_rest_api(dax_query, dataset_id)
            except Exception as e2:
                logger.error(f"Both execution methods failed. SemPy: {e}, REST API: {e2}")
                raise Exception(f"Query execution failed: {e2}")
    
    def _mock_execute_query(self, dax_query: str, dataset_id: str) -> Dict[str, Any]:
        """Mock query execution for testing"""
        logger.info("Using mock execution")
        return {
            'status': 'success',
            'data': [
                {'Column1': 'Sample Data', 'Measure1': 12345.67},
                {'Column1': 'More Data', 'Measure1': 23456.78}
            ],
            'execution_time': 0.1,
            'row_count': 2,
            'method': 'mock'
        }
    
    def execute_with_error_handling(self, dax_query: str, dataset_id: str) -> Dict[str, Any]:
        """Execute with comprehensive error handling and retry logic"""
        max_retries = int(os.getenv("DAX_EXECUTION_RETRIES", "3"))
        
        for attempt in range(max_retries):
            try:
                result = self.execute_query(dax_query, dataset_id)
                if attempt > 0:
                    logger.info(f"Query succeeded on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed: {e}")
                    return {
                        'status': 'error',
                        'error': str(e),
                        'data': None,
                        'attempts': max_retries
                    }
        
        return {
            'status': 'error',
            'error': 'Max retries exceeded',
            'data': None
        }

class NL2DAXPipeline:
    """Complete NL2DAX pipeline orchestrator with enterprise features"""
    
    def __init__(self, semantic_model: SemanticModel = None, azure_openai_client=None, 
                 workspace_id: str = None, use_fabric: bool = True):
        self.semantic_model = semantic_model
        self.workspace_id = workspace_id or os.getenv("FABRIC_WORKSPACE_ID")
        
        # Initialize components
        if semantic_model:
            self.analyzer = NLQueryAnalyzer(semantic_model)
            self.generator = DAXGenerator(semantic_model, azure_openai_client)
            self.validator = DAXValidator(semantic_model)
        else:
            self.analyzer = None
            self.generator = None
            self.validator = None
            
        self.executor = DAXExecutor(self.workspace_id, use_fabric)
        
        # Query cache for performance
        self.query_cache = {}
        self.cache_enabled = os.getenv("ENABLE_QUERY_CACHE", "true").lower() == "true"
    
    @classmethod
    def from_dataset(cls, dataset_id: str, workspace_id: str = None, 
                     azure_openai_client=None, use_fabric: bool = True):
        """Create pipeline directly from a Fabric dataset"""
        try:
            semantic_model = SemanticModel.from_fabric_dataset(dataset_id, workspace_id)
            return cls(semantic_model, azure_openai_client, workspace_id, use_fabric)
        except Exception as e:
            logger.error(f"Failed to create pipeline from dataset {dataset_id}: {e}")
            raise
    
    def _get_cache_key(self, query: str, dataset_id: str) -> str:
        """Generate cache key for query"""
        import hashlib
        return hashlib.md5(f"{query}:{dataset_id}".encode()).hexdigest()
    
    def _should_use_cache(self, query: str) -> bool:
        """Determine if query should use cache based on patterns"""
        # Don't cache time-sensitive queries
        time_indicators = ['today', 'now', 'current', 'latest', 'recent']
        return not any(indicator in query.lower() for indicator in time_indicators)
    
    async def process_query_async(self, natural_language_query: str, dataset_id: str, 
                                use_llm: bool = True, validate_only: bool = False) -> Dict[str, Any]:
        """Asynchronous query processing for better performance"""
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Run analysis, generation, and validation in parallel where possible
            if self.semantic_model:
                analysis_future = loop.run_in_executor(executor, self.analyzer.analyze, natural_language_query)
                analysis_result = await analysis_future
                
                generation_future = loop.run_in_executor(executor, self.generator.generate, analysis_result, use_llm)
                dax_query = await generation_future
                
                validation_future = loop.run_in_executor(executor, self.validator.validate, dax_query.dax_expression)
                is_valid, validation_errors = await validation_future
            else:
                # Fallback for when semantic model is not available
                analysis_result = None
                dax_query = None
                is_valid, validation_errors = False, ["No semantic model available"]
        
        # Build result
        result = {
            'natural_language': natural_language_query,
            'dataset_id': dataset_id,
            'timestamp': datetime.now().isoformat()
        }
        
        if analysis_result and dax_query:
            result.update({
                'analyzed_query': {
                    'type': analysis_result.query_type.value if analysis_result.query_type else None,
                    'confidence': analysis_result.confidence,
                    'entities': {
                        'tables': analysis_result.tables_mentioned,
                        'measures': analysis_result.measures_mentioned
                    }
                },
                'generated_dax': dax_query.dax_expression,
                'dax_confidence': dax_query.confidence,
                'validation': {
                    'is_valid': is_valid,
                    'errors': validation_errors
                }
            })
            
            # Execute if valid and not validation-only
            if is_valid and not validate_only:
                execution_result = await loop.run_in_executor(
                    executor, 
                    self.executor.execute_with_error_handling,
                    dax_query.dax_expression, 
                    dataset_id
                )
                result['execution'] = execution_result
        
        return result
    
    def process_query(self, natural_language_query: str, dataset_id: str, 
                     use_llm: bool = True, validate_only: bool = False, 
                     use_cache: bool = None) -> Dict[str, Any]:
        """Process complete NL2DAX pipeline with caching"""
        
        # Check cache
        if use_cache is None:
            use_cache = self.cache_enabled and self._should_use_cache(natural_language_query)
        
        cache_key = None
        if use_cache:
            cache_key = self._get_cache_key(natural_language_query, dataset_id)
            if cache_key in self.query_cache:
                logger.info("Returning cached result")
                cached_result = self.query_cache[cache_key].copy()
                cached_result['cache_hit'] = True
                return cached_result
        
        # Process query
        start_time = time.time()
        
        if not self.semantic_model:
            # Try to load semantic model from dataset
            try:
                self.semantic_model = SemanticModel.from_fabric_dataset(dataset_id, self.workspace_id)
                self.analyzer = NLQueryAnalyzer(self.semantic_model)
                self.generator = DAXGenerator(self.semantic_model, None)  # Add azure client if needed
                self.validator = DAXValidator(self.semantic_model)
                logger.info(f"Loaded semantic model for dataset {dataset_id}")
            except Exception as e:
                logger.error(f"Could not load semantic model: {e}")
                return {
                    'natural_language': natural_language_query,
                    'error': 'Could not load semantic model',
                    'dataset_id': dataset_id,
                    'timestamp': datetime.now().isoformat()
                }
        
        # Step 1: Analyze natural language query
        nl_query = self.analyzer.analyze(natural_language_query)
        
        # Step 2: Generate DAX query
        dax_query = self.generator.generate(nl_query, use_llm=use_llm)
        
        # Step 3: Validate DAX query
        is_valid, validation_errors = self.validator.validate(dax_query.dax_expression)
        dax_query.validation_errors = validation_errors
        
        processing_time = time.time() - start_time
        
        result = {
            'natural_language': natural_language_query,
            'dataset_id': dataset_id,
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
            'processing_time': round(processing_time, 3),
            'cache_hit': False,
            'timestamp': datetime.now().isoformat()
        }
        
        # Step 4: Execute if valid and not validation-only
        if is_valid and not validate_only:
            execution_result = self.executor.execute_with_error_handling(
                dax_query.dax_expression, dataset_id
            )
            result['execution'] = execution_result
        
        # Cache result if caching is enabled
        if use_cache and cache_key and is_valid:
            # Don't cache execution results, only generation/validation
            cache_result = result.copy()
            if 'execution' in cache_result:
                del cache_result['execution']
            self.query_cache[cache_key] = cache_result
            logger.info(f"Cached result with key: {cache_key}")
        
        return result
    
    def batch_process_queries(self, queries: List[str], dataset_id: str, 
                            use_llm: bool = True) -> List[Dict[str, Any]]:
        """Process multiple queries in batch for efficiency"""
        results = []
        
        logger.info(f"Processing {len(queries)} queries in batch")
        
        for i, query in enumerate(queries, 1):
            logger.info(f"Processing query {i}/{len(queries)}: {query}")
            try:
                result = self.process_query(query, dataset_id, use_llm, validate_only=True)
                result['batch_index'] = i
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process query {i}: {e}")
                results.append({
                    'natural_language': query,
                    'error': str(e),
                    'batch_index': i,
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline performance and usage statistics"""
        return {
            'cache_size': len(self.query_cache),
            'cache_enabled': self.cache_enabled,
            'workspace_id': self.workspace_id,
            'semantic_model_loaded': self.semantic_model is not None,
            'fabric_enabled': self.executor.use_fabric if self.executor else False,
            'model_info': {
                'name': self.semantic_model.name if self.semantic_model else None,
                'table_count': len(self.semantic_model.tables) if self.semantic_model else 0,
                'measure_count': len(self.semantic_model.measures) if self.semantic_model else 0
            } if self.semantic_model else None
        }
    
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
    """Demonstrate the NL2DAX pipeline with real Fabric integration"""
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
    
    print("\n=== Fabric Integration Test ===")
    
    # Test with real dataset if available
    dataset_id = os.getenv("POWER_BI_DATASET_ID")
    workspace_id = os.getenv("FABRIC_WORKSPACE_ID")
    
    if dataset_id:
        print(f"Testing with real dataset: {dataset_id}")
        try:
            # Create pipeline directly from Fabric dataset
            pipeline = NL2DAXPipeline.from_dataset(
                dataset_id=dataset_id,
                workspace_id=workspace_id,
                azure_openai_client=azure_client,
                use_fabric=True
            )
            
            # Get pipeline stats
            stats = pipeline.get_pipeline_stats()
            print(f"Pipeline stats: {json.dumps(stats, indent=2)}")
            
            # Test queries with real data
            test_queries = [
                "What are the total sales?",
                "Show me revenue by product category",
                "What was the performance last month?",
            ]
            
            print("\n=== Real Dataset Query Tests ===")
            for query in test_queries:
                print(f"\nQuery: {query}")
                try:
                    result = pipeline.process_query(query, dataset_id, use_llm=True, validate_only=False)
                    print(f"Status: {'✓' if result.get('validation', {}).get('is_valid') else '✗'}")
                    print(f"DAX: {result.get('generated_dax', 'N/A')}")
                    
                    if result.get('execution'):
                        exec_result = result['execution']
                        print(f"Execution: {exec_result.get('status')} ({exec_result.get('method', 'unknown')})")
                        print(f"Rows: {exec_result.get('row_count', 0)}, Time: {exec_result.get('execution_time', 0)}s")
                        
                        # Show sample data
                        if exec_result.get('data') and len(exec_result['data']) > 0:
                            sample_data = exec_result['data'][:3]  # First 3 rows
                            print(f"Sample data: {json.dumps(sample_data, indent=2)}")
                    
                except Exception as e:
                    print(f"✗ Error: {e}")
                
                print("-" * 60)
            
            # Test batch processing
            print("\n=== Batch Processing Test ===")
            batch_queries = [
                "Total revenue this year",
                "Top 5 customers by sales",
                "Monthly sales trend"
            ]
            
            batch_results = pipeline.batch_process_queries(batch_queries, dataset_id, use_llm=True)
            for result in batch_results:
                print(f"Query {result.get('batch_index')}: {'✓' if result.get('validation', {}).get('is_valid') else '✗'}")
            
        except Exception as e:
            print(f"✗ Failed to test with real dataset: {e}")
            print("  Falling back to mock demo")
            demo_with_mock_data(azure_client)
    else:
        print("No dataset ID configured, using mock data")
        demo_with_mock_data(azure_client)

def demo_with_mock_data(azure_client):
    """Demo with sample/mock data when real Fabric connection isn't available"""
    print("\n=== Mock Data Demo ===")
    
    # Create sample model
    model = create_sample_semantic_model()
    
    # Initialize pipeline with mock data
    pipeline = NL2DAXPipeline(
        model, 
        azure_openai_client=azure_client,
        workspace_id=os.getenv("FABRIC_WORKSPACE_ID"),
        use_fabric=False  # Force mock mode
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
    
    print("Testing queries with mock execution...")
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            result = pipeline.process_query(
                query, 
                dataset_id="mock-dataset", 
                use_llm=azure_client is not None,
                validate_only=False
            )
            
            print(f"Type: {result['analyzed_query']['type']}")
            print(f"Confidence: {result['analyzed_query']['confidence']:.2f}")
            print(f"DAX: {result['generated_dax']}")
            print(f"Valid: {result['validation']['is_valid']}")
            
            if result['validation']['errors']:
                print(f"Errors: {', '.join(result['validation']['errors'])}")
            
            if result.get('execution'):
                exec_result = result['execution']
                print(f"Execution: {exec_result['status']} - {exec_result['row_count']} rows in {exec_result['execution_time']}s")
            
        except Exception as e:
            print(f"✗ Error: {e}")
        
        print("-" * 60)

async def demo_async_processing():
    """Demonstrate asynchronous query processing"""
    print("\n=== Async Processing Demo ===")
    
    try:
        azure_client = create_azure_openai_client()
    except:
        azure_client = None
    
    model = create_sample_semantic_model()
    pipeline = NL2DAXPipeline(model, azure_client, use_fabric=False)
    
    queries = [
        "What are total sales?",
        "Show revenue by region",
        "Customer count by city"
    ]
    
    print("Processing queries asynchronously...")
    start_time = time.time()
    
    tasks = []
    for query in queries:
        task = pipeline.process_query_async(query, "mock-dataset", use_llm=False, validate_only=True)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - start_time
    print(f"Processed {len(queries)} queries in {total_time:.2f}s")
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Query {i+1}: ✗ Error - {result}")
        else:
            print(f"Query {i+1}: {'✓' if result.get('validation', {}).get('is_valid') else '✗'}")

def create_env_template():
    """Create a comprehensive .env template file for users"""
    env_template = """# Azure OpenAI Configuration (Required)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5

# Microsoft Fabric Configuration (Required for real data)
FABRIC_WORKSPACE_ID=your-workspace-id
POWER_BI_DATASET_ID=your-dataset-id

# Azure Authentication (Optional - defaults to DefaultAzureCredential)
AZURE_AUTH_METHOD=default  # or 'interactive' for browser auth

# Pipeline Configuration (Optional)
ENABLE_QUERY_CACHE=true
DAX_EXECUTION_RETRIES=3
LOG_LEVEL=INFO

# Performance Tuning (Optional)
MAX_CONCURRENT_QUERIES=5
CACHE_TTL_SECONDS=3600
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_template)
        print("✓ Created comprehensive .env template file.")
        print("  Please update with your actual Azure and Fabric credentials.")
    else:
        print("⚠ .env file already exists")

def setup_logging():
    """Setup comprehensive logging configuration"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Configure logging with both file and console handlers
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"logs/nl2dax_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler()
        ]
    )
    
    # Set specific log levels for external libraries
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

def main():
    """Main function to run the complete demo"""
    # Setup
    setup_logging()
    create_env_template()
    
    print("=" * 80)
    print("NL2DAX Pipeline with Microsoft Fabric Integration")
    print("=" * 80)
    
    try:
        # Run synchronous demo
        demo_nl2dax_pipeline()
        
        # Run async demo if asyncio is available
        if os.getenv("ENABLE_ASYNC_DEMO", "false").lower() == "true":
            asyncio.run(demo_async_processing())
        
        print("\n" + "=" * 80)
        print("Demo completed successfully!")
        print("Check the logs/ directory for detailed execution logs.")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n⚠ Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        print(f"\n✗ Demo failed: {e}")
        print("Check the logs for more details.")

if __name__ == "__main__":
    main()