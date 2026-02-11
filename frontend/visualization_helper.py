"""
Visualization Helper
Enhances query responses with chart data and insights
"""
from typing import Dict, List, Any, Optional
import re


class VisualizationHelper:
    """Helper class to format query results for visualization"""

    @staticmethod
    def format_for_charts(query_result: Dict[str, Any], question: str = "") -> Dict[str, Any]:
        """
        Format query result to include chart data and visualization hints

        Args:
            query_result: Raw query result from semantic layer
            question: Original user question

        Returns:
            Enhanced result with chart data
        """
        enhanced_result = query_result.copy()

        # Extract tabular data for charting
        if "data" in query_result and isinstance(query_result["data"], list):
            enhanced_result["chart_data"] = query_result["data"]
            enhanced_result["chart_type"] = VisualizationHelper.suggest_chart_type(
                query_result["data"], question
            )
            enhanced_result["chart_title"] = VisualizationHelper.generate_chart_title(question)

        # Add color-coded insights
        if "response" in query_result:
            enhanced_result["insights"] = VisualizationHelper.extract_insights(
                query_result["response"],
                query_result.get("data", [])
            )

        return enhanced_result

    @staticmethod
    def suggest_chart_type(data: List[Dict], question: str = "") -> str:
        """
        Suggest appropriate chart type based on data shape and question

        Args:
            data: Query result data
            question: User question

        Returns:
            Suggested chart type
        """
        if not data or len(data) == 0:
            return "table"

        # Analyze question for chart type hints
        question_lower = question.lower()

        # Trend analysis → line chart
        if any(word in question_lower for word in ["trend", "over time", "by month", "by year", "timeline"]):
            return "line"

        # Comparison → bar chart
        if any(word in question_lower for word in ["compare", "vs", "versus", "by region", "by type"]):
            return "bar"

        # Distribution/breakdown → pie chart
        if any(word in question_lower for word in ["distribution", "breakdown", "share", "percentage"]):
            return "pie"

        # Analyze data shape
        keys = list(data[0].keys())
        numeric_fields = [k for k in keys if isinstance(data[0][k], (int, float))]
        string_fields = [k for k in keys if isinstance(data[0][k], str)]

        # Time series detection
        if any(k.lower() in ['date', 'month', 'year', 'quarter', 'week'] for k in keys):
            return "line"

        # Category comparison
        if len(string_fields) == 1 and len(numeric_fields) >= 1 and len(data) <= 20:
            return "bar"

        # Distribution
        if len(string_fields) == 1 and len(numeric_fields) == 1 and len(data) <= 10:
            return "pie"

        # Default to table for complex data
        return "table"

    @staticmethod
    def generate_chart_title(question: str) -> str:
        """
        Generate chart title from question

        Args:
            question: User question

        Returns:
            Chart title
        """
        # Clean up question
        title = question.strip()

        # Remove question words
        title = re.sub(r'^(what|show|get|find|how many|how much|which)\s+', '', title, flags=re.IGNORECASE)

        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]

        return title

    @staticmethod
    def extract_insights(response_text: str, data: List[Dict]) -> List[Dict[str, str]]:
        """
        Extract and categorize insights from response

        Args:
            response_text: Response text
            data: Query result data

        Returns:
            List of insights with types (positive/negative/neutral/warning)
        """
        insights = []

        # Positive indicators
        positive_patterns = [
            (r'\b(increase|increased|growth|up|higher|improved|growing|gain)\b', 'positive'),
            (r'\b(\d+%\s+increase|\d+%\s+growth)\b', 'positive'),
        ]

        # Negative indicators
        negative_patterns = [
            (r'\b(decrease|decreased|decline|down|lower|dropped|falling|loss)\b', 'negative'),
            (r'\b(\d+%\s+decrease|\d+%\s+decline)\b', 'negative'),
        ]

        # Warning indicators
        warning_patterns = [
            (r'\b(warning|alert|concerning|unusual|anomaly)\b', 'warning'),
        ]

        # Find insights
        for pattern, insight_type in positive_patterns + negative_patterns + warning_patterns:
            matches = re.finditer(pattern, response_text, re.IGNORECASE)
            for match in matches:
                # Get surrounding context (20 chars before and after)
                start = max(0, match.start() - 20)
                end = min(len(response_text), match.end() + 20)
                context = response_text[start:end].strip()

                # Clean up context
                context = re.sub(r'^\W+|\W+$', '', context)

                insights.append({
                    "text": context,
                    "type": insight_type
                })

        # Add data-driven insights
        if data and len(data) > 0:
            numeric_fields = [k for k in data[0].keys() if isinstance(data[0][k], (int, float))]

            for field in numeric_fields:
                values = [row[field] for row in data if field in row]
                if len(values) >= 2:
                    # Calculate trend
                    first_val = values[0]
                    last_val = values[-1]
                    if first_val > 0:
                        change_pct = ((last_val - first_val) / first_val) * 100

                        if abs(change_pct) > 10:  # Significant change
                            insight_type = 'positive' if change_pct > 0 else 'negative'
                            insights.append({
                                "text": f"{field}: {change_pct:+.1f}% change",
                                "type": insight_type
                            })

        return insights[:5]  # Return top 5 insights

    @staticmethod
    def add_color_coding(response_text: str) -> str:
        """
        Add HTML color coding to response text

        Args:
            response_text: Plain text response

        Returns:
            HTML-formatted response with color coding
        """
        # Color code numbers (blue/purple)
        response_text = re.sub(
            r'\b(\d{1,3}(,\d{3})*(\.\d+)?)\b',
            r'<span style="color: #667eea; font-weight: 600;">\1</span>',
            response_text
        )

        # Highlight positive trends (green)
        response_text = re.sub(
            r'\b(increased|growth|up|higher|improved|growing|gain)\b',
            r'<span style="color: #28a745; font-weight: 600;">\1</span>',
            response_text,
            flags=re.IGNORECASE
        )

        # Highlight negative trends (red)
        response_text = re.sub(
            r'\b(decreased|decline|down|lower|dropped|falling|loss)\b',
            r'<span style="color: #dc3545; font-weight: 600;">\1</span>',
            response_text,
            flags=re.IGNORECASE
        )

        # Highlight warnings (orange)
        response_text = re.sub(
            r'\b(warning|alert|concerning|unusual|anomaly)\b',
            r'<span style="color: #ff6b6b; font-weight: 600;">\1</span>',
            response_text,
            flags=re.IGNORECASE
        )

        return response_text
