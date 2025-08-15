/*
SQL Queries for FIS_CUSTOMER_DIMENSION Table
============================================

This file contains various SQL queries to explore and analyze the
customer dimension table in your Azure SQL Database.

Generated: August 15, 2025
Purpose: Explore customer data in Azure SQL Database for NL2DAX pipeline
Database: aqsqlserver001.database.windows.net/adventureworksdb
*/

-- ====================================================================
-- QUERY 1: Show all customers and their names (basic)
-- ====================================================================
-- Simple query to see customer keys and names

SELECT 
    CUSTOMER_KEY,
    CUSTOMER_NAME
FROM FIS_CUSTOMER_DIMENSION
ORDER BY CUSTOMER_NAME;

-- ====================================================================
-- QUERY 2: Show all customers with key information
-- ====================================================================
-- More detailed view of customer data

SELECT 
    CUSTOMER_KEY,
    CUSTOMER_NAME,
    CUSTOMER_TYPE,
    COUNTRY,
    INDUSTRY,
    RISK_RATING,
    BUSINESS_UNIT
FROM FIS_CUSTOMER_DIMENSION
ORDER BY CUSTOMER_NAME;

-- ====================================================================
-- QUERY 3: Show first 20 customers (limited results)
-- ====================================================================
-- Use this when you have a large customer table

SELECT TOP 20
    CUSTOMER_KEY,
    CUSTOMER_NAME,
    CUSTOMER_TYPE,
    COUNTRY,
    INDUSTRY
FROM FIS_CUSTOMER_DIMENSION
ORDER BY CUSTOMER_NAME;

-- ====================================================================
-- QUERY 4: Customer summary statistics
-- ====================================================================
-- Get overview of customer data

SELECT 
    COUNT(*) AS [Total Customers],
    COUNT(DISTINCT COUNTRY) AS [Unique Countries],
    COUNT(DISTINCT INDUSTRY) AS [Unique Industries],
    COUNT(DISTINCT CUSTOMER_TYPE) AS [Unique Customer Types],
    COUNT(DISTINCT RISK_RATING) AS [Unique Risk Ratings]
FROM FIS_CUSTOMER_DIMENSION;

-- ====================================================================
-- QUERY 5: Customer count by country
-- ====================================================================
-- Geographic distribution of customers

SELECT 
    COUNTRY,
    COUNT(*) AS [Customer Count]
FROM FIS_CUSTOMER_DIMENSION
GROUP BY COUNTRY
ORDER BY [Customer Count] DESC;

-- ====================================================================
-- QUERY 6: Customer count by industry
-- ====================================================================
-- Industry distribution of customers

SELECT 
    INDUSTRY,
    COUNT(*) AS [Customer Count]
FROM FIS_CUSTOMER_DIMENSION
GROUP BY INDUSTRY
ORDER BY [Customer Count] DESC;

-- ====================================================================
-- QUERY 7: Customer count by risk rating
-- ====================================================================
-- Risk profile distribution

SELECT 
    RISK_RATING,
    COUNT(*) AS [Customer Count]
FROM FIS_CUSTOMER_DIMENSION
GROUP BY RISK_RATING
ORDER BY [Customer Count] DESC;

-- ====================================================================
-- QUERY 8: Search customers by name
-- ====================================================================
-- Find customers containing specific text (replace 'ACME' with search term)

SELECT 
    CUSTOMER_KEY,
    CUSTOMER_NAME,
    CUSTOMER_TYPE,
    COUNTRY,
    INDUSTRY
FROM FIS_CUSTOMER_DIMENSION
WHERE CUSTOMER_NAME LIKE '%ACME%'
ORDER BY CUSTOMER_NAME;

-- ====================================================================
-- QUERY 9: Customers in specific country
-- ====================================================================
-- Filter customers by country (replace 'United States' with desired country)

SELECT 
    CUSTOMER_KEY,
    CUSTOMER_NAME,
    CUSTOMER_TYPE,
    INDUSTRY,
    RISK_RATING
FROM FIS_CUSTOMER_DIMENSION
WHERE COUNTRY = 'United States'
ORDER BY CUSTOMER_NAME;

-- ====================================================================
-- QUERY 10: High-risk customers
-- ====================================================================
-- Show customers with high risk ratings

SELECT 
    CUSTOMER_KEY,
    CUSTOMER_NAME,
    CUSTOMER_TYPE,
    COUNTRY,
    INDUSTRY,
    RISK_RATING
FROM FIS_CUSTOMER_DIMENSION
WHERE RISK_RATING IN ('High', 'Very High', 'Critical')
ORDER BY RISK_RATING DESC, CUSTOMER_NAME;

