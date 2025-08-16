# NL2DAX International Test Questions
*Comprehensive test cases leveraging enhanced international dimension data*

## 📊 Customer Analysis Questions

### Geographic & Risk Distribution
1. **"Show me the distribution of customers by country and their risk ratings"**
   - Tests: Multi-table joins, geographic grouping, risk analytics
   - Visualization: Geographic map/bar chart with risk color coding
   - Business Value: International portfolio risk assessment

2. **"Which countries have the highest concentration of high-risk customers?"**
   - Tests: Country aggregation, risk filtering, ranking
   - Visualization: Heat map or ranked bar chart
   - Business Value: Geographic risk management

3. **"Compare customer risk profiles between North American and South American markets"**
   - Tests: Regional grouping, comparative analysis, risk categorization
   - Visualization: Side-by-side comparison charts
   - Business Value: Regional market strategy

### Customer Segmentation
4. **"List all international customers with their primary business sectors and total exposure"**
   - Tests: Customer dimension joins, sector analysis, exposure calculation
   - Visualization: Bubble chart (sector vs exposure vs customer count)
   - Business Value: Sector diversification analysis

5. **"Show me customers from emerging markets (Mexico, Brazil, Argentina, Colombia) and their credit profiles"**
   - Tests: Multi-country filtering, credit analysis
   - Visualization: Matrix view with credit metrics
   - Business Value: Emerging market exposure assessment

## 💰 Multi-Currency Analysis Questions

### Currency Exposure
6. **"What is our total loan portfolio exposure by currency?"**
   - Tests: Currency aggregation, loan amount summation
   - Visualization: Pie chart or treemap by currency
   - Business Value: Currency risk management

7. **"Show me the largest loans in each currency and their maturity profiles"**
   - Tests: Currency grouping, loan ranking, date analysis
   - Visualization: Timeline chart with currency-coded markers
   - Business Value: Liquidity and currency risk planning

8. **"Compare loan amounts in USD equivalent across all international currencies"**
   - Tests: Currency conversion logic, cross-currency comparison
   - Visualization: Normalized bar chart
   - Business Value: True portfolio size assessment

### Credit Facility Analysis
9. **"What are the utilization rates for credit facilities by country?"**
   - Tests: Available vs commitment amount calculations, geographic grouping
   - Visualization: Utilization gauge charts by country
   - Business Value: Credit facility management

10. **"Show me credit facilities nearing maturity in the next 12 months by currency"**
    - Tests: Date filtering, currency grouping, maturity analysis
    - Visualization: Timeline with currency-coded facility bars
    - Business Value: Renewal planning and cash flow management

## 🏦 Portfolio Diversification Questions

### Loan Product Mix
11. **"Analyze our loan portfolio diversification across product types and currencies"**
    - Tests: Multi-dimensional grouping, product type analysis
    - Visualization: Matrix heatmap (product type vs currency)
    - Business Value: Portfolio diversification assessment

12. **"Which loan purposes are most common in each geographic region?"**
    - Tests: Purpose categorization, geographic analysis
    - Visualization: Stacked bar chart by region
    - Business Value: Regional business pattern insights

13. **"Show me the distribution of secured vs unsecured loans by country"**
    - Tests: Loan type classification, country analysis
    - Visualization: Stacked column chart
    - Business Value: Collateral risk by geography

### Pricing Analysis
14. **"Compare interest rate benchmarks used across different countries"**
    - Tests: Pricing option analysis, country grouping
    - Visualization: Reference rate comparison chart
    - Business Value: Pricing strategy optimization

15. **"What are the average loan amounts by product type in each currency?"**
    - Tests: Product grouping, currency analysis, statistical calculations
    - Visualization: Multi-series bar chart
    - Business Value: Product positioning insights

## 📈 Advanced Analytics Questions

### Cross-Dimensional Analysis
16. **"Show me customers with both loans and credit facilities, broken down by country"**
    - Tests: Multi-table joins, customer relationship analysis
    - Visualization: Venn diagram or relationship network
    - Business Value: Customer relationship depth

17. **"Which international customers have the most diversified product relationships?"**
    - Tests: Product count per customer, diversification metrics
    - Visualization: Bubble chart (customer vs product count vs total exposure)
    - Business Value: Relationship strength assessment

