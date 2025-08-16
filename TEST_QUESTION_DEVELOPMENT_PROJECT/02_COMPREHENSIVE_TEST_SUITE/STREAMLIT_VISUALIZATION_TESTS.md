# Streamlit Visualization Test Questions
*Questions specifically designed for visual analysis in the Streamlit Analysis tab*

## 📊 Chart-Specific Test Questions

### 🗺️ Geographic Visualizations (Maps & Regional Charts)

#### World Map Visualizations
1. **"Show me customer distribution by country"**
   - Chart Type: World map with country markers
   - Data: Customer count per country
   - Colors: Risk-based color coding

2. **"What is our loan exposure by country?"**
   - Chart Type: Choropleth map
   - Data: Total loan amounts by country
   - Colors: Exposure level intensity

3. **"Display credit facility utilization rates by country"**
   - Chart Type: Geographic scatter plot
   - Data: Utilization percentage by country
   - Size: Total facility amounts

#### Regional Comparison Charts
4. **"Compare North America vs South America loan portfolios"**
   - Chart Type: Side-by-side bar charts
   - Data: Loan amounts by region
   - Categories: Product types

5. **"Show emerging markets vs developed markets exposure"**
   - Chart Type: Grouped column chart
   - Data: Portfolio metrics by market type
   - Metrics: Count, amount, average deal size

### 💰 Currency & Financial Charts

#### Multi-Currency Analysis
6. **"Display our portfolio by currency"**
   - Chart Type: Treemap
   - Data: Total amounts by currency
   - Hierarchy: Currency > Product Type > Customer

7. **"Show currency concentration risk"**
   - Chart Type: Pie chart with drill-down
   - Data: Portfolio percentage by currency
   - Threshold: Risk concentration alerts

8. **"Compare loan amounts across all currencies"**
   - Chart Type: Stacked bar chart
   - Data: Loan amounts by currency and country
   - Axis: Countries (X), Amounts (Y), Currency (Stack)

#### Financial Trends
9. **"Show loan origination trends by currency over time"**
   - Chart Type: Multi-line time series
   - Data: Monthly origination amounts
   - Lines: One per currency

10. **"Display facility maturity timeline by currency"**
    - Chart Type: Gantt chart or timeline
    - Data: Facility start/end dates
    - Color: Currency coding

### 📈 Risk & Performance Dashboards

#### Risk Analytics
11. **"Create a risk profile dashboard for international customers"**
    - Chart Type: Multi-panel dashboard
    - Panels: Risk distribution, Geographic risk, Risk trends
    - Filters: Country, Risk rating, Product type

12. **"Show customer risk ratings vs exposure amounts"**
    - Chart Type: Bubble chart
    - Data: Risk rating (X), Total exposure (Y), Customer count (Bubble size)
    - Colors: Geographic regions

13. **"Display concentration risk by customer, country, and currency"**
    - Chart Type: Heat map matrix
    - Data: Exposure percentages
    - Dimensions: Customer vs Country vs Currency

#### Portfolio Performance
14. **"Show portfolio utilization rates across all dimensions"**
    - Chart Type: Multi-dimensional gauge chart
    - Data: Utilization percentages
    - Gauges: By country, currency, product type

15. **"Create a portfolio health dashboard"**
    - Chart Type: KPI dashboard with multiple widgets
    - Metrics: Total exposure, Risk distribution, Geographic spread
    - Indicators: Green/Yellow/Red status

### 🏦 Product & Customer Analysis

#### Product Mix Analysis
16. **"Display loan product distribution by country"**
    - Chart Type: Stacked horizontal bar chart
    - Data: Product types by country
    - Stack: Product categories

17. **"Show agricultural vs manufacturing vs energy loan distribution"**
    - Chart Type: Donut chart with drill-down
    - Data: Loan amounts by sector
    - Drill-down: Countries within sectors

18. **"Compare secured vs unsecured loan ratios by region"**
    - Chart Type: Grouped column chart
    - Data: Loan type percentages by region
    - Groups: Secured/Unsecured

