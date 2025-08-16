# 📊 NL2DAX Pipeline Execution Report

**Generated:** August 15, 2025 at 04:50:04 PM
**Query:** Which customers are located in the United States?

---

## 📋 Executive Summary

| Metric | Value |
|--------|--------|
| **SQL Execution** | ✅ Success |
| **DAX Execution** | ✅ Success |
| **SQL Rows Returned** | 7 |
| **DAX Rows Returned** | 7 |
| **Total Execution Time** | 0.00s |
| **Errors Encountered** | 0 |

## 🔍 Query Analysis

**Original Query:** `Which customers are located in the United States?`

| Attribute | Value |
|-----------|--------|
| **Character Count** | 49 |
| **Word Count** | 8 |
| **Detected Features** | Basic query |

## 🧠 Intent & Entity Extraction

### Extracted Intent and Entities

```json
{
  "intent": "get_customers_by_location",
  "entities": {
    "table": "FIS_CUSTOMER_DIMENSION",
    "filter_field": "COUNTRY_DESCRIPTION",
    "filter_value": "United States"
  }
}
```

## 🚀 Cache Performance

| Cache Type | Hits | Misses | Hit Rate |
|------------|------|--------|----------|
| **Intent Parsing** | 0 | 0 | N/A% |
| **SQL Generation** | 0 | 0 | N/A% |
| **DAX Generation** | 0 | 0 | N/A% |

## 🗄️ SQL Generation & Execution

### Generated SQL Query

```sql
SELECT
    CUSTOMER_KEY,
    CUSTOMER_ID,
    CUSTOMER_NAME,
    CUSTOMER_SHORT_NAME,
    CUSTOMER_TYPE_CODE,
    CUSTOMER_TYPE_DESCRIPTION,
    COUNTRY_CODE,
    COUNTRY_DESCRIPTION,
    STATE_CODE,
    STATE_DESCRIPTION,
    CITY,
    POSTAL_CODE,
    INDUSTRY_CODE,
    INDUSTRY_DESCRIPTION,
    RELATIONSHIP_MANAGER,
    CUSTOMER_STATUS,
    ESTABLISHED_DATE
FROM FIS_CUSTOMER_DIMENSION
WHERE COUNTRY_DESCRIPTION = 'United States'
ORDER BY CUSTOMER_NAME;
```

### SQL Execution Results

**Rows Returned:** 7
**Execution Time:** 0.00 seconds

**SQL Results (First 5 Rows)**

| CUSTOMER_KEY | CUSTOMER_ID | CUSTOMER_NAME | CUSTOMER_SHORT_NAME | CUSTOMER_TYPE_CODE | CUSTOMER_TYPE_DESCRIPTION | COUNTRY_CODE | COUNTRY_DESCRIPTION | STATE_CODE | STATE_DESCRIPTION | CITY | POSTAL_CODE | INDUSTRY_CODE | INDUSTRY_DESCRIPTION | RELATIONSHIP_MANAGER | CUSTOMER_STATUS | ESTABLISHED_DATE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1002 | CUST005 | Atlantic Biomedical Corporation | Atlantic Bio | CORP | Corporation | US | United States | FL | Florida | Miami | 33101 | 2800 | Pharmaceutical and Medical Devices | Jennifer Martinez | Active | 2017-06-14 |
| 1 | CUST001 | Desert Manufacturing LLC | Desert Mfg | CORP | Corporation | US | United States | NY | New York | New York | 10001 | 3100 | Manufacturing - Industrial Equipment | Sarah Johnson | Active | 2018-03-15 |
| 1003 | CUST006 | Mountain Capital Advisors LLC | Mountain Cap | LLC | Limited Liability Company | US | United States | CO | Colorado | Denver | 80202 | 5200 | Financial Services and Investment Management | Robert Thompson | Active | 2021-03-08 |
| 1004 | CUST007 | Northwest Retail Enterprises Inc. | NW Retail | CORP | Corporation | US | United States | WA | Washington | Seattle | 98101 | 4400 | Retail and Consumer Goods | Amanda Foster | Active | 2016-12-02 |
| 4 | CUST004 | Pacific Technology Solutions | Pac Tech | CORP | Corporation | US | United States | CA | California | Los Angeles | 90001 | 5400 | Technology Services | David Kim | Active | 2019-11-08 |

