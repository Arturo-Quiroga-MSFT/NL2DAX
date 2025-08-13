# ❓ TEST QUESTIONS Directory

This directory contains curated sets of test questions and validation scenarios for the NL2DAX system, organized by complexity and domain area.

## 📋 Overview

The TEST QUESTIONS directory provides:
- Pre-built test cases for system validation
- Regression testing scenarios
- Performance benchmarking queries
- Domain-specific question sets
- Training examples for new users

## 📁 Current Contents

### nl2dax_star_schema_test_questions.txt

The primary test question file containing a comprehensive set of natural language queries designed to test various aspects of the NL2DAX system.

**Question Categories:**

1. **Basic Aggregations**
   - Simple SUM, COUNT, AVG operations
   - Single table queries
   - Fundamental DAX patterns

2. **Multi-table Joins**
   - Fact-to-dimension relationships
   - Complex join scenarios
   - Relationship navigation in DAX

3. **Filtering and Segmentation**
   - WHERE clause equivalents
   - Conditional aggregations
   - Time-based filtering

4. **Top N Queries**
   - TOPN DAX function testing
   - ORDER BY scenarios
   - Ranking and percentile queries

5. **Complex Analytics**
   - Ratio calculations
   - Year-over-year analysis
   - Running totals and cumulative metrics

## 🎯 Test Question Structure

Each test question follows this format:

```
=== TEST CASE #[NUMBER] ===
Category: [CATEGORY_NAME]
Complexity: [BASIC|INTERMEDIATE|ADVANCED]
Expected Tables: [TABLE_NAMES]
Expected Functions: [DAX_FUNCTIONS]

Question: [NATURAL_LANGUAGE_QUESTION]

Expected DAX Pattern:
[SAMPLE_DAX_STRUCTURE]

Expected SQL Pattern:
[SAMPLE_SQL_STRUCTURE]

Success Criteria:
- [CRITERION_1]
- [CRITERION_2]
- [CRITERION_3]

Notes: [ADDITIONAL_INFORMATION]
```

## 📊 Test Categories

### Financial Risk Analysis

**Questions covering:**
- NPL (Non-Performing Loan) ratio calculations
- Risk rating distributions
- Exposure analysis by geography
- Credit limit utilization

**Example questions:**
```
"What is the NPL ratio by country and risk rating?"
"Show me the top 10 countries by total exposure"
"Calculate the average credit utilization by risk rating"
```

### Customer Analytics

**Questions covering:**
- Customer segmentation
- Geographic distribution
- Balance analysis
- Portfolio composition

**Example questions:**
```
"List the top 5 customers by total balance"
"Show customers located in the United States"
"What is the average balance per customer by country?"
```

### Temporal Analysis

**Questions covering:**
- Time-series analysis
- Period-over-period comparisons
- Trend calculations
- Seasonal patterns

**Example questions:**
```
"Show monthly balance trends for the last year"
"Compare this quarter's NPL ratio to last quarter"
"What was the total exposure in December 2024?"
```

### Performance Testing

**Questions covering:**
- Large result set handling
- Complex calculation performance
- Multi-dimensional analysis
- Resource utilization

**Example questions:**
```
"Calculate exposure for all customers across all periods"
"Show detailed breakdown by customer, country, and month"
"Generate comprehensive risk report with all metrics"
```

## 🧪 Testing Methodologies

### Automated Testing

```bash
# Run all test questions
python ../CODE/run_test_suite.py --input nl2dax_star_schema_test_questions.txt

# Run specific category
python ../CODE/run_test_suite.py --category "Financial Risk Analysis"

# Performance testing
python ../CODE/run_test_suite.py --benchmark --iterations 5
```

### Manual Testing

```bash
# Interactive testing with specific questions
python ../CODE/main.py < nl2dax_star_schema_test_questions.txt

# Single question testing
echo "What is the total balance by country?" | python ../CODE/main.py
```

### Regression Testing

```bash
# Compare results with baseline
python ../CODE/regression_test.py --baseline baseline_results.json --current current_run.json

# Generate regression report
python ../CODE/generate_regression_report.py --results regression_results/
```

## 📈 Test Metrics

### Success Criteria

**Query Generation:**
- ✅ Valid DAX syntax (100% target)
- ✅ Valid SQL syntax (100% target)
- ✅ Appropriate table selection (95% target)
- ✅ Correct aggregation functions (90% target)

