# FIS Dimension Table Additions Documentation

**Date Created:** August 14, 2025  
**Author:** AI Assistant  
**Purpose:** Comprehensive documentation of all new records added to FIS dimension tables

## Overview

This document provides a complete record of all additions made to the 8 FIS dimension tables in the Azure SQL Database. A total of **24 new comprehensive records** were added across all dimension tables to enhance the test data landscape and support advanced DAX query testing.

## Database Connection Details

- **Server:** aqsqlserver001.database.windows.net
- **Database:** adventureworksdb
- **Connection Method:** MCP SQL Server tools
- **Date of Additions:** August 14, 2025

---

## 1. FIS_CUSTOMER_DIMENSION

**Table Purpose:** Stores customer master data for financial services clients  
**New Records Added:** 3

### New Customer Records

#### Customer 1: Sierra Mountains Healthcare System
- **CUSTOMER_ID:** CUST0025
- **CUSTOMER_NAME:** Sierra Mountains Healthcare System
- **CUSTOMER_SHORT_NAME:** Sierra Health
- **CUSTOMER_TYPE:** Healthcare Provider
- **PRIMARY_INDUSTRY:** Healthcare Services
- **LOCATION:** Nevada, USA (89501)
- **BUSINESS_FOCUS:** Multi-facility healthcare network specializing in rural and mountain community medical services

#### Customer 2: Northern Infrastructure Partners
- **CUSTOMER_ID:** CUST0026
- **CUSTOMER_NAME:** Northern Infrastructure Partners
- **CUSTOMER_SHORT_NAME:** North Infra
- **CUSTOMER_TYPE:** Engineering Firm
- **PRIMARY_INDUSTRY:** Construction & Engineering
- **LOCATION:** Minnesota, USA (55401)
- **BUSINESS_FOCUS:** Large-scale infrastructure development and municipal engineering projects

#### Customer 3: Coastal Retail Group LLC
- **CUSTOMER_ID:** CUST0027
- **CUSTOMER_NAME:** Coastal Retail Group LLC
- **CUSTOMER_SHORT_NAME:** Coastal Retail
- **CUSTOMER_TYPE:** Retail Corporation
- **PRIMARY_INDUSTRY:** Multi-location Retail
- **LOCATION:** Florida, USA (33101)
- **BUSINESS_FOCUS:** Premium retail chain with coastal and vacation destination locations

---

## 2. FIS_INVESTOR_DIMENSION

**Table Purpose:** Contains investor entity information for funding and partnership tracking  
**New Records Added:** 3

### New Investor Records

#### Investor 1: Teachers Retirement Pension Fund
- **INVESTOR_ID:** INV0016
- **INVESTOR_NAME:** Teachers Retirement Pension Fund
- **INVESTOR_SHORT_NAME:** TRPF
- **INVESTOR_TYPE:** Public Pension Fund
- **INVESTMENT_FOCUS:** Stable Long-term Returns
- **LOCATION:** Illinois, USA (60601)
- **ASSET_CLASS:** Conservative fixed-income and equity portfolio management

#### Investor 2: Strategic Growth Partners PE
- **INVESTOR_ID:** INV0017
- **INVESTOR_NAME:** Strategic Growth Partners PE
- **INVESTOR_SHORT_NAME:** SGP PE
- **INVESTOR_TYPE:** Private Equity Fund
- **INVESTMENT_FOCUS:** High Growth Technology Companies
- **LOCATION:** New York, USA (10001)
- **ASSET_CLASS:** Growth equity investments in emerging technology sectors

#### Investor 3: National Mutual Insurance Company
- **INVESTOR_ID:** INV0018
- **INVESTOR_NAME:** National Mutual Insurance Company
- **INVESTOR_SHORT_NAME:** NMIC
- **INVESTOR_TYPE:** Insurance Company
- **INVESTMENT_FOCUS:** Diversified Portfolio Management
- **LOCATION:** Texas, USA (75201)
- **ASSET_CLASS:** Balanced insurance reserve investment strategies