-- ====================================================================
-- QUERY 11: Customer table structure/schema
-- ====================================================================
-- See all columns and their data types

SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'FIS_CUSTOMER_DIMENSION'
ORDER BY ORDINAL_POSITION;

-- ====================================================================
-- QUERY 12: Sample data from each column
-- ====================================================================
-- See sample values for each column

SELECT TOP 1
    CUSTOMER_KEY,
    CUSTOMER_NAME,
    CUSTOMER_TYPE,
    COUNTRY,
    INDUSTRY,
    RISK_RATING,
    BUSINESS_UNIT
FROM FIS_CUSTOMER_DIMENSION;

-- ====================================================================
-- QUERY 13: Customers with missing/null data
-- ====================================================================
-- Find customers with incomplete information

SELECT 
    CUSTOMER_KEY,
    CUSTOMER_NAME,
    CASE WHEN CUSTOMER_TYPE IS NULL THEN 'Missing Type' ELSE CUSTOMER_TYPE END AS CUSTOMER_TYPE,
    CASE WHEN COUNTRY IS NULL THEN 'Missing Country' ELSE COUNTRY END AS COUNTRY,
    CASE WHEN INDUSTRY IS NULL THEN 'Missing Industry' ELSE INDUSTRY END AS INDUSTRY,
    CASE WHEN RISK_RATING IS NULL THEN 'Missing Risk Rating' ELSE RISK_RATING END AS RISK_RATING
FROM FIS_CUSTOMER_DIMENSION
WHERE CUSTOMER_TYPE IS NULL 
   OR COUNTRY IS NULL 
   OR INDUSTRY IS NULL 
   OR RISK_RATING IS NULL
ORDER BY CUSTOMER_NAME;

-- ====================================================================
-- QUERY 14: Customer distribution by type and country
-- ====================================================================
-- Cross-tabulation of customer type and country

SELECT 
    CUSTOMER_TYPE,
    COUNTRY,
    COUNT(*) AS [Customer Count]
FROM FIS_CUSTOMER_DIMENSION
GROUP BY CUSTOMER_TYPE, COUNTRY
ORDER BY CUSTOMER_TYPE, [Customer Count] DESC;

-- ====================================================================
-- QUERY 15: Most recent customers (if you have date columns)
-- ====================================================================
-- Uncomment and modify if you have created_date or similar columns

/*
SELECT TOP 10
    CUSTOMER_KEY,
    CUSTOMER_NAME,
    CUSTOMER_TYPE,
    COUNTRY,
    CREATED_DATE
FROM FIS_CUSTOMER_DIMENSION
WHERE CREATED_DATE IS NOT NULL
ORDER BY CREATED_DATE DESC;
*/

/*
USAGE INSTRUCTIONS:
==================

1. COPY any query above
2. PASTE into SQL Server Management Studio, Azure Data Studio, or your SQL execution environment
3. EXECUTE to see the results
4. MODIFY search terms, countries, or other filters as needed

CONNECTION DETAILS:
==================
Server: aqsqlserver001.database.windows.net
Database: adventureworksdb
Authentication: Azure Active Directory

QUERY RECOMMENDATIONS:
=====================

🔍 START WITH: Query 1 (customer keys and names) to verify basic connectivity
📊 OVERVIEW: Query 4 (summary statistics) to understand data volume
🌍 GEOGRAPHY: Query 5 (by country) to see geographic distribution  
🏭 INDUSTRY: Query 6 (by industry) to see sector breakdown
⚠️  RISK: Query 7 (by risk rating) to see risk profile
🔎 SEARCH: Query 8 or 9 to find specific customers
📋 SCHEMA: Query 11 to see table structure
🔍 DATA QUALITY: Query 13 to check for missing data

EXPECTED RESULTS:
================

If your customer dimension is properly loaded:
✅ Query 1 will show customer keys and names
✅ Query 4 will show meaningful counts (not zero)
✅ Query 5-7 will show distribution breakdowns
✅ Query 8-10 will return filtered results based on criteria

If there are issues:
❌ "Invalid object name 'FIS_CUSTOMER_DIMENSION'" = Table doesn't exist
❌ Empty results = No data loaded
❌ Column errors = Column names don't match your table structure
❌ Permission errors = Check database access rights

PERFORMANCE NOTES:
=================
- Use TOP clause for large tables to limit results
- Add WHERE clauses to filter data effectively
- Consider adding indexes on frequently queried columns
- Use appropriate data types for better performance
*/
