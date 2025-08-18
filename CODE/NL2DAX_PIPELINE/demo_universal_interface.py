"""
demo_universal_interface.py - Demonstration of Universal Query Interface
========================================================================

This script demonstrates the new database-agnostic query generation system
that works with any SQL database and Power BI/Fabric semantic model.

Key Demonstrations:
- Automatic schema discovery and analysis
- Generic SQL and DAX query generation
- Business intent-driven query creation
- Cross-platform compatibility

Usage:
    python demo_universal_interface.py

Author: NL2DAX Pipeline Development Team
Last Updated: August 16, 2025
"""

import os
import sys
from datetime import datetime
from universal_query_interface import UniversalQueryInterface, QueryType, AnalysisType

def print_banner(title: str):
    """Print a formatted banner"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_query_result(result, title: str):
    """Print formatted query result"""
    print_banner(title)
    print(f"Analysis Type: {result.analysis_type.value}")
    print(f"Business Intent: {result.business_intent}")
    
    if result.sql_query:
        print(f"\n📊 Generated SQL Query:")
        print("-" * 40)
        print(result.sql_query)
    
    if result.dax_query:
        print(f"\n⚡ Generated DAX Query:")
        print("-" * 40)
        print(result.dax_query)
    
    if result.execution_notes:
        print(f"\n⚠️  Notes: {result.execution_notes}")
    
    if result.estimated_complexity:
        print(f"📈 Estimated Complexity: {result.estimated_complexity}")

def demonstrate_schema_analysis(interface: UniversalQueryInterface):
    """Demonstrate automatic schema analysis"""
    print_banner("AUTOMATIC SCHEMA ANALYSIS")
    
    # Get schema summary
    summary = interface.get_schema_summary()
    print("📋 Schema Summary:")
    print(f"   • Total Tables: {summary['total_tables']}")
    print(f"   • Fact Tables: {summary['fact_tables']}")
    print(f"   • Dimension Tables: {summary['dimension_tables']}")
    print(f"   • Business Areas: {', '.join(summary['business_areas'])}")
    print(f"   • Complexity: {summary['complexity_assessment']}")
    
    # Get business suggestions
    suggestions = interface.get_business_suggestions()
    print(f"\n💡 Suggested Business Queries:")
    for i, suggestion in enumerate(suggestions[:5], 1):
        print(f"   {i}. {suggestion['query']} (Complexity: {suggestion['complexity']})")

def demonstrate_predefined_analyses(interface: UniversalQueryInterface):
    """Demonstrate predefined business analysis patterns"""
    print_banner("PREDEFINED BUSINESS ANALYSES")
    
    # Customer Overview
    result = interface.generate_customer_overview(QueryType.BOTH)
    print_query_result(result, "Customer Overview Analysis")
    
    # Currency Exposure  
    result = interface.generate_currency_exposure(QueryType.SQL)
    print_query_result(result, "Currency Exposure Analysis (SQL Only)")
    
    # Risk Analysis
    result = interface.generate_risk_analysis(QueryType.DAX)
    print_query_result(result, "Risk Analysis (DAX Only)")

def demonstrate_custom_intents(interface: UniversalQueryInterface):
    """Demonstrate custom business intent queries"""
    print_banner("CUSTOM BUSINESS INTENT QUERIES")
    
    # Custom intent examples
    custom_intents = [
        "Show me the top 5 customers by total exposure with their risk ratings",
        "Compare North American vs European portfolio performance",
        "Analyze currency concentration risk in our loan portfolio",
        "Display monthly trend of new customer acquisitions by country"
    ]
    
    for i, intent in enumerate(custom_intents, 1):
        print(f"\n🎯 Custom Intent {i}: {intent}")
        result = interface.generate_query_from_intent(intent, QueryType.BOTH)
        
        if result.sql_query:
            print(f"\n📊 SQL Query (Complexity: {result.estimated_complexity}):")
            print(result.sql_query[:200] + "..." if len(result.sql_query) > 200 else result.sql_query)
        
        if result.dax_query:
            print(f"\n⚡ DAX Query (Complexity: {result.estimated_complexity}):")
            print(result.dax_query[:200] + "..." if len(result.dax_query) > 200 else result.dax_query)

def demonstrate_adaptability(interface: UniversalQueryInterface):
    """Demonstrate how the system adapts to different schemas"""
    print_banner("SCHEMA ADAPTABILITY DEMONSTRATION")
    
    # Show how the system analyzes and adapts
    schema_analysis = interface.analyze_current_schema()
    
    print("🔍 Discovered Schema Patterns:")
    for table_name, table_info in list(schema_analysis['tables'].items())[:3]:
        print(f"\n📋 Table: {table_name}")
        print(f"   • Type: {table_info.table_type.value}")
        print(f"   • Business Concepts: {', '.join(table_info.business_concepts)}")
        print(f"   • Key Columns: {table_info.primary_key}, {', '.join(table_info.foreign_keys[:2])}")
        print(f"   • Total Columns: {len(table_info.columns)}")
    
    print(f"\n🔗 Discovered Relationships:")
    for rel in schema_analysis['relationships'][:3]:
        print(f"   • {rel['parent_table']}.{rel['parent_column']} → {rel['referenced_table']}.{rel['referenced_column']}")

def main():
    """Main demonstration function"""
    print("🚀 Universal Query Interface Demonstration")
    print("   Database-Agnostic SQL & DAX Query Generation")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize the universal interface
        print("\n🔧 Initializing Universal Query Interface...")
        interface = UniversalQueryInterface()
        
        # Demonstrate each capability
        demonstrate_schema_analysis(interface)
        demonstrate_predefined_analyses(interface)
        demonstrate_custom_intents(interface)
        demonstrate_adaptability(interface)
        
        # Summary
        print_banner("DEMONSTRATION COMPLETE")
        print("✅ Successfully demonstrated:")
        print("   • Automatic schema discovery and analysis")
        print("   • Generic SQL query generation")
        print("   • Generic DAX query generation")
        print("   • Business intent-driven query creation")
        print("   • Cross-platform database compatibility")
        print("   • Adaptive schema pattern recognition")
        
        print(f"\n💡 The system is now ready to work with ANY database schema!")
        print(f"   Simply change the database connection and it will adapt automatically.")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {str(e)}")
        print(f"   Please check your environment configuration.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)