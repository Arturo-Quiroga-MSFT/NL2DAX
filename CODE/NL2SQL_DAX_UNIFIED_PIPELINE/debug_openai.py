#!/usr/bin/env python3
"""
debug_openai.py - Debug script for testing OpenAI API responses directly
=======================================================================

This script helps diagnose OpenAI API issues by testing various scenarios
and showing detailed response information including token usage.

Author: Unified Pipeline Team
Date: August 2025
"""

import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

def test_openai_direct():
    """Test OpenAI API directly with various scenarios"""
    print("🔍 Testing OpenAI API Direct Connection")
    print("=" * 50)
    
    # Initialize client
    try:
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        print(f"✅ Client initialized successfully")
        print(f"🔧 Configuration:")
        print(f"   Deployment: {deployment_name}")
        print(f"   Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
        print(f"   API Version: {os.getenv('AZURE_OPENAI_API_VERSION')}")
        
    except Exception as e:
        print(f"❌ Client initialization failed: {str(e)}")
        return
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Simple SQL Query",
            "system": "You are a helpful SQL expert.",
            "user": "Generate a simple SQL query to select all customers from a table called 'customers'.",
            "max_tokens": 500
        },
        {
            "name": "Complex SQL with Schema",
            "system": "You are an expert SQL developer. Generate accurate T-SQL queries for Azure SQL Database.",
            "user": "Given a table called FIS_CUSTOMER_DIMENSION with columns CUSTOMER_NAME, RISK_RATING_CODE, generate a query to find customers with lowest risk.",
            "max_tokens": 1000
        },
        {
            "name": "High Token Limit Test",
            "system": "You are a helpful assistant.",
            "user": "Explain what SQL is and provide a simple example.",
            "max_tokens": 2000
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"🧪 Test {i}: {scenario['name']}")
        print('='*60)
        
        try:
            print(f"🚀 Making API call with {scenario['max_tokens']} max tokens...")
            response = client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": scenario["system"]},
                    {"role": "user", "content": scenario["user"]}
                ],
                max_completion_tokens=scenario["max_tokens"],
                reasoning_effort="medium"
            )
            
            # Extract key information
            choice = response.choices[0]
            usage = response.usage
            content = choice.message.content
            
            print(f"✅ API call successful!")
            print(f"📊 Response Analysis:")
            print(f"   Finish Reason: {choice.finish_reason}")
            print(f"   Content Length: {len(content) if content else 0}")
            print(f"   Total Tokens: {usage.total_tokens}")
            print(f"   Prompt Tokens: {usage.prompt_tokens}")
            print(f"   Completion Tokens: {usage.completion_tokens}")
            
            if hasattr(usage.completion_tokens_details, 'reasoning_tokens'):
                print(f"   Reasoning Tokens: {usage.completion_tokens_details.reasoning_tokens}")
            
            print(f"\n📝 Content Preview:")
            if content:
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"   '{preview}'")
            else:
                print("   ❌ No content returned")
            
            # Analysis
            if choice.finish_reason == 'length':
                print("⚠️  WARNING: Response was truncated due to token limit")
            elif choice.finish_reason == 'stop':
                print("✅ Response completed successfully")
            
            if not content or len(content.strip()) == 0:
                print("❌ ISSUE: Empty content returned")
            
        except Exception as e:
            print(f"❌ Test {i} failed: {str(e)}")

def test_token_limits():
    """Test different token limits to find optimal settings"""
    print(f"\n{'='*60}")
    print("🔬 Token Limit Optimization Test")
    print('='*60)
    
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    token_limits = [100, 500, 1000, 1500, 2000, 3000]
    test_query = "Generate a SQL query to find the top 10 customers by risk rating from FIS_CUSTOMER_DIMENSION table."
    
    for limit in token_limits:
        try:
            print(f"\n🧪 Testing with {limit} max_completion_tokens...")
            response = client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": "You are an SQL expert."},
                    {"role": "user", "content": test_query}
                ],
                max_completion_tokens=limit,
                reasoning_effort="medium"
            )
            
            choice = response.choices[0]
            usage = response.usage
            content = choice.message.content
            
            status = "✅ SUCCESS" if choice.finish_reason == 'stop' and content else "❌ FAILED"
            content_length = len(content) if content else 0
            
            print(f"   {status} - Content: {content_length} chars, Finish: {choice.finish_reason}")
            
        except Exception as e:
            print(f"   ❌ FAILED - Error: {str(e)}")

def main():
    """Main debug function"""
    print("🧪 OpenAI API Debug Tool")
    print("=" * 60)
    
    # Test direct API
    test_openai_direct()
    
    # Test token limits
    test_token_limits()
    
    print("\n🏁 OpenAI debug session completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()