# Expected Query Examples for Enhanced Dataset
*Sample SQL and DAX queries that should be generated for key test questions*

## 🔍 Query Generation Examples

### 1. Geographic Customer Distribution

#### Test Question: "Show me the distribution of customers by country and their risk ratings"

**Expected SQL:**
```sql
SELECT 
    cd.CUSTOMER_COUNTRY,
    cd.CUSTOMER_RISK_RATING,
    COUNT(*) as customer_count,
    AVG(CAST(cd.CUSTOMER_RISK_RATING AS DECIMAL)) as avg_risk_rating
FROM FIS_CUSTOMER_DIMENSION cd
WHERE cd.CUSTOMER_COUNTRY IS NOT NULL
GROUP BY cd.CUSTOMER_COUNTRY, cd.CUSTOMER_RISK_RATING
ORDER BY cd.CUSTOMER_COUNTRY, cd.CUSTOMER_RISK_RATING;
```

**Expected DAX:**
```dax
EVALUATE
SUMMARIZECOLUMNS(
    FIS_CUSTOMER_DIMENSION[CUSTOMER_COUNTRY],
    FIS_CUSTOMER_DIMENSION[CUSTOMER_RISK_RATING],
    "CustomerCount", COUNTROWS(FIS_CUSTOMER_DIMENSION),
    "AvgRiskRating", AVERAGE(FIS_CUSTOMER_DIMENSION[CUSTOMER_RISK_RATING])
)
ORDER BY FIS_CUSTOMER_DIMENSION[CUSTOMER_COUNTRY], FIS_CUSTOMER_DIMENSION[CUSTOMER_RISK_RATING]
```

### 2. Multi-Currency Loan Portfolio

#### Test Question: "What is our total loan portfolio exposure by currency?"

**Expected SQL:**
```sql
SELECT 
    lpd.LOAN_CURRENCY_CODE,
    lpd.LOAN_CURRENCY_DESCRIPTION,
    COUNT(*) as loan_count,
    SUM(lpd.ORIGINAL_AMOUNT) as total_exposure,
    AVG(lpd.ORIGINAL_AMOUNT) as avg_loan_size
FROM FIS_LOAN_PRODUCT_DIMENSION lpd
GROUP BY lpd.LOAN_CURRENCY_CODE, lpd.LOAN_CURRENCY_DESCRIPTION
ORDER BY total_exposure DESC;
```

**Expected DAX:**
```dax
EVALUATE
SUMMARIZECOLUMNS(
    FIS_LOAN_PRODUCT_DIMENSION[LOAN_CURRENCY_CODE],
    FIS_LOAN_PRODUCT_DIMENSION[LOAN_CURRENCY_DESCRIPTION],
    "LoanCount", COUNTROWS(FIS_LOAN_PRODUCT_DIMENSION),
    "TotalExposure", SUM(FIS_LOAN_PRODUCT_DIMENSION[ORIGINAL_AMOUNT]),
    "AvgLoanSize", AVERAGE(FIS_LOAN_PRODUCT_DIMENSION[ORIGINAL_AMOUNT])
)
ORDER BY [TotalExposure] DESC
```

### 3. International Customer Analysis

#### Test Question: "List all international customers with their primary business sectors and total exposure"

**Expected SQL:**
```sql
SELECT 
    cd.CUSTOMER_ID,
    cd.CUSTOMER_NAME,
    cd.CUSTOMER_COUNTRY,
    cd.CUSTOMER_BUSINESS_SECTOR,
    cd.CUSTOMER_RISK_RATING,
    COALESCE(loan_summary.total_loan_exposure, 0) as total_loan_exposure,
    COALESCE(ca_summary.total_facility_commitment, 0) as total_facility_commitment,
    COALESCE(loan_summary.total_loan_exposure, 0) + COALESCE(ca_summary.total_facility_commitment, 0) as total_exposure
FROM FIS_CUSTOMER_DIMENSION cd
LEFT JOIN (
    SELECT 
        lpd.CA_CUSTOMER_ID,
        SUM(lpd.ORIGINAL_AMOUNT) as total_loan_exposure
    FROM FIS_LOAN_PRODUCT_DIMENSION lpd
    GROUP BY lpd.CA_CUSTOMER_ID
) loan_summary ON cd.CUSTOMER_ID = loan_summary.CA_CUSTOMER_ID
LEFT JOIN (
    SELECT 
        ca.CA_CUSTOMER_ID,
        SUM(ca.COMMITMENT_AMOUNT) as total_facility_commitment
    FROM FIS_CA_PRODUCT_DIMENSION ca
    GROUP BY ca.CA_CUSTOMER_ID
) ca_summary ON cd.CUSTOMER_ID = ca_summary.CA_CUSTOMER_ID
WHERE cd.CUSTOMER_COUNTRY != 'United States'
ORDER BY total_exposure DESC;
```

