# DAX Query Fix Recommendations

## Problem Analysis
The DAX query is generating inconsistent results compared to SQL due to improper relationship handling in SUMMARIZECOLUMNS.

## Current Problematic DAX Pattern
```dax
EVALUATE
SUMMARIZECOLUMNS(
    'FIS_CL_DETAIL_FACT'[CUSTOMER_KEY],
    'FIS_CUSTOMER_DIMENSION'[CUSTOMER_NAME],  -- Cross-product issue
    'FIS_CL_DETAIL_FACT'[PRINCIPAL_BALANCE],
    'FIS_CL_DETAIL_FACT'[LOAN_CURRENCY_CODE],
    FILTER(...)
)
```

## Recommended DAX Pattern Fixes

### Option 1: Use SELECTCOLUMNS with RELATED (Best for established relationships)
```dax
EVALUATE
TOPN(
    5,
    SELECTCOLUMNS(
        FILTER(
            'FIS_CL_DETAIL_FACT',
            'FIS_CL_DETAIL_FACT'[PRINCIPAL_BALANCE] >= 1000000 &&
            'FIS_CL_DETAIL_FACT'[LOAN_CURRENCY_CODE] = "USD"
        ),
        "Customer Key", 'FIS_CL_DETAIL_FACT'[CUSTOMER_KEY],
        "Customer Name", RELATED('FIS_CUSTOMER_DIMENSION'[CUSTOMER_NAME]),
        "Principal Balance", 'FIS_CL_DETAIL_FACT'[PRINCIPAL_BALANCE],
        "Currency", 'FIS_CL_DETAIL_FACT'[LOAN_CURRENCY_CODE]
    ),
    [Principal Balance],
    DESC
)
```

### Option 2: Use ADDCOLUMNS with LOOKUPVALUE (Explicit relationship)
```dax
EVALUATE
TOPN(
    5,
    ADDCOLUMNS(
        FILTER(
            'FIS_CL_DETAIL_FACT',
            'FIS_CL_DETAIL_FACT'[PRINCIPAL_BALANCE] >= 1000000 &&
            'FIS_CL_DETAIL_FACT'[LOAN_CURRENCY_CODE] = "USD"
        ),
        "Customer Name", 
        LOOKUPVALUE(
            'FIS_CUSTOMER_DIMENSION'[CUSTOMER_NAME],
            'FIS_CUSTOMER_DIMENSION'[CUSTOMER_KEY],
            'FIS_CL_DETAIL_FACT'[CUSTOMER_KEY]
        )
    ),
    'FIS_CL_DETAIL_FACT'[PRINCIPAL_BALANCE],
    DESC
)
```

### Option 3: Use SUMMARIZE with proper grouping (For aggregated results)
```dax
EVALUATE
TOPN(
    5,
    SUMMARIZE(
        FILTER(
            'FIS_CL_DETAIL_FACT',
            'FIS_CL_DETAIL_FACT'[PRINCIPAL_BALANCE] >= 1000000 &&
            'FIS_CL_DETAIL_FACT'[LOAN_CURRENCY_CODE] = "USD"
        ),
        'FIS_CL_DETAIL_FACT'[CUSTOMER_KEY],
        "Customer Name", 
        LOOKUPVALUE(
            'FIS_CUSTOMER_DIMENSION'[CUSTOMER_NAME],
            'FIS_CUSTOMER_DIMENSION'[CUSTOMER_KEY],
            'FIS_CL_DETAIL_FACT'[CUSTOMER_KEY]
        ),
        "Total Principal Balance", SUM('FIS_CL_DETAIL_FACT'[PRINCIPAL_BALANCE])
    ),
    [Total Principal Balance],
    DESC
)
```

## DAX Generator Prompt Improvements

The DAX generation prompt should include these specific patterns and avoid SUMMARIZECOLUMNS for cross-table queries.

### Updated Prompt Rules:
1. **NEVER use SUMMARIZECOLUMNS with columns from multiple tables unless relationships are guaranteed**
2. **Use SELECTCOLUMNS + RELATED() for detail rows with lookup columns**
3. **Use ADDCOLUMNS + LOOKUPVALUE() for explicit relationship handling**
4. **Use SUMMARIZE only for grouping within the same table or with explicit lookups**
5. **Always test relationship context before using cross-table references**

## Implementation Steps:
1. Update the DAX prompt template with these patterns
2. Add validation rules to detect cross-table SUMMARIZECOLUMNS usage
3. Test with known queries to ensure consistency
4. Document the approved DAX patterns for future reference