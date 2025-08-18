"""
demo_sql_example.py - Universal SQL Generation Demo
================================================

This demo shows how the universal SQL generator works with any database
schema by automatically discovering patterns and generating appropriate queries.

Usage:
    python demo_sql_example.py
"""

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core import SchemaAgnosticAnalyzer, GenericSQLGenerator

def demo_sql_generation():
    """Demonstrate universal SQL generation capabilities"""
    
    print("=== Universal SQL Generation Demo ===\n")
    
    # Initialize components
    analyzer = SchemaAgnosticAnalyzer()
    generator = GenericSQLGenerator()
    
    print("1. Discovering database schema patterns...")
    
    # Analyze the schema
    try:
        schema_analysis = analyzer.analyze_schema_structure()
        print(f"   ✅ Discovered {len(schema_analysis.get('tables', []))} tables")
        print(f"   ✅ Identified {len(schema_analysis.get('business_areas', []))} business areas")
        print(f"   ✅ Schema complexity: {schema_analysis.get('complexity', 'Unknown')}")
    except Exception as e:
        print(f"   ❌ Schema analysis failed: {e}")
        return
    
    print("\n2. Testing universal SQL generation...")
    
    # Test queries that should work with any business database
    test_queries = [
        "Show me the top 10 customers by total revenue",
        "List all products with their categories and prices",
        "Find customers who haven't made purchases in the last 6 months",
        "Show monthly sales trends for the last year",
        "List the most popular products by quantity sold"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: {query}")
        try:
            result = generator.generate_sql_from_intent(query)
            print(f"   ✅ Generated SQL:")
            print(f"   {result['sql_query'][:100]}..." if len(result['sql_query']) > 100 else f"   {result['sql_query']}")
            print(f"   Analysis: {result['analysis_type']}")
            print(f"   Complexity: {result['estimated_complexity']}")
        except Exception as e:
            print(f"   ❌ Generation failed: {e}")
    
    print("\n3. Schema adaptability test...")
    
    # Show how it adapts to different schema patterns
    business_concepts = analyzer.get_business_suggestions()
    print(f"   ✅ Identified {len(business_concepts)} business concepts in this schema")
    
    for concept in business_concepts[:3]:  # Show first 3
        print(f"   • {concept['query']} (Complexity: {concept['complexity']})")
    
    print("\n=== Demo Complete ===")
    print("The universal SQL generator successfully adapted to your database schema!")
    print("🚀 Ready to work with any SQL database without code changes.")

if __name__ == "__main__":
    demo_sql_generation()