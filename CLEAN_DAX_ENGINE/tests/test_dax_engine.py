"""
Test suite for Clean DAX Engine
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.schema_manager import SchemaManager, SchemaTable, SchemaInfo
from core.dax_generator import CleanDAXGenerator, DAXGenerationRequest
from core.dax_validator import CleanDAXValidator, ValidationSeverity
from datetime import datetime

class TestSchemaManager(unittest.TestCase):
    """Test cases for SchemaManager"""
    
    def setUp(self):
        self.schema_manager = SchemaManager(cache_dir="./test_cache")
    
    def test_schema_table_creation(self):
        """Test SchemaTable creation"""
        table = SchemaTable(
            name="TEST_FACT",
            table_type="fact",
            columns=["ID", "AMOUNT", "CUSTOMER_KEY"],
            key_columns=["ID", "CUSTOMER_KEY"],
            measure_columns=["AMOUNT"]
        )
        
        self.assertEqual(table.name, "TEST_FACT")
        self.assertEqual(table.table_type, "fact")
        self.assertIn("AMOUNT", table.measure_columns)
    
    def test_table_validation(self):
        """Test table existence validation"""
        # Mock schema with test table
        test_table = SchemaTable(
            name="TEST_TABLE",
            table_type="fact",
            columns=["ID", "VALUE"],
            key_columns=["ID"],
            measure_columns=["VALUE"]
        )
        
        schema_info = SchemaInfo(
            tables={"TEST_TABLE": test_table},
            relationships=[],
            cached_at=datetime.now()
        )
        
        self.schema_manager._schema_cache = schema_info
        
        self.assertTrue(self.schema_manager.validate_table_exists("TEST_TABLE"))
        self.assertFalse(self.schema_manager.validate_table_exists("NONEXISTENT_TABLE"))

class TestDAXGenerator(unittest.TestCase):
    """Test cases for CleanDAXGenerator"""
    
    def setUp(self):
        # Mock schema manager
        self.mock_schema_manager = Mock(spec=SchemaManager)
        
        # Create test schema
        fact_table = SchemaTable(
            name="FIS_LOAN_FACT",
            table_type="fact",
            columns=["CUSTOMER_KEY", "EXPOSURE_AMT"],
            key_columns=["CUSTOMER_KEY"],
            measure_columns=["EXPOSURE_AMT"]
        )
        
        dim_table = SchemaTable(
            name="FIS_CUSTOMER_DIMENSION",
            table_type="dimension",
            columns=["CUSTOMER_KEY", "CUSTOMER_NAME"],
            key_columns=["CUSTOMER_KEY"],
            measure_columns=[]
        )
        
        schema_info = SchemaInfo(
            tables={"FIS_LOAN_FACT": fact_table, "FIS_CUSTOMER_DIMENSION": dim_table},
            relationships=[],
            cached_at=datetime.now()
        )
        
        self.mock_schema_manager.get_schema.return_value = schema_info
        self.generator = CleanDAXGenerator(self.mock_schema_manager)
    
    def test_intent_analysis(self):
        """Test business intent analysis"""
        schema = self.mock_schema_manager.get_schema()
        analysis = self.generator._analyze_intent("top 5 customers by exposure", schema)
        
        self.assertEqual(analysis['intent_type'], 'ranking')
        self.assertEqual(analysis['target_entity'], 'customer')
        self.assertIn('FIS_CUSTOMER_DIMENSION', analysis['tables'])
    
    def test_dax_generation(self):
        """Test DAX query generation"""
        request = DAXGenerationRequest(
            business_intent="Show top 5 customers by exposure",
            limit=5
        )
        
        result = self.generator.generate_dax(request)
        
        self.assertIsNotNone(result.dax_query)
        self.assertIn("EVALUATE", result.dax_query)
        self.assertIn("TOPN", result.dax_query)
        self.assertGreater(result.confidence_score, 0)

class TestDAXValidator(unittest.TestCase):
    """Test cases for CleanDAXValidator"""
    
    def setUp(self):
        # Mock schema manager
        self.mock_schema_manager = Mock(spec=SchemaManager)
        self.mock_schema_manager.validate_table_exists.return_value = True
        self.mock_schema_manager.validate_column_exists.return_value = True
        
        # Mock schema
        schema_info = SchemaInfo(
            tables={"TEST_TABLE": SchemaTable("TEST_TABLE", "fact", ["ID", "AMOUNT"], ["ID"], ["AMOUNT"])},
            relationships=[],
            cached_at=datetime.now()
        )
        self.mock_schema_manager.get_schema.return_value = schema_info
        
        self.validator = CleanDAXValidator(self.mock_schema_manager)
    
    def test_syntax_validation(self):
        """Test basic syntax validation"""
        # Valid query
        valid_query = "EVALUATE ROW(\"Test\", 1)"
        result = self.validator.validate(valid_query)
        self.assertTrue(result.is_valid)
        
        # Invalid query - missing EVALUATE
        invalid_query = "ROW(\"Test\", 1)"
        result = self.validator.validate(invalid_query)
        self.assertFalse(result.is_valid)
        self.assertTrue(any(issue.severity == ValidationSeverity.ERROR for issue in result.issues))
    
    def test_table_reference_extraction(self):
        """Test table reference extraction"""
        query = "EVALUATE SUMMARIZE('TEST_TABLE', 'TEST_TABLE'[ID])"
        tables = self.validator._extract_table_references(query)
        self.assertIn("TEST_TABLE", tables)
    
    def test_best_practices_validation(self):
        """Test best practices validation"""
        # Query with ORDER BY (should fail)
        query_with_order_by = "EVALUATE 'TEST_TABLE' ORDER BY 'TEST_TABLE'[ID]"
        result = self.validator.validate(query_with_order_by)
        self.assertTrue(any("ORDER BY" in issue.message for issue in result.issues))

if __name__ == '__main__':
    print("🧪 Running Clean DAX Engine Tests")
    print("=" * 50)
    
    # Run the tests
    unittest.main(verbosity=2)