**Expected DAX:**
```dax
EVALUATE
ADDCOLUMNS(
    FILTER(
        FIS_CUSTOMER_DIMENSION,
        FIS_CUSTOMER_DIMENSION[CUSTOMER_COUNTRY] <> "United States"
    ),
    "TotalLoanExposure", 
    CALCULATE(
        SUM(FIS_LOAN_PRODUCT_DIMENSION[ORIGINAL_AMOUNT]),
        RELATED(FIS_LOAN_PRODUCT_DIMENSION[CA_CUSTOMER_ID]) = FIS_CUSTOMER_DIMENSION[CUSTOMER_ID]
    ),
    "TotalFacilityCommitment",
    CALCULATE(
        SUM(FIS_CA_PRODUCT_DIMENSION[COMMITMENT_AMOUNT]),
        RELATED(FIS_CA_PRODUCT_DIMENSION[CA_CUSTOMER_ID]) = FIS_CUSTOMER_DIMENSION[CUSTOMER_ID]
    ),
    "TotalExposure",
    [TotalLoanExposure] + [TotalFacilityCommitment]
)
ORDER BY [TotalExposure] DESC
```

### 4. Credit Facility Utilization by Country

#### Test Question: "What are the utilization rates for credit facilities by country?"

**Expected SQL:**
```sql
SELECT 
    ca.CA_COUNTRY_OF_EXPOSURE_RISK as country,
    COUNT(*) as facility_count,
    SUM(ca.COMMITMENT_AMOUNT) as total_commitment,
    SUM(ca.AVAILABLE_AMOUNT) as total_available,
    SUM(ca.COMMITMENT_AMOUNT - ca.AVAILABLE_AMOUNT) as total_utilized,
    CASE 
        WHEN SUM(ca.COMMITMENT_AMOUNT) > 0 
        THEN (SUM(ca.COMMITMENT_AMOUNT - ca.AVAILABLE_AMOUNT) / SUM(ca.COMMITMENT_AMOUNT)) * 100
        ELSE 0 
    END as utilization_rate_percent
FROM FIS_CA_PRODUCT_DIMENSION ca
WHERE ca.CA_OVERALL_STATUS_CODE = 'A'
GROUP BY ca.CA_COUNTRY_OF_EXPOSURE_RISK
ORDER BY utilization_rate_percent DESC;
```

**Expected DAX:**
```dax
EVALUATE
ADDCOLUMNS(
    SUMMARIZECOLUMNS(
        FIS_CA_PRODUCT_DIMENSION[CA_COUNTRY_OF_EXPOSURE_RISK],
        FILTER(FIS_CA_PRODUCT_DIMENSION, FIS_CA_PRODUCT_DIMENSION[CA_OVERALL_STATUS_CODE] = "A"),
        "FacilityCount", COUNTROWS(FIS_CA_PRODUCT_DIMENSION),
        "TotalCommitment", SUM(FIS_CA_PRODUCT_DIMENSION[COMMITMENT_AMOUNT]),
        "TotalAvailable", SUM(FIS_CA_PRODUCT_DIMENSION[AVAILABLE_AMOUNT])
    ),
    "TotalUtilized", [TotalCommitment] - [TotalAvailable],
    "UtilizationRatePercent", 
    IF([TotalCommitment] > 0, 
       ([TotalCommitment] - [TotalAvailable]) / [TotalCommitment] * 100, 
       0)
)
ORDER BY [UtilizationRatePercent] DESC
```

### 5. Emerging Markets Analysis

#### Test Question: "Show me customers from emerging markets (Mexico, Brazil, Argentina, Colombia) and their credit profiles"

