"""
Demo script for Clean DAX Engine
"""
if __name__ == "__main__":
    from main import CleanDAXEngine
    
    # Initialize the engine
    print("=" * 60)
    print("🚀 CLEAN DAX ENGINE DEMO")
    print("=" * 60)
    
    engine = CleanDAXEngine()
    
    # Test all components
    print("\n📋 Component Tests:")
    test_results = engine.test_components()
    for component, status in test_results.items():
        status_emoji = "✅" if status else "❌"
        print(f"  {status_emoji} {component}: {'PASS' if status else 'FAIL'}")
    
    # Show schema summary
    print("\n📊 Schema Summary:")
    schema_summary = engine.get_schema_summary()
    print(f"  • Total Tables: {schema_summary['total_tables']}")
    print(f"  • Fact Tables: {schema_summary['fact_tables']} ({', '.join(schema_summary['fact_table_names'][:3])}{'...' if len(schema_summary['fact_table_names']) > 3 else ''})")
    print(f"  • Dimension Tables: {schema_summary['dimension_tables']} ({', '.join(schema_summary['dimension_table_names'][:3])}{'...' if len(schema_summary['dimension_table_names']) > 3 else ''})")
    print(f"  • Cache Status: {'FRESH' if not schema_summary['is_expired'] else 'EXPIRED'}")
    
    # Test query generation and validation only (no execution to avoid errors)
    print("\n🔧 Testing DAX Generation & Validation:")
    test_query = "Show me top 5 customers by total exposure"
    
    result = engine.process_request(test_query, limit=5, execute=False)
    
    print(f"\n📝 Generated DAX Query:")
    print("=" * 40)
    print(result.dax_query)
    print("=" * 40)
    
    print(f"\n📈 Generation Results:")
    print(f"  • Pattern Used: {result.pattern_used}")
    print(f"  • Confidence: {result.confidence_score:.2f}")
    print(f"  • Generation Time: {result.generation_time:.3f}s")
    print(f"  • Valid: {'✅ YES' if result.is_valid else '❌ NO'}")
    
    if result.validation_issues:
        print(f"\n⚠️  Validation Issues ({len(result.validation_issues)}):")
        for issue in result.validation_issues:
            print(f"  • {issue}")
    else:
        print(f"\n✅ No validation issues found!")
    
    print("\n" + "=" * 60)
    print("🎉 Clean DAX Engine demo completed!")
    print("=" * 60)