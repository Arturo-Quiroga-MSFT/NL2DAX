"""
Full demo with execution for Clean DAX Engine
"""
if __name__ == "__main__":
    from main import CleanDAXEngine
    
    # Initialize the engine
    print("=" * 60)
    print("🚀 CLEAN DAX ENGINE - FULL EXECUTION TEST")
    print("=" * 60)
    
    engine = CleanDAXEngine()
    
    # Test with execution enabled
    print("\n🔧 Testing DAX Generation, Validation & Execution:")
    test_query = "Show me top 5 customers by total exposure"
    
    result = engine.process_request(test_query, limit=5, execute=True)
    
    print(f"\n📝 Generated DAX Query:")
    print("=" * 40)
    print(result.dax_query)
    print("=" * 40)
    
    print(f"\n📈 Complete Results:")
    print(f"  • Pattern Used: {result.pattern_used}")
    print(f"  • Confidence: {result.confidence_score:.2f}")
    print(f"  • Generation Time: {result.generation_time:.3f}s")
    print(f"  • Valid: {'✅ YES' if result.is_valid else '❌ NO'}")
    print(f"  • Execution Success: {'✅ YES' if result.execution_success else '❌ NO'}")
    
    if result.execution_success:
        print(f"  • Rows Returned: {result.row_count}")
        print(f"  • Execution Time: {result.execution_time:.3f}s")
        
        print(f"\n🎯 DAX Execution Results:")
        for i, row in enumerate(result.data[:5]):
            print(f"  {i+1}. {row}")
            
        # Check if values are different
        exposure_values = [row.get('[TotalAmount]', 0) for row in result.data[:5]]
        unique_values = set(exposure_values)
        if len(unique_values) > 1:
            print(f"\n🎉 SUCCESS! Found {len(unique_values)} different exposure values")
            print(f"    Range: {min(unique_values):,.0f} to {max(unique_values):,.0f}")
        else:
            print(f"\n⚠️  All customers have identical exposure: {list(unique_values)[0]:,.0f}")
    else:
        print(f"  • Error: {result.error_message}")
    
    if result.validation_issues:
        print(f"\n⚠️  Validation Issues ({len(result.validation_issues)}):")
        for issue in result.validation_issues:
            print(f"  • {issue}")
    
    print("\n" + "=" * 60)
    print("🎉 Clean DAX Engine full test completed!")
    print("=" * 60)