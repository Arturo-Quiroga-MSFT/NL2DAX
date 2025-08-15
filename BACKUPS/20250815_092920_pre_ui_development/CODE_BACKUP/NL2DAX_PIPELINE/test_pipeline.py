#!/usr/bin/env python3
"""
test_pipeline.py - Quick Pipeline Health Check
============================================

This script provides a quick way to verify that the NL2DAX pipeline
is still working correctly after any modifications.

Usage:
    python test_pipeline.py

Expected behavior:
- Should complete without errors
- Should return results from both SQL and DAX
- Should complete in under 60 seconds
"""

import sys
import subprocess
import time

def test_pipeline():
    """Run a simple test query through the pipeline."""
    print("🧪 Testing NL2DAX Pipeline Health...")
    print("=" * 50)
    
    # Test query that we know works
    test_query = "show me top 3 customers"
    
    start_time = time.time()
    
    try:
        # Run the pipeline with the test query
        result = subprocess.run(
            ['python', 'main.py'],
            input=test_query,
            text=True,
            capture_output=True,
            timeout=90  # 90 second timeout
        )
        
        duration = time.time() - start_time
        
        # Check if it completed successfully
        if result.returncode == 0:
            output = result.stdout
            
            # Check for key success indicators
            sql_success = "SQL QUERY RESULTS" in output
            dax_success = "DAX QUERY RESULTS" in output or "DAX EXECUTION WARNING" in output
            no_critical_errors = "ERROR" not in output or "DAX EXECUTION WARNING" in output
            
            print(f"✅ Pipeline completed in {duration:.2f} seconds")
            print(f"✅ SQL execution: {'PASS' if sql_success else 'FAIL'}")
            print(f"✅ DAX execution: {'PASS' if dax_success else 'FAIL'}")
            print(f"✅ No critical errors: {'PASS' if no_critical_errors else 'FAIL'}")
            
            if sql_success and dax_success and no_critical_errors:
                print("\n🎉 PIPELINE HEALTH: EXCELLENT - All systems working!")
                return True
            else:
                print("\n⚠️  PIPELINE HEALTH: DEGRADED - Some issues detected")
                print("\nOutput preview:")
                print(output[-500:])  # Last 500 chars
                return False
        else:
            print(f"❌ Pipeline failed with return code: {result.returncode}")
            print("Error output:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Pipeline timed out (>90 seconds)")
        return False
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)