## ⚡ DAX Generation & Execution

### Generated DAX Query

```dax
EVALUATE
FILTER(
    'FIS_CUSTOMER_DIMENSION',
    'FIS_CUSTOMER_DIMENSION'[COUNTRY_DESCRIPTION] = "United States"
    )
```

### DAX Execution Results

**Rows Returned:** 7
**Execution Time:** 0.00 seconds

**DAX Results (First 5 Rows)**

| FIS_CUSTOMER_DIMENSION[CUSTOMER_KEY] | FIS_CUSTOMER_DIMENSION[CUSTOMER_ID] | FIS_CUSTOMER_DIMENSION[CUSTOMER_NAME] | FIS_CUSTOMER_DIMENSION[CUSTOMER_SHORT_NAME] | FIS_CUSTOMER_DIMENSION[CUSTOMER_TYPE_CODE] | FIS_CUSTOMER_DIMENSION[CUSTOMER_TYPE_DESCRIPTION] | FIS_CUSTOMER_DIMENSION[INDUSTRY_CODE] | FIS_CUSTOMER_DIMENSION[INDUSTRY_DESCRIPTION] | FIS_CUSTOMER_DIMENSION[COUNTRY_CODE] | FIS_CUSTOMER_DIMENSION[COUNTRY_DESCRIPTION] | FIS_CUSTOMER_DIMENSION[STATE_CODE] | FIS_CUSTOMER_DIMENSION[STATE_DESCRIPTION] | FIS_CUSTOMER_DIMENSION[CITY] | FIS_CUSTOMER_DIMENSION[POSTAL_CODE] | FIS_CUSTOMER_DIMENSION[RISK_RATING_CODE] | FIS_CUSTOMER_DIMENSION[RISK_RATING_DESCRIPTION] | FIS_CUSTOMER_DIMENSION[CUSTOMER_STATUS] | FIS_CUSTOMER_DIMENSION[ESTABLISHED_DATE] | FIS_CUSTOMER_DIMENSION[RELATIONSHIP_MANAGER] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1002 | CUST005 | Atlantic Biomedical Corporation | Atlantic Bio | CORP | Corporation | 2800 | Pharmaceutical and Medical Devices | US | United States | FL | Florida | Miami | 33101 | A- | Strong Credit Quality | Active | 2017-06-14T00:00:00 | Jennifer Martinez |
| 1003 | CUST006 | Mountain Capital Advisors LLC | Mountain Cap | LLC | Limited Liability Company | 5200 | Financial Services and Investment Management | US | United States | CO | Colorado | Denver | 80202 | B+ | Good Credit Quality | Active | 2021-03-08T00:00:00 | Robert Thompson |
| 1004 | CUST007 | Northwest Retail Enterprises Inc. | NW Retail | CORP | Corporation | 4400 | Retail and Consumer Goods | US | United States | WA | Washington | Seattle | 98101 | B | Satisfactory Credit Quality | Active | 2016-12-02T00:00:00 | Amanda Foster |
| 1 | CUST001 | Desert Manufacturing LLC | Desert Mfg | CORP | Corporation | 3100 | Manufacturing - Industrial Equipment | US | United States | NY | New York | New York | 10001 | B+ | Good Credit Quality | Active | 2018-03-15T00:00:00 | Sarah Johnson |
| 2 | CUST002 | Palm Investors Inc. | Palm Invest | CORP | Corporation | 6200 | Real Estate Investment | US | United States | TX | Texas | Dallas | 75201 | A- | Strong Credit Quality | Active | 2015-09-22T00:00:00 | Michael Chen |

## ⏱️ Performance Metrics

| Operation | Time (seconds) | Percentage |
|-----------|----------------|------------|
| **SQL Generation & Execution** | 0.00s | 0.0% |
| **DAX Generation & Execution** | 0.00s | 0.0% |
| **Total Pipeline Time** | 0.00s | 100% |

## 💡 Recommendations

- Pipeline executed successfully with no specific recommendations

---

*Report generated by NL2DAX Pipeline v1.0*

*Generated on August 15, 2025 at 04:50:04 PM*