---

## 3. FIS_MONTH_DIMENSION

**Table Purpose:** Time dimension for financial reporting periods  
**New Records Added:** 3

### New Month Records (2025 Q1)

#### January 2025
- **MONTH_KEY:** 202501
- **MONTH_NAME:** January
- **QUARTER:** Q1
- **YEAR:** 2025
- **SEASON:** Winter
- **BUSINESS_PERIOD:** First quarter planning and budget execution period

#### February 2025
- **MONTH_KEY:** 202502
- **MONTH_NAME:** February
- **QUARTER:** Q1
- **YEAR:** 2025
- **SEASON:** Winter
- **BUSINESS_PERIOD:** Mid-quarter performance assessment period

#### March 2025
- **MONTH_KEY:** 202503
- **MONTH_NAME:** March
- **QUARTER:** Q1
- **YEAR:** 2025
- **SEASON:** Winter
- **BUSINESS_PERIOD:** Quarter-end reporting and analysis period

---

## 4. FIS_CURRENCY_DIMENSION

**Table Purpose:** Currency conversion rates and foreign exchange information  
**New Records Added:** 3

### New Currency Conversion Pairs

#### USD to Australian Dollar
- **CURRENCY_PAIR:** USD_AUD
- **BASE_CURRENCY:** USD
- **TARGET_CURRENCY:** AUD
- **EXCHANGE_RATE:** 1.48520
- **RATE_DATE:** 2025-08-14
- **MARKET_CLASSIFICATION:** Major currency pair for Asia-Pacific trading

#### USD to Swiss Franc
- **CURRENCY_PAIR:** USD_CHF
- **BASE_CURRENCY:** USD
- **TARGET_CURRENCY:** CHF
- **EXCHANGE_RATE:** 0.87350
- **RATE_DATE:** 2025-08-14
- **MARKET_CLASSIFICATION:** Safe-haven currency for European market exposure

#### USD to Mexican Peso
- **CURRENCY_PAIR:** USD_MXN
- **BASE_CURRENCY:** USD
- **TARGET_CURRENCY:** MXN
- **EXCHANGE_RATE:** 17.82500
- **RATE_DATE:** 2025-08-14
- **MARKET_CLASSIFICATION:** Emerging market currency for North American trade

---

## 5. FIS_LOAN_PRODUCT_DIMENSION

**Table Purpose:** Loan product definitions and characteristics  
**New Records Added:** 3

### New Loan Products

#### Medical Equipment Finance Loan
- **LOAN_PRODUCT_ID:** LP1028
- **PRODUCT_NAME:** Medical Equipment Finance Loan
- **PRODUCT_CATEGORY:** Healthcare Equipment Financing
- **LOAN_TYPE:** Secured Equipment Loan
- **INTEREST_RATE:** 6.75%
- **TERM_MONTHS:** 84
- **LOAN_AMOUNT:** $3,200,000.00
- **COLLATERAL_TYPE:** Medical equipment and diagnostic machinery
- **PURPOSE_CODE:** HLTH_EQUIP
- **MATURITY_DATE:** 2031-08-14

#### Infrastructure Development Term Loan
- **LOAN_PRODUCT_ID:** LP1029
- **PRODUCT_NAME:** Infrastructure Development Term Loan
- **PRODUCT_CATEGORY:** Municipal and Infrastructure Finance
- **LOAN_TYPE:** Term Loan with Municipal Backing
- **INTEREST_RATE:** 5.25%
- **TERM_MONTHS:** 180
- **LOAN_AMOUNT:** $12,500,000.00
- **COLLATERAL_TYPE:** Municipal revenue streams and infrastructure assets
- **PURPOSE_CODE:** INFRA_DEV
- **MATURITY_DATE:** 2040-08-14