#### Customer Relationship Analysis
19. **"Show customer relationship depth (products per customer)"**
    - Chart Type: Histogram
    - Data: Number of products per customer
    - Bins: 1, 2, 3, 4+ products

20. **"Display top customers by total relationship value"**
    - Chart Type: Horizontal bar chart (Top 10)
    - Data: Total exposure per customer
    - Bars: Customer names with flags

### ⏰ Temporal Analysis Charts

#### Time Series Analysis
21. **"Show quarterly loan origination trends by region"**
    - Chart Type: Multi-area chart
    - Data: Quarterly origination volumes
    - Areas: Geographic regions

22. **"Display facility renewal patterns over time"**
    - Chart Type: Line chart with markers
    - Data: Renewal rates by quarter
    - Lines: Different product types

23. **"Show maturity cliff analysis"**
    - Chart Type: Waterfall chart
    - Data: Maturing amounts by year
    - Categories: By currency and product type

#### Seasonal Patterns
24. **"Display seasonal lending patterns by country"**
    - Chart Type: Polar/Radar chart
    - Data: Monthly origination patterns
    - Spokes: Months, Lines: Countries

25. **"Show business cycle correlation with loan demand"**
    - Chart Type: Dual-axis line chart
    - Data: Loan volumes vs economic indicators
    - Axes: Volume (Left), Economic index (Right)

### 🔄 Interactive Dashboard Questions

#### Multi-Filter Dashboards
26. **"Create an interactive international portfolio explorer"**
    - Components: Multiple linked charts
    - Filters: Country, Currency, Product type, Risk level
    - Charts: Map, treemap, time series, risk matrix

27. **"Build a customer deep-dive dashboard"**
    - Components: Customer selector with profile view
    - Details: All products, facilities, risk metrics, trends
    - Layout: Master-detail with drill-down capability

28. **"Design a currency exposure monitoring dashboard"**
    - Components: Real-time currency exposure tracking
    - Alerts: Concentration thresholds, maturity alerts
    - Charts: Currency treemap, exposure timeline, risk gauges

#### Comparative Analysis
29. **"Create a country comparison tool"**
    - Components: Side-by-side country profiles
    - Metrics: Portfolio size, risk profile, product mix
    - Interaction: Country selector with dynamic comparison

30. **"Build a product performance analyzer"**
    - Components: Product type selector with performance metrics
    - Charts: Performance trends, geographic distribution, risk analysis
    - Filters: Time period, geographic region, customer segment

---

## 🎨 Streamlit Component Specifications

### Chart Library Recommendations:
- **Plotly**: Interactive maps, 3D charts, hover details
- **Altair**: Statistical visualizations, linked brushing
- **Matplotlib/Seaborn**: Statistical analysis, correlation plots
- **Folium**: Advanced geographic mapping
- **Streamlit native**: Metrics, KPIs, simple charts

### Layout Suggestions:
- **Sidebar**: Filters (Country, Currency, Date range, Risk level)
- **Main Panel**: Primary visualization
- **Tabs**: Different analysis perspectives
- **Columns**: Side-by-side comparisons
- **Expanders**: Detailed breakdowns

### Interactivity Features:
- **Click-through**: From summary to detail views
- **Hover details**: Additional context on charts
- **Filter persistence**: Maintain selections across views
- **Export options**: Download charts and data
- **Real-time updates**: Refresh with new data

## 📋 Testing Matrix

| Question Type | Chart Type | Complexity | Interactive | Geographic | Currency | Risk |
|---------------|------------|------------|-------------|------------|----------|------|
| Customer Dist | Map | Low | Yes | Yes | No | Yes |
| Currency Mix | Treemap | Medium | Yes | No | Yes | No |
| Risk Analysis | Dashboard | High | Yes | Yes | Yes | Yes |
| Time Trends | Time Series | Medium | Yes | No | Yes | No |
| Comparative | Side-by-side | Medium | Yes | Yes | Yes | Yes |

---

*These questions are specifically designed to create compelling visual stories using our enhanced international banking dataset in the Streamlit analysis interface.*