**Expected SQL:**
```sql
SELECT 
    cd.CUSTOMER_ID,
    cd.CUSTOMER_NAME,
    cd.CUSTOMER_COUNTRY,
    cd.CUSTOMER_BUSINESS_SECTOR,
    cd.CUSTOMER_RISK_RATING,
    cd.CUSTOMER_ANNUAL_REVENUE,
    COUNT(DISTINCT lpd.LOAN_PRODUCT_KEY) as loan_count,
    COUNT(DISTINCT ca.CA_PRODUCT_KEY) as facility_count,
    COALESCE(SUM(lpd.ORIGINAL_AMOUNT), 0) as total_loans,
    COALESCE(SUM(ca.COMMITMENT_AMOUNT), 0) as total_facilities
FROM FIS_CUSTOMER_DIMENSION cd
LEFT JOIN FIS_LOAN_PRODUCT_DIMENSION lpd ON cd.CUSTOMER_ID = lpd.CA_CUSTOMER_ID
LEFT JOIN FIS_CA_PRODUCT_DIMENSION ca ON cd.CUSTOMER_ID = ca.CA_CUSTOMER_ID
WHERE cd.CUSTOMER_COUNTRY IN ('Mexico', 'Brazil', 'Argentina', 'Colombia')
GROUP BY cd.CUSTOMER_ID, cd.CUSTOMER_NAME, cd.CUSTOMER_COUNTRY, 
         cd.CUSTOMER_BUSINESS_SECTOR, cd.CUSTOMER_RISK_RATING, cd.CUSTOMER_ANNUAL_REVENUE
ORDER BY cd.CUSTOMER_COUNTRY, total_loans + total_facilities DESC;
```

**Expected DAX:**
```dax
EVALUATE
ADDCOLUMNS(
    FILTER(
        FIS_CUSTOMER_DIMENSION,
        FIS_CUSTOMER_DIMENSION[CUSTOMER_COUNTRY] IN {"Mexico", "Brazil", "Argentina", "Colombia"}
    ),
    "LoanCount", 
    CALCULATE(DISTINCTCOUNT(FIS_LOAN_PRODUCT_DIMENSION[LOAN_PRODUCT_KEY])),
    "FacilityCount",
    CALCULATE(DISTINCTCOUNT(FIS_CA_PRODUCT_DIMENSION[CA_PRODUCT_KEY])),
    "TotalLoans",
    CALCULATE(SUM(FIS_LOAN_PRODUCT_DIMENSION[ORIGINAL_AMOUNT])),
    "TotalFacilities",
    CALCULATE(SUM(FIS_CA_PRODUCT_DIMENSION[COMMITMENT_AMOUNT])),
    "TotalExposure",
    [TotalLoans] + [TotalFacilities]
)
ORDER BY FIS_CUSTOMER_DIMENSION[CUSTOMER_COUNTRY], [TotalExposure] DESC
```

### 6. Loan Maturity Analysis

#### Test Question: "Show me loans maturing in the next 12 months by currency"

**Expected SQL:**
```sql
SELECT 
    lpd.LOAN_CURRENCY_CODE,
    lpd.LOAN_CURRENCY_DESCRIPTION,
    COUNT(*) as maturing_loans,
    SUM(lpd.ORIGINAL_AMOUNT) as maturing_amount,
    STRING_AGG(CONCAT(lpd.OBLIGATION_NUMBER, ' (', cd.CUSTOMER_NAME, ')'), '; ') as loan_details
FROM FIS_LOAN_PRODUCT_DIMENSION lpd
LEFT JOIN FIS_CUSTOMER_DIMENSION cd ON lpd.CA_CUSTOMER_ID = cd.CUSTOMER_ID
WHERE lpd.LEGAL_MATURITY_DATE BETWEEN GETDATE() AND DATEADD(MONTH, 12, GETDATE())
GROUP BY lpd.LOAN_CURRENCY_CODE, lpd.LOAN_CURRENCY_DESCRIPTION
ORDER BY maturing_amount DESC;
```

**Expected DAX:**
```dax
EVALUATE
SUMMARIZECOLUMNS(
    FIS_LOAN_PRODUCT_DIMENSION[LOAN_CURRENCY_CODE],
    FIS_LOAN_PRODUCT_DIMENSION[LOAN_CURRENCY_DESCRIPTION],
    FILTER(
        FIS_LOAN_PRODUCT_DIMENSION,
        FIS_LOAN_PRODUCT_DIMENSION[LEGAL_MATURITY_DATE] >= TODAY() &&
        FIS_LOAN_PRODUCT_DIMENSION[LEGAL_MATURITY_DATE] <= EDATE(TODAY(), 12)
    ),
    "MaturingLoans", COUNTROWS(FIS_LOAN_PRODUCT_DIMENSION),
    "MaturingAmount", SUM(FIS_LOAN_PRODUCT_DIMENSION[ORIGINAL_AMOUNT])
)
ORDER BY [MaturingAmount] DESC
```