18. **"Analyze the correlation between customer risk rating and loan product types"**
    - Tests: Risk vs product analysis, correlation calculation
    - Visualization: Scatter plot with trend lines
    - Business Value: Risk-based product strategy

### Temporal Analysis
19. **"Show loan origination trends by quarter for each international market"**
    - Tests: Time series analysis, geographic grouping
    - Visualization: Multi-line time series chart
    - Business Value: Market growth patterns

20. **"Compare facility renewal rates between domestic and international customers"**
    - Tests: Renewal indicator analysis, geographic comparison
    - Visualization: Comparison bar chart with percentages
    - Business Value: Customer retention insights

## 🌍 International Banking Insights

### Market Penetration
21. **"What is our market share by loan amount in each Latin American country?"**
    - Tests: Regional filtering, market share calculations
    - Visualization: Market share pie charts by country
    - Business Value: Regional competitive positioning

22. **"Show me the average deal size progression by country over time"**
    - Tests: Time-based averaging, country trends
    - Visualization: Multi-line trend chart
    - Business Value: Market development tracking

### Operational Insights
23. **"Which booking units handle the most international business?"**
    - Tests: Booking unit analysis, international classification
    - Visualization: Horizontal bar chart ranked by volume
    - Business Value: Operational efficiency assessment

24. **"Compare processing times for different product types across countries"**
    - Tests: Processing time calculation, product/country analysis
    - Visualization: Box plot or heat map
    - Business Value: Operational improvement opportunities

## 💼 Risk Management Questions

### Concentration Risk
25. **"Identify concentration risks by customer, country, and currency"**
    - Tests: Concentration calculations, multi-dimensional risk analysis
    - Visualization: Risk dashboard with multiple gauges
    - Business Value: Portfolio risk management

26. **"Show me exposure limits vs actual exposure by country"**
    - Tests: Limit comparison, exposure calculation
    - Visualization: Gauge charts or variance analysis
    - Business Value: Regulatory compliance monitoring

### Credit Quality
27. **"Analyze the relationship between collateral types and loan performance by region"**
    - Tests: Collateral analysis, performance correlation, regional grouping
    - Visualization: Performance matrix by collateral type
    - Business Value: Collateral strategy optimization

28. **"Which portfolios have the highest concentration of emerging market exposure?"**
    - Tests: Portfolio analysis, emerging market classification
    - Visualization: Portfolio composition pie charts
    - Business Value: Strategic portfolio management

## 🔄 Complex Multi-Table Questions

### Comprehensive Analysis
29. **"Create a complete customer profile for our top 5 international customers including all their products and facilities"**
    - Tests: Multi-table joins, customer ranking, comprehensive data integration
    - Visualization: Customer profile dashboards
    - Business Value: Relationship management

30. **"Show me a complete view of our Latin American portfolio including customers, loans, and credit facilities with risk metrics"**
    - Tests: Complex multi-table joins, regional filtering, risk calculations
    - Visualization: Comprehensive regional dashboard
    - Business Value: Regional portfolio management

## 📋 Query Complexity Levels

### **Level 1: Basic** (Questions 1-10)
- Single or simple joins
- Basic aggregations
- Geographic/currency grouping

### **Level 2: Intermediate** (Questions 11-20)
- Multi-table joins
- Conditional logic
- Time-based analysis

### **Level 3: Advanced** (Questions 21-30)
- Complex multi-dimensional analysis
- Statistical calculations
- Comprehensive business intelligence

---

## 🎯 Testing Strategy

Each question is designed to:
1. **Test DAX/SQL Generation**: Complex queries that challenge the NL2DAX pipeline
2. **Provide Business Value**: Real insights that banking professionals would need
3. **Enable Visualization**: Data structures suitable for charts and dashboards
4. **Leverage International Data**: Utilize our enhanced multi-currency, multi-country dataset

## 📊 Expected Visualizations

- **Geographic Maps**: Country-based analysis
- **Currency Treemaps**: Multi-currency portfolio views
- **Timeline Charts**: Maturity and origination analysis
- **Risk Dashboards**: Multi-dimensional risk metrics
- **Comparison Charts**: Regional and product comparisons
- **Correlation Plots**: Risk and performance relationships

These questions will thoroughly test the NL2DAX pipeline's ability to generate sophisticated queries while providing actionable business insights for international banking operations.