# Quick Test Questions for NL2DAX Pipeline
*Simplified versions for rapid testing and validation*

## 🚀 Quick Test Set (30 Questions)

### Geographic Analysis (Quick Tests)
1. "Show me all customers by country"
2. "List customers from Canada and Mexico"
3. "Which countries have the most customers?"
4. "Show me customers with high risk ratings by country"
5. "What is the total number of customers per region?"

### Currency & Loan Analysis
6. "Show me all loans by currency"
7. "What currencies do we have loans in?"
8. "List loans greater than 10 million in any currency"
9. "Show me Brazilian Real loans"
10. "Which currency has the highest total loan amount?"

### Product & Facility Analysis
11. "Show me all credit facilities"
12. "List facilities by customer"
13. "What are the different loan product types?"
14. "Show me agricultural loans"
15. "Which customers have both loans and credit facilities?"

### Risk & Portfolio Questions
16. "Show me high risk customers"
17. "List customers by risk rating"
18. "What is the average loan amount by country?"
19. "Show me customers with multiple products"
20. "Which portfolios have international exposure?"

### Maturity & Time Analysis
21. "Show me loans maturing next year"
22. "List facilities by maturity date"
23. "What loans were originated in 2024?"
24. "Show me facilities nearing maturity"
25. "Which loans have the longest terms?"

### Complex Multi-Table Questions
26. "Show me customer details with their loan amounts"
27. "List all products for Canadian customers"
28. "Show me facilities and loans for the same customer"
29. "Which international customers have the largest exposure?"
30. "Give me a complete view of our Mexican portfolio"

---

## ⚡ One-Line Test Commands

### For Terminal/Script Testing:
```bash
# Customer Analysis
"Show me all customers by country"
"List high risk customers from Latin America"
"Which customers are from emerging markets?"

# Currency Analysis  
"What is our exposure by currency?"
"Show me all non-USD loans"
"List loans in Canadian dollars"

# Product Analysis
"Show me all agricultural loans"
"List trade finance facilities"
"What are our project finance loans?"

# Risk Analysis
"Show me customers with risk rating above 7"
"List high-value international loans"
"Which countries have the most exposure?"

# Temporal Analysis
"Show me loans originating this year"
"List facilities expiring next year"
"What loans mature in 2027?"
```

## 🎯 Expected Results Summary

### These questions should generate:
- **Multi-table DAX queries** with proper relationships
- **Currency-aware calculations** (CAD, MXN, BRL, ARS, COP, EUR, USD)
- **Geographic filtering** (CA, MX, BR, AR, CO, DE, US)
- **Risk-based analysis** using customer risk ratings
- **Product classification** across loan types and portfolios
- **Time-based filtering** for maturity and origination analysis

### Visual Components for Streamlit:
- **Country distribution maps**
- **Currency exposure pie charts**
- **Risk rating histograms**
- **Maturity timeline charts**
- **Product mix analysis**
- **Customer portfolio dashboards**

## 📋 Testing Checklist

### ✅ DAX Generation Tests:
- [ ] Simple customer queries
- [ ] Multi-currency calculations
- [ ] Geographic filtering
- [ ] Risk-based analysis
- [ ] Product type analysis
- [ ] Date range filtering
- [ ] Multi-table joins
- [ ] Aggregation functions

### ✅ SQL Generation Tests:
- [ ] Customer dimension queries
- [ ] Loan product queries
- [ ] Credit facility queries
- [ ] Cross-table relationships
- [ ] Currency calculations
- [ ] Geographic grouping
- [ ] Risk analytics
- [ ] Temporal analysis

### ✅ Visualization Tests:
- [ ] Chart-ready data formats
- [ ] Geographic data for maps
- [ ] Time series data
- [ ] Categorical distributions
- [ ] Risk metrics displays
- [ ] Multi-dimensional analysis

---

*Use these quick tests for rapid validation of NL2DAX pipeline improvements and international data integration.*