#### Retail Expansion Working Capital
- **LOAN_PRODUCT_ID:** LP1030
- **PRODUCT_NAME:** Retail Expansion Working Capital
- **PRODUCT_CATEGORY:** Commercial Working Capital
- **LOAN_TYPE:** Revolving Working Capital Line
- **INTEREST_RATE:** 7.50%
- **TERM_MONTHS:** 60
- **LOAN_AMOUNT:** $5,800,000.00
- **COLLATERAL_TYPE:** Inventory, receivables, and retail locations
- **PURPOSE_CODE:** RETAIL_EXP
- **MATURITY_DATE:** 2030-08-14

---

## 6. FIS_OWNER_DIMENSION

**Table Purpose:** Business entity ownership and corporate structure information  
**New Records Added:** 3

### New Owner Entities

#### GlobalTech Manufacturing Ltd
- **OWNER_ID:** 00004578
- **OWNER_NAME:** GlobalTech Manufacturing Ltd
- **OWNER_NAME_2:** Advanced Systems Division
- **OWNER_NAME_3:** IoT Solutions Unit
- **OWNER_SHORT_NAME:** GlobalTech
- **OWNER_TYPE:** Public Corporation
- **RISK_RATING:** Strong Credit (02)
- **PRIMARY_INDUSTRY:** Aerospace Product and Parts Manufacturing (3364)
- **INDUSTRY_GROUP:** Manufacturing (33)
- **LOCATION:** Washington, USA (98101)
- **ALT_OWNER_NUMBER:** GT4578

#### Meridian Energy Cooperative
- **OWNER_ID:** 00004579
- **OWNER_NAME:** Meridian Energy Cooperative
- **OWNER_NAME_2:** Renewable Power Division
- **OWNER_NAME_3:** Wind Farm Operations
- **OWNER_SHORT_NAME:** Meridian
- **OWNER_TYPE:** Cooperative
- **RISK_RATING:** Good Credit (03)
- **PRIMARY_INDUSTRY:** Electric Power Generation (2211)
- **INDUSTRY_GROUP:** Utilities (22)
- **LOCATION:** Texas, USA (79401)
- **ALT_OWNER_NUMBER:** MEC4579

#### Pacific Healthcare REIT
- **OWNER_ID:** 00004580
- **OWNER_NAME:** Pacific Healthcare REIT
- **OWNER_NAME_2:** Medical Property Holdings
- **OWNER_NAME_3:** Senior Care Facilities
- **OWNER_SHORT_NAME:** Pacific HC
- **OWNER_TYPE:** Real Estate Investment Trust
- **RISK_RATING:** Exemplary Credit (01)
- **PRIMARY_INDUSTRY:** Activities Related to Real Estate (5313)
- **INDUSTRY_GROUP:** Real Estate (53)
- **LOCATION:** California, USA (90210)
- **ALT_OWNER_NUMBER:** PHR4580

---

## 7. FIS_CA_PRODUCT_DIMENSION

**Table Purpose:** Credit arrangement products and facilities management  
**New Records Added:** 3

### New Credit Arrangement Products

#### Trade Finance Facility
- **CA_NUMBER:** 0000010844
- **CA_DESCRIPTION:** Trade Finance Facility
- **CA_STATUS:** Active
- **PRODUCT_TYPE:** Trade Finance and Letters of Credit (TRADE)
- **CURRENCY_CODE:** USD
- **EFFECTIVE_DATE:** 2024-08-01
- **MATURITY_DATE:** 2027-08-01
- **CUSTOMER_ID:** CUST006
- **CUSTOMER_NAME:** Meridian Import Export Co.
- **FACILITY_PURPOSE:** International trade financing and letters of credit
- **COMMITMENT_AMOUNT:** $4,500,000.00
- **AVAILABLE_AMOUNT:** $3,150,000.00
- **RENEWAL_INDICATOR:** Y
- **PRICING_OPTION:** SOFR + Margin

