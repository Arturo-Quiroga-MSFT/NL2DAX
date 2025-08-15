"""
report_generator.py - Pipeline Execution Report Generator
========================================================

This module generates comprehensive markdown reports for NL2DAX pipeline executions,
capturing all aspects of the natural language to SQL/DAX transformation process.

Features:
- User query analysis and intent extraction details
- Cache hit/miss statistics and performance metrics
- Generated SQL and DAX queries with formatting
- Execution results and error handling
- Performance timing and execution statistics
- Export to timestamped markdown files

Author: NL2DAX Pipeline Development Team
Last Updated: August 15, 2025
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class PipelineReportGenerator:
    """
    Generates comprehensive markdown reports for NL2DAX pipeline executions.
    
    Captures all pipeline execution details including user queries, intent analysis,
    cache performance, query generation, execution results, and timing metrics.
    """
    
    def __init__(self, reports_dir: str = "./REPORTS"):
        """
        Initialize the report generator.
        
        Args:
            reports_dir: Directory to save report files
        """
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        
    def generate_report(self, 
                       user_query: str,
                       execution_results: Dict[str, Any],
                       cache_stats: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a comprehensive markdown report for a pipeline execution.
        
        Args:
            user_query: The original natural language query
            execution_results: Results from execute_pipeline function
            cache_stats: Cache performance statistics
            
        Returns:
            Path to the generated markdown file
        """
        
        timestamp = datetime.now()
        report_filename = self._generate_filename(user_query, timestamp)
        report_path = self.reports_dir / report_filename
        
        # Generate the markdown content
        markdown_content = self._build_markdown_report(
            user_query, execution_results, cache_stats, timestamp
        )
        
        # Write the report to file
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        return str(report_path)
    
    def _generate_filename(self, user_query: str, timestamp: datetime) -> str:
        """Generate a safe filename for the report."""
        # Sanitize query for filename
        safe_query = "".join(c for c in user_query if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_query = safe_query.replace(' ', '_')[:50]  # Limit length
        
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        return f"nl2dax_report_{safe_query}_{timestamp_str}.md"
    
    def _build_markdown_report(self, 
                              user_query: str,
                              results: Dict[str, Any],
                              cache_stats: Optional[Dict[str, Any]],
                              timestamp: datetime) -> str:
        """Build the complete markdown report content."""
        
        report_lines = []
        
        # Header
        report_lines.extend(self._build_header(user_query, timestamp))
        
        # Executive Summary
        report_lines.extend(self._build_executive_summary(results))
        
        # User Query Analysis
        report_lines.extend(self._build_query_analysis(user_query, results))
        
        # Intent and Entity Extraction
        report_lines.extend(self._build_intent_analysis(results))
        
        # Cache Performance
        if cache_stats:
            report_lines.extend(self._build_cache_analysis(cache_stats))
        
        # SQL Generation and Execution
        report_lines.extend(self._build_sql_section(results))
        
        # DAX Generation and Execution
        report_lines.extend(self._build_dax_section(results))
        
        # Performance Metrics
        report_lines.extend(self._build_performance_section(results))
        
        # Error Analysis
        if results.get('errors'):
            report_lines.extend(self._build_error_analysis(results))
        
        # Recommendations
        report_lines.extend(self._build_recommendations(results))
        
        # Footer
        report_lines.extend(self._build_footer())
        
        return '\n'.join(report_lines)
    
    def _build_header(self, user_query: str, timestamp: datetime) -> List[str]:
        """Build the report header section."""
        return [
            "# 📊 NL2DAX Pipeline Execution Report",
            "",
            f"**Generated:** {timestamp.strftime('%B %d, %Y at %I:%M:%S %p')}",
            f"**Query:** {user_query}",
            "",
            "---",
            ""
        ]
    
    def _build_executive_summary(self, results: Dict[str, Any]) -> List[str]:
        """Build the executive summary section."""
        sql_success = "✅ Success" if results.get('sql_results') else "❌ Failed" if results.get('sql_query') else "⏭️ Skipped"
        dax_success = "✅ Success" if results.get('dax_results') else "❌ Failed" if results.get('dax_query') else "⏭️ Skipped"
        
        sql_rows = len(results.get('sql_results', [])) if results.get('sql_results') else 0
        dax_rows = len(results.get('dax_results', [])) if results.get('dax_results') else 0
        
        total_time = results.get('sql_time', 0) + results.get('dax_time', 0)
        
        return [
            "## 📋 Executive Summary",
            "",
            f"| Metric | Value |",
            f"|--------|--------|",
            f"| **SQL Execution** | {sql_success} |",
            f"| **DAX Execution** | {dax_success} |",
            f"| **SQL Rows Returned** | {sql_rows:,} |",
            f"| **DAX Rows Returned** | {dax_rows:,} |",
            f"| **Total Execution Time** | {total_time:.2f}s |",
            f"| **Errors Encountered** | {len(results.get('errors', []))} |",
            "",
        ]
    
    def _build_query_analysis(self, user_query: str, results: Dict[str, Any]) -> List[str]:
        """Build the user query analysis section."""
        query_length = len(user_query)
        word_count = len(user_query.split())
        
        # Analyze query complexity
        complexity_indicators = {
            'aggregation_words': ['count', 'sum', 'average', 'total', 'maximum', 'minimum'],
            'filtering_words': ['where', 'filter', 'only', 'exclude', 'include'],
            'grouping_words': ['group', 'by', 'category', 'type', 'grouped'],
            'sorting_words': ['top', 'bottom', 'highest', 'lowest', 'order', 'sort']
        }
        
        detected_features = []
        for feature_type, keywords in complexity_indicators.items():
            if any(keyword in user_query.lower() for keyword in keywords):
                detected_features.append(feature_type.replace('_', ' ').title())
        
        return [
            "## 🔍 Query Analysis",
            "",
            f"**Original Query:** `{user_query}`",
            "",
            f"| Attribute | Value |",
            f"|-----------|--------|",
            f"| **Character Count** | {query_length} |",
            f"| **Word Count** | {word_count} |",
            f"| **Detected Features** | {', '.join(detected_features) if detected_features else 'Basic query'} |",
            "",
        ]
    
    def _build_intent_analysis(self, results: Dict[str, Any]) -> List[str]:
        """Build the intent and entity extraction section."""
        intent_entities = results.get('intent_entities', 'Not available')
        
        lines = [
            "## 🧠 Intent & Entity Extraction",
            "",
            "### Extracted Intent and Entities",
            "",
            "```json"
        ]
        
        if isinstance(intent_entities, (dict, list)):
            lines.append(json.dumps(intent_entities, indent=2))
        else:
            lines.append(str(intent_entities))
        
        lines.extend([
            "```",
            ""
        ])
        
        return lines
    
    def _build_cache_analysis(self, cache_stats: Dict[str, Any]) -> List[str]:
        """Build the cache performance analysis section."""
        return [
            "## 🚀 Cache Performance",
            "",
            f"| Cache Type | Hits | Misses | Hit Rate |",
            f"|------------|------|--------|----------|",
            f"| **Intent Parsing** | {cache_stats.get('intent_hits', 0)} | {cache_stats.get('intent_misses', 0)} | {self._calculate_hit_rate(cache_stats.get('intent_hits', 0), cache_stats.get('intent_misses', 0))}% |",
            f"| **SQL Generation** | {cache_stats.get('sql_hits', 0)} | {cache_stats.get('sql_misses', 0)} | {self._calculate_hit_rate(cache_stats.get('sql_hits', 0), cache_stats.get('sql_misses', 0))}% |",
            f"| **DAX Generation** | {cache_stats.get('dax_hits', 0)} | {cache_stats.get('dax_misses', 0)} | {self._calculate_hit_rate(cache_stats.get('dax_hits', 0), cache_stats.get('dax_misses', 0))}% |",
            "",
        ]
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> str:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return "N/A"
        return f"{(hits / total * 100):.1f}"
    
    def _build_sql_section(self, results: Dict[str, Any]) -> List[str]:
        """Build the SQL generation and execution section."""
        lines = [
            "## 🗄️ SQL Generation & Execution",
            ""
        ]
        
        if results.get('sql_query'):
            lines.extend([
                "### Generated SQL Query",
                "",
                "```sql",
                results['sql_query'],
                "```",
                ""
            ])
            
            # SQL Execution Results
            if results.get('sql_results'):
                sql_results = results['sql_results']
                lines.extend([
                    "### SQL Execution Results",
                    "",
                    f"**Rows Returned:** {len(sql_results)}",
                    f"**Execution Time:** {results.get('sql_time', 0):.2f} seconds",
                    ""
                ])
                
                # Show first few rows as sample
                if sql_results and len(sql_results) > 0:
                    lines.extend(self._format_results_table(sql_results[:5], "SQL Results (First 5 Rows)"))
            else:
                lines.extend([
                    "### SQL Execution Results",
                    "",
                    "❌ **Execution Failed** - See error analysis section for details",
                    ""
                ])
        else:
            lines.extend([
                "⏭️ **SQL Generation Skipped**",
                ""
            ])
        
        return lines
    
    def _build_dax_section(self, results: Dict[str, Any]) -> List[str]:
        """Build the DAX generation and execution section."""
        lines = [
            "## ⚡ DAX Generation & Execution",
            ""
        ]
        
        if results.get('dax_query'):
            lines.extend([
                "### Generated DAX Query",
                "",
                "```dax",
                results['dax_query'],
                "```",
                ""
            ])
            
            # DAX Execution Results
            if results.get('dax_results'):
                dax_results = results['dax_results']
                lines.extend([
                    "### DAX Execution Results",
                    "",
                    f"**Rows Returned:** {len(dax_results)}",
                    f"**Execution Time:** {results.get('dax_time', 0):.2f} seconds",
                    ""
                ])
                
                # Show first few rows as sample
                if dax_results and len(dax_results) > 0:
                    lines.extend(self._format_results_table(dax_results[:5], "DAX Results (First 5 Rows)"))
            else:
                lines.extend([
                    "### DAX Execution Results",
                    "",
                    "❌ **Execution Failed** - See error analysis section for details",
                    ""
                ])
        else:
            lines.extend([
                "⏭️ **DAX Generation Skipped**",
                ""
            ])
        
        return lines
    
    def _format_results_table(self, results: List[Dict], title: str) -> List[str]:
        """Format query results as a markdown table."""
        if not results:
            return [f"**{title}**", "", "No data returned", ""]
        
        lines = [f"**{title}**", ""]
        
        # Get column headers
        headers = list(results[0].keys())
        
        # Create header row
        header_row = "| " + " | ".join(headers) + " |"
        separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
        
        lines.extend([header_row, separator_row])
        
        # Add data rows
        for row in results:
            data_row = "| " + " | ".join(str(row.get(col, "")) for col in headers) + " |"
            lines.append(data_row)
        
        lines.append("")
        return lines
    
    def _build_performance_section(self, results: Dict[str, Any]) -> List[str]:
        """Build the performance metrics section."""
        sql_time = results.get('sql_time', 0)
        dax_time = results.get('dax_time', 0)
        total_time = sql_time + dax_time
        
        return [
            "## ⏱️ Performance Metrics",
            "",
            f"| Operation | Time (seconds) | Percentage |",
            f"|-----------|----------------|------------|",
            f"| **SQL Generation & Execution** | {sql_time:.2f}s | {(sql_time/total_time*100) if total_time > 0 else 0:.1f}% |",
            f"| **DAX Generation & Execution** | {dax_time:.2f}s | {(dax_time/total_time*100) if total_time > 0 else 0:.1f}% |",
            f"| **Total Pipeline Time** | {total_time:.2f}s | 100% |",
            "",
        ]
    
    def _build_error_analysis(self, results: Dict[str, Any]) -> List[str]:
        """Build the error analysis section."""
        errors = results.get('errors', [])
        
        lines = [
            "## ⚠️ Error Analysis",
            "",
            f"**Total Errors:** {len(errors)}",
            ""
        ]
        
        for i, error in enumerate(errors, 1):
            lines.extend([
                f"### Error {i}",
                "",
                f"```",
                str(error),
                f"```",
                ""
            ])
        
        return lines
    
    def _build_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Build the recommendations section."""
        recommendations = []
        
        # Performance recommendations
        total_time = results.get('sql_time', 0) + results.get('dax_time', 0)
        if total_time > 10:
            recommendations.append("Consider optimizing queries for better performance (>10s execution time)")
        
        # Error-based recommendations
        errors = results.get('errors', [])
        if errors:
            if any('timeout' in str(error).lower() for error in errors):
                recommendations.append("Query timeout detected - consider simplifying complex queries")
            if any('permission' in str(error).lower() for error in errors):
                recommendations.append("Permission issues detected - verify database access credentials")
        
        # Result-based recommendations
        sql_results = results.get('sql_results', [])
        dax_results = results.get('dax_results', [])
        
        if sql_results and not dax_results:
            recommendations.append("SQL execution successful but DAX failed - check Power BI connection")
        elif dax_results and not sql_results:
            recommendations.append("DAX execution successful but SQL failed - check database connection")
        
        if not sql_results and not dax_results:
            recommendations.append("No results returned from either query - verify query logic and data availability")
        
        # Default recommendation if none detected
        if not recommendations:
            recommendations.append("Pipeline executed successfully with no specific recommendations")
        
        lines = [
            "## 💡 Recommendations",
            ""
        ]
        
        for rec in recommendations:
            lines.append(f"- {rec}")
        
        lines.append("")
        return lines
    
    def _build_footer(self) -> List[str]:
        """Build the report footer."""
        return [
            "---",
            "",
            "*Report generated by NL2DAX Pipeline v1.0*",
            "",
            f"*Generated on {datetime.now().strftime('%B %d, %Y at %I:%M:%S %p')}*"
        ]


def create_pipeline_report(user_query: str, 
                          execution_results: Dict[str, Any],
                          cache_stats: Optional[Dict[str, Any]] = None,
                          reports_dir: str = "./REPORTS") -> str:
    """
    Convenience function to create a pipeline execution report.
    
    Args:
        user_query: The original natural language query
        execution_results: Results from execute_pipeline function
        cache_stats: Optional cache performance statistics
        reports_dir: Directory to save the report
        
    Returns:
        Path to the generated report file
    """
    generator = PipelineReportGenerator(reports_dir)
    return generator.generate_report(user_query, execution_results, cache_stats)
