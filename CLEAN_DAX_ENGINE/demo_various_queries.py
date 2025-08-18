#!/usr/bin/env python3
"""
Demo script to test various query types with the Clean DAX Engine
"""

from main import CleanDAXEngine

def main():
    print("=" * 60)
    print("🚀 CLEAN DAX ENGINE - VARIOUS QUERY TYPES DEMO")
    print("=" * 60)
    
    # Initialize the engine
    engine = CleanDAXEngine()
    
    # Test different query types
    test_queries = [
        "Show me top 3 customers by total exposure",
        "List customers by total balance",
        "Show me top 5 customers by loan amounts", 
        "Display customers with highest principal balance"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔧 Test {i}: {query}")
        print("-" * 50)
        
        try:
            result = engine.process_request(query, limit=3)
            
            print(f"📝 Generated DAX Pattern: {result.pattern_used}")
            print(f"📊 Confidence: {result.confidence_score:.2f}")
            print(f"🎯 Execution Success: {'✅ YES' if result.execution_success else '❌ NO'}")
            
            if result.execution_success and result.data:
                print(f"📈 Results ({len(result.data)} rows):")
                for j, row in enumerate(result.data[:3], 1):
                    customer_name = row.get('[CustomerName]', 'Unknown')
                    total_amount = row.get('[TotalAmount]', 0)
                    print(f"  {j}. {customer_name}: {total_amount:,.0f}")
            
            if result.validation_issues:
                print(f"⚠️  Warnings: {len(result.validation_issues)}")
                for warning in result.validation_issues[:2]:  # Show first 2
                    print(f"  • {warning}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Demo completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()