### 7. Product Diversification Analysis

#### Test Question: "Which international customers have the most diversified product relationships?"

**Expected SQL:**
```sql
WITH customer_products AS (
    SELECT 
        cd.CUSTOMER_ID,
        cd.CUSTOMER_NAME,
        cd.CUSTOMER_COUNTRY,
        COUNT(DISTINCT lpd.PRODUCT_TYPE_CODE) as loan_product_types,
        COUNT(DISTINCT ca.CA_PRODUCT_TYPE_CODE) as facility_product_types,
        COUNT(DISTINCT lpd.LOAN_CURRENCY_CODE) as loan_currencies,
        COUNT(DISTINCT ca.CA_CURRENCY_CODE) as facility_currencies
    FROM FIS_CUSTOMER_DIMENSION cd
    LEFT JOIN FIS_LOAN_PRODUCT_DIMENSION lpd ON cd.CUSTOMER_ID = lpd.CA_CUSTOMER_ID
    LEFT JOIN FIS_CA_PRODUCT_DIMENSION ca ON cd.CUSTOMER_ID = ca.CA_CUSTOMER_ID
    WHERE cd.CUSTOMER_COUNTRY != 'United States'
    GROUP BY cd.CUSTOMER_ID, cd.CUSTOMER_NAME, cd.CUSTOMER_COUNTRY
)
SELECT 
    *,
    (loan_product_types + facility_product_types) as total_product_types,
    (loan_currencies + facility_currencies) as total_currencies,
    (loan_product_types + facility_product_types + loan_currencies + facility_currencies) as diversification_score
FROM customer_products
WHERE (loan_product_types + facility_product_types) > 0
ORDER BY diversification_score DESC;
```

**Expected DAX:**
```dax
EVALUATE
ADDCOLUMNS(
    FILTER(
        FIS_CUSTOMER_DIMENSION,
        FIS_CUSTOMER_DIMENSION[CUSTOMER_COUNTRY] <> "United States"
    ),
    "LoanProductTypes",
    CALCULATE(DISTINCTCOUNT(FIS_LOAN_PRODUCT_DIMENSION[PRODUCT_TYPE_CODE])),
    "FacilityProductTypes", 
    CALCULATE(DISTINCTCOUNT(FIS_CA_PRODUCT_DIMENSION[CA_PRODUCT_TYPE_CODE])),
    "LoanCurrencies",
    CALCULATE(DISTINCTCOUNT(FIS_LOAN_PRODUCT_DIMENSION[LOAN_CURRENCY_CODE])),
    "FacilityCurrencies",
    CALCULATE(DISTINCTCOUNT(FIS_CA_PRODUCT_DIMENSION[CA_CURRENCY_CODE])),
    "TotalProductTypes", [LoanProductTypes] + [FacilityProductTypes],
    "TotalCurrencies", [LoanCurrencies] + [FacilityCurrencies],
    "DiversificationScore", [TotalProductTypes] + [TotalCurrencies]
)
ORDER BY [DiversificationScore] DESC
```

## 🎯 Key Query Patterns

### Common Joins Expected:
1. **Customer + Loans**: `FIS_CUSTOMER_DIMENSION` ↔ `FIS_LOAN_PRODUCT_DIMENSION`
2. **Customer + Facilities**: `FIS_CUSTOMER_DIMENSION` ↔ `FIS_CA_PRODUCT_DIMENSION`
3. **Multi-table Analysis**: All three tables joined for comprehensive views

### Expected Aggregations:
- **COUNT(*)**: Record counts
- **SUM()**: Financial amounts
- **AVG()**: Average calculations
- **MIN/MAX()**: Range analysis
- **DISTINCTCOUNT()**: Unique value counting

### Expected Filters:
- **Geographic**: Country filtering and grouping
- **Currency**: Multi-currency analysis
- **Date**: Maturity and origination filtering
- **Risk**: Customer risk rating analysis
- **Status**: Active vs inactive products

### Expected Calculations:
- **Utilization Rates**: (Commitment - Available) / Commitment
- **Risk Aggregations**: Average risk by geography
- **Currency Totals**: Sum amounts by currency
- **Diversification Metrics**: Count of distinct products/currencies

---

*These examples represent the expected sophistication level for queries generated by the enhanced NL2DAX pipeline using our international dataset.*