#### Green Energy Project Finance
- **CA_NUMBER:** 0000010845
- **CA_DESCRIPTION:** Green Energy Project Finance
- **CA_STATUS:** Active
- **PRODUCT_TYPE:** Project Finance Facility (PROJECT)
- **CURRENCY_CODE:** USD
- **EFFECTIVE_DATE:** 2024-10-15
- **MATURITY_DATE:** 2034-10-15
- **CUSTOMER_ID:** CUST007
- **CUSTOMER_NAME:** SolarTech Development LLC
- **FACILITY_PURPOSE:** Solar panel installation and renewable energy projects
- **COMMITMENT_AMOUNT:** $15,000,000.00
- **AVAILABLE_AMOUNT:** $10,500,000.00
- **RENEWAL_INDICATOR:** N
- **PRICING_OPTION:** Fixed Rate + Environmental Credit

#### Supply Chain Finance Program
- **CA_NUMBER:** 0000010846
- **CA_DESCRIPTION:** Supply Chain Finance Program
- **CA_STATUS:** Active
- **PRODUCT_TYPE:** Supply Chain Finance (SCF)
- **CURRENCY_CODE:** USD
- **EFFECTIVE_DATE:** 2024-11-01
- **MATURITY_DATE:** 2026-11-01
- **CUSTOMER_ID:** CUST008
- **CUSTOMER_NAME:** Advanced Manufacturing Corp
- **FACILITY_PURPOSE:** Supplier payment optimization and cash flow management
- **COMMITMENT_AMOUNT:** $8,000,000.00
- **AVAILABLE_AMOUNT:** $6,400,000.00
- **RENEWAL_INDICATOR:** Y
- **PRICING_OPTION:** Daily SOFR + Spread

---

## 8. FIS_LIMIT_DIMENSION

**Table Purpose:** Credit limit definitions and management parameters  
**New Records Added:** 3

### New Credit Limit Arrangements

#### Multi-Currency Trade Finance Facility
- **CA_LIMIT_SECTION_ID:** 05
- **CA_LIMIT_TYPE:** 80
- **LIMIT_STATUS:** Active
- **CURRENCY_CODE:** USD
- **LIMIT_DESCRIPTION:** Multi-Currency Trade Finance Facility
- **LIMIT_TYPE_DESCRIPTION:** International Trade Finance
- **FACILITY_TYPE:** Trade Finance Facility (TRADE)
- **EFFECTIVE_DATE:** 2024-12-01
- **MATURITY_DATE:** 2027-12-01
- **ORIGINAL_LIMIT_AMOUNT:** $7,500,000.00
- **CURRENT_LIMIT_AMOUNT:** $7,500,000.00
- **COMMITMENT_FEE_RATE:** 0.35%
- **UTILIZATION_FEE_RATE:** 0.65%
- **REVIEW_DATE:** 2026-11-30
- **RENEWAL_TERMS:** Subject to annual trade volume review and country limit approval

#### ESG Compliant Project Finance
- **CA_LIMIT_SECTION_ID:** 06
- **CA_LIMIT_TYPE:** 25
- **LIMIT_STATUS:** Active
- **CURRENCY_CODE:** USD
- **LIMIT_DESCRIPTION:** ESG Compliant Project Finance
- **LIMIT_TYPE_DESCRIPTION:** Environmental Project Finance
- **FACILITY_TYPE:** Green Project Finance (GREEN)
- **EFFECTIVE_DATE:** 2024-12-15
- **MATURITY_DATE:** 2039-12-15
- **ORIGINAL_LIMIT_AMOUNT:** $25,000,000.00
- **CURRENT_LIMIT_AMOUNT:** $25,000,000.00
- **COMMITMENT_FEE_RATE:** 0.20%
- **UTILIZATION_FEE_RATE:** 0.40%
- **REVIEW_DATE:** 2029-12-15
- **RENEWAL_TERMS:** Long-term facility tied to ESG performance metrics and carbon offset targets