**Execution Success:**
- ✅ SQL execution without errors (95% target)
- ✅ DAX execution without errors (85% target)
- ✅ Results returned within timeout (90% target)
- ✅ Non-empty result sets (85% target)

**Result Quality:**
- ✅ Logically consistent results (95% target)
- ✅ Expected data types (100% target)
- ✅ Reasonable value ranges (90% target)
- ✅ Matching SQL/DAX results (80% target)

### Performance Benchmarks

**Response Time Targets:**
- Simple queries: < 2 seconds
- Moderate complexity: < 5 seconds
- Complex analytics: < 15 seconds
- Large result sets: < 30 seconds

**Resource Usage:**
- Memory usage: < 500MB per query
- CPU utilization: < 80% peak
- Database connections: < 10 concurrent

## 🔍 Test Question Development

### Creating New Test Questions

1. **Identify Gap Areas**
   ```bash
   # Analyze current coverage
   python ../CODE/analyze_test_coverage.py
   ```

2. **Design Question Structure**
   - Start with business requirement
   - Define expected behavior
   - Specify success criteria
   - Include edge cases

3. **Validate Questions**
   ```bash
   # Test new questions before adding to suite
   python ../CODE/validate_question.py --question "New test question"
   ```

### Question Categories to Expand

**Needed additions:**
- Error handling scenarios
- Edge case testing (empty results, null values)
- Data type testing (dates, decimals, strings)
- Security testing (injection attempts)
- Performance stress testing

**Complex scenarios:**
- Multi-step analytical processes
- Conditional logic testing
- Advanced DAX functions (CALCULATE, FILTER, etc.)
- Window functions and ranking

## 📋 Test Execution Workflows

### Daily Smoke Testing

```bash
#!/bin/bash
# Run essential test cases daily
python ../CODE/run_test_suite.py \
  --category "Basic Aggregations" \
  --quick-mode \
  --output daily_smoke_$(date +%Y%m%d).log
```

### Weekly Regression Testing

```bash
#!/bin/bash
# Comprehensive weekly testing
python ../CODE/run_test_suite.py \
  --full-suite \
  --benchmark \
  --generate-report \
  --output weekly_regression_$(date +%Y-%W).html
```

### Release Validation

```bash
#!/bin/bash
# Pre-release comprehensive testing
python ../CODE/run_test_suite.py \
  --all-categories \
  --performance-testing \
  --error-injection \
  --generate-detailed-report \
  --output release_validation_$(date +%Y%m%d).json
```

## 🎯 Best Practices

### Test Question Design

1. **Clarity and Specificity**
   - Use clear, unambiguous language
   - Specify exact requirements
   - Include expected result characteristics

2. **Coverage Completeness**
   - Test all major DAX functions
   - Cover all table relationships
   - Include error scenarios

3. **Realistic Business Context**
   - Use domain-appropriate terminology
   - Mirror real user questions
   - Include common analytical patterns

### Test Maintenance

1. **Regular Updates**
   - Add questions for new features
   - Remove obsolete test cases
   - Update expected results for schema changes

2. **Performance Monitoring**
   - Track execution time trends
   - Identify performance regressions
   - Optimize slow test cases

3. **Result Validation**
   - Regularly verify expected outcomes
   - Update baselines for legitimate changes
   - Investigate unexpected result variations

## 📊 Test Results Analysis

### Historical Tracking

```bash
# Generate trend analysis
python ../CODE/analyze_test_trends.py --period 30days

# Compare different versions
python ../CODE/compare_test_results.py --baseline v1.0 --current v1.1
```

### Common Failure Patterns

**Typical issues identified:**
- Schema evolution breaking old questions
- Performance degradation with complex queries
- Authentication failures with XMLA endpoints
- Network timeouts with large result sets

### Success Rate Monitoring

```bash
# Generate success rate dashboard
python ../CODE/generate_test_dashboard.py --output test_dashboard.html

# Track specific metrics
python ../CODE/track_test_metrics.py --metric success_rate --period weekly
```

## 🔮 Future Enhancements

### Planned Improvements

1. **Interactive Test Builder**
   - Web interface for creating test questions
   - Guided question construction
   - Automatic validation and suggestion

2. **AI-Powered Test Generation**
   - Generate test questions from schema
   - Create edge cases automatically
   - Suggest test coverage improvements

3. **Advanced Analytics**
   - Machine learning for result validation
   - Anomaly detection in test results
   - Predictive performance modeling

---

💡 **Tip**: Use the test questions as training examples when onboarding new users. They demonstrate effective natural language patterns that work well with the system.