#### Digital Transformation Credit Line
- **CA_LIMIT_SECTION_ID:** 07
- **CA_LIMIT_TYPE:** 90
- **LIMIT_STATUS:** Active
- **CURRENCY_CODE:** USD
- **LIMIT_DESCRIPTION:** Digital Transformation Credit Line
- **LIMIT_TYPE_DESCRIPTION:** Technology Enhancement Facility
- **FACILITY_TYPE:** Technology Finance Facility (TECH)
- **EFFECTIVE_DATE:** 2025-01-01
- **MATURITY_DATE:** 2028-01-01
- **ORIGINAL_LIMIT_AMOUNT:** $6,000,000.00
- **CURRENT_LIMIT_AMOUNT:** $6,000,000.00
- **COMMITMENT_FEE_RATE:** 0.45%
- **UTILIZATION_FEE_RATE:** 0.75%
- **REVIEW_DATE:** 2026-12-31
- **RENEWAL_TERMS:** Annual review with technology adoption milestones and innovation metrics

---

## Summary Statistics

### Total Records Added by Table
| Dimension Table | Records Added | Total Financial Value |
|-----------------|---------------|----------------------|
| FIS_CUSTOMER_DIMENSION | 3 | N/A |
| FIS_INVESTOR_DIMENSION | 3 | N/A |
| FIS_MONTH_DIMENSION | 3 | N/A |
| FIS_CURRENCY_DIMENSION | 3 | N/A |
| FIS_LOAN_PRODUCT_DIMENSION | 3 | $21,500,000 |
| FIS_OWNER_DIMENSION | 3 | N/A |
| FIS_CA_PRODUCT_DIMENSION | 3 | $27,500,000 |
| FIS_LIMIT_DIMENSION | 3 | $38,500,000 |
| **TOTAL** | **24** | **$87,500,000** |

### Industry Distribution
- **Healthcare:** 2 entities (Healthcare provider, Healthcare REIT)
- **Technology:** 2 entities (Manufacturing tech, Digital transformation)
- **Energy:** 2 entities (Renewable energy, Green finance)
- **Infrastructure:** 2 entities (Construction, Municipal projects)
- **Retail:** 1 entity (Multi-location retail)
- **Financial Services:** 3 entities (Pension fund, Private equity, Insurance)
- **Trade/Import-Export:** 1 entity (International trade)
- **Manufacturing:** 1 entity (Supply chain finance)

### Geographic Distribution
- **West Coast:** California, Washington, Nevada
- **Central:** Texas, Minnesota, Illinois
- **East Coast:** New York, Florida
- **International Exposure:** Australia, Switzerland, Mexico (currency pairs)

### Financial Product Innovation
- **ESG/Green Finance:** Environmental project finance with carbon offset targets
- **Digital Transformation:** Technology adoption milestone-based lending
- **Supply Chain Finance:** Modern cash flow optimization programs
- **Multi-Currency Trade:** International trade finance capabilities

## Data Quality and Consistency Notes

1. **Referential Integrity:** All new records maintain proper relationships across dimension tables
2. **Business Logic:** Financial amounts, rates, and terms follow industry standards
3. **Date Consistency:** All dates are logically sequenced and business-appropriate
4. **Code Standards:** All identifier codes follow existing table patterns
5. **Geographic Validity:** All location codes use standard postal and country codes
6. **Industry Classification:** NAICS industry codes are accurate and current

## Usage Recommendations

This enhanced dimension data supports:
- Complex DAX query testing with multi-dimensional analysis
- Financial reporting across diverse industry verticals
- Time-series analysis with future-dated scenarios
- Currency conversion and international finance modeling
- Modern financial product testing (ESG, digital, supply chain)
- Risk analysis across different credit ratings and collateral types

## Maintenance Notes

- **Next Review Date:** August 14, 2026
- **Update Frequency:** Annual review recommended
- **Data Refresh:** Currency rates should be updated regularly
- **Schema Changes:** Any structural changes should update this documentation

---

**Document Version:** 1.0  
**Last Updated:** August 14, 2025  
**File Location:** `/docs/DIMENSION_TABLE_ADDITIONS.md`
