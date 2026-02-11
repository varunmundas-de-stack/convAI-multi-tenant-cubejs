"""
Push Insights Engine
Generates and delivers proactive insights to users
"""
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class Insight:
    """Represents a single insight"""
    insight_id: str
    title: str
    description: str
    insight_type: str  # 'trend', 'anomaly', 'recommendation', 'alert'
    priority: str  # 'high', 'medium', 'low'
    data: Dict[str, Any]
    created_at: datetime
    tenant_id: str
    user_roles: List[str]  # Which roles should see this


class InsightGenerator:
    """
    Generates insights from data analysis
    """

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def generate_daily_insights(self, tenant_id: str, top_n: int = 5) -> List[Insight]:
        """
        Generate top N daily insights for a tenant

        Args:
            tenant_id: Tenant identifier
            top_n: Number of insights to generate

        Returns:
            List of insights
        """
        insights = []

        # 1. Sales Trend Analysis
        trend_insight = self._analyze_sales_trend(tenant_id)
        if trend_insight:
            insights.append(trend_insight)

        # 2. Top Products Performance
        top_products_insight = self._analyze_top_products(tenant_id)
        if top_products_insight:
            insights.append(top_products_insight)

        # 3. Regional Performance
        regional_insight = self._analyze_regional_performance(tenant_id)
        if regional_insight:
            insights.append(regional_insight)

        # 4. Anomaly Detection
        anomaly_insight = self._detect_anomalies(tenant_id)
        if anomaly_insight:
            insights.append(anomaly_insight)

        # 5. Customer Behavior Insight
        customer_insight = self._analyze_customer_behavior(tenant_id)
        if customer_insight:
            insights.append(customer_insight)

        # Sort by priority and return top N
        insights.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x.priority])
        return insights[:top_n]

    def _analyze_sales_trend(self, tenant_id: str) -> Optional[Insight]:
        """Analyze sales trend over last 7 vs previous 7 days"""
        try:
            query = """
            WITH recent AS (
                SELECT SUM(transaction_amount) as amount
                FROM fact_transactions ft
                JOIN dim_date d ON ft.date_key = d.date_key
                WHERE d.date >= CURRENT_DATE - INTERVAL '7 days'
                  AND d.date < CURRENT_DATE
            ),
            previous AS (
                SELECT SUM(transaction_amount) as amount
                FROM fact_transactions ft
                JOIN dim_date d ON ft.date_key = d.date_key
                WHERE d.date >= CURRENT_DATE - INTERVAL '14 days'
                  AND d.date < CURRENT_DATE - INTERVAL '7 days'
            )
            SELECT
                recent.amount as recent_amount,
                previous.amount as previous_amount,
                ((recent.amount - previous.amount) / previous.amount * 100) as change_pct
            FROM recent, previous
            """

            result = self.db_manager.execute_query(tenant_id, query)
            if result and len(result) > 0:
                recent, previous, change_pct = result[0]

                if abs(change_pct) > 5:  # Significant change
                    priority = 'high' if abs(change_pct) > 15 else 'medium'
                    trend = 'increased' if change_pct > 0 else 'decreased'

                    return Insight(
                        insight_id=f"trend_{tenant_id}_{datetime.now().strftime('%Y%m%d')}",
                        title=f"Sales {trend} by {abs(change_pct):.1f}%",
                        description=f"Sales have {trend} from ${previous:,.2f} to ${recent:,.2f} compared to last week.",
                        insight_type='trend',
                        priority=priority,
                        data={
                            'recent_amount': recent,
                            'previous_amount': previous,
                            'change_pct': change_pct
                        },
                        created_at=datetime.now(),
                        tenant_id=tenant_id,
                        user_roles=['manager', 'executive']
                    )
        except Exception as e:
            print(f"Error analyzing sales trend: {e}")

        return None

    def _analyze_top_products(self, tenant_id: str) -> Optional[Insight]:
        """Identify top performing products"""
        try:
            query = """
            SELECT
                p.product_name,
                SUM(t.transaction_amount) as total_sales,
                COUNT(t.transaction_key) as transaction_count
            FROM fact_transactions t
            JOIN dim_product p ON t.product_key = p.product_key
            JOIN dim_date d ON t.date_key = d.date_key
            WHERE d.date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY p.product_name
            ORDER BY total_sales DESC
            LIMIT 3
            """

            result = self.db_manager.execute_query(tenant_id, query)
            if result and len(result) > 0:
                top_products = [
                    {'name': row[0], 'sales': row[1], 'count': row[2]}
                    for row in result
                ]

                product_names = ", ".join([p['name'] for p in top_products[:2]])

                return Insight(
                    insight_id=f"top_products_{tenant_id}_{datetime.now().strftime('%Y%m%d')}",
                    title=f"Top Products: {product_names}",
                    description=f"Top performing products this month generated ${sum(p['sales'] for p in top_products):,.2f} in sales.",
                    insight_type='recommendation',
                    priority='medium',
                    data={'top_products': top_products},
                    created_at=datetime.now(),
                    tenant_id=tenant_id,
                    user_roles=['manager', 'sales_rep', 'executive']
                )
        except Exception as e:
            print(f"Error analyzing top products: {e}")

        return None

    def _analyze_regional_performance(self, tenant_id: str) -> Optional[Insight]:
        """Analyze regional performance"""
        try:
            query = """
            SELECT
                a.region,
                SUM(t.transaction_amount) as total_sales
            FROM fact_transactions t
            JOIN dim_account a ON t.account_key = a.account_key
            JOIN dim_date d ON t.date_key = d.date_key
            WHERE d.date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY a.region
            ORDER BY total_sales DESC
            LIMIT 1
            """

            result = self.db_manager.execute_query(tenant_id, query)
            if result and len(result) > 0:
                top_region, sales = result[0]

                return Insight(
                    insight_id=f"region_{tenant_id}_{datetime.now().strftime('%Y%m%d')}",
                    title=f"Top Region: {top_region}",
                    description=f"{top_region} leads with ${sales:,.2f} in sales this month.",
                    insight_type='trend',
                    priority='low',
                    data={'region': top_region, 'sales': sales},
                    created_at=datetime.now(),
                    tenant_id=tenant_id,
                    user_roles=['manager', 'executive']
                )
        except Exception as e:
            print(f"Error analyzing regional performance: {e}")

        return None

    def _detect_anomalies(self, tenant_id: str) -> Optional[Insight]:
        """Detect anomalies in sales patterns"""
        # Simplified anomaly detection
        try:
            query = """
            WITH daily_sales AS (
                SELECT
                    d.date,
                    SUM(t.transaction_amount) as daily_amount
                FROM fact_transactions t
                JOIN dim_date d ON t.date_key = d.date_key
                WHERE d.date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY d.date
            ),
            stats AS (
                SELECT
                    AVG(daily_amount) as avg_amount,
                    STDDEV(daily_amount) as std_amount
                FROM daily_sales
            )
            SELECT
                ds.date,
                ds.daily_amount,
                s.avg_amount,
                s.std_amount
            FROM daily_sales ds, stats s
            WHERE ds.date = CURRENT_DATE - INTERVAL '1 days'
              AND ABS(ds.daily_amount - s.avg_amount) > (2 * s.std_amount)
            """

            result = self.db_manager.execute_query(tenant_id, query)
            if result and len(result) > 0:
                date, amount, avg, std = result[0]
                deviation = ((amount - avg) / avg * 100)

                return Insight(
                    insight_id=f"anomaly_{tenant_id}_{datetime.now().strftime('%Y%m%d')}",
                    title=f"⚠️ Unusual Sales Pattern Detected",
                    description=f"Yesterday's sales of ${amount:,.2f} deviated {deviation:.1f}% from the 30-day average.",
                    insight_type='anomaly',
                    priority='high',
                    data={'date': str(date), 'amount': amount, 'avg': avg, 'deviation': deviation},
                    created_at=datetime.now(),
                    tenant_id=tenant_id,
                    user_roles=['manager', 'executive']
                )
        except Exception as e:
            print(f"Error detecting anomalies: {e}")

        return None

    def _analyze_customer_behavior(self, tenant_id: str) -> Optional[Insight]:
        """Analyze customer behavior patterns"""
        try:
            query = """
            SELECT
                c.customer_segment,
                COUNT(DISTINCT c.customer_key) as customer_count,
                SUM(t.transaction_amount) as total_spent
            FROM fact_transactions t
            JOIN dim_customer c ON t.customer_key = c.customer_key
            JOIN dim_date d ON t.date_key = d.date_key
            WHERE d.date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY c.customer_segment
            ORDER BY total_spent DESC
            LIMIT 1
            """

            result = self.db_manager.execute_query(tenant_id, query)
            if result and len(result) > 0:
                segment, count, total = result[0]

                return Insight(
                    insight_id=f"customer_{tenant_id}_{datetime.now().strftime('%Y%m%d')}",
                    title=f"Top Customer Segment: {segment}",
                    description=f"{count} customers in '{segment}' segment generated ${total:,.2f} this month.",
                    insight_type='recommendation',
                    priority='medium',
                    data={'segment': segment, 'count': count, 'total': total},
                    created_at=datetime.now(),
                    tenant_id=tenant_id,
                    user_roles=['manager', 'sales_rep', 'executive']
                )
        except Exception as e:
            print(f"Error analyzing customer behavior: {e}")

        return None


class InsightNotifier:
    """
    Delivers insights via various channels
    """

    def __init__(self):
        self.notification_queue = []

    def send_daily_digest(self, user_email: str, insights: List[Insight]):
        """
        Send daily digest email with insights

        Args:
            user_email: Recipient email
            insights: List of insights to include
        """
        # Format insights as HTML
        html_content = self._format_digest_html(insights)

        # Send email (placeholder - integrate with actual email service)
        print(f"📧 Sending daily digest to {user_email}")
        print(f"Insights: {len(insights)}")
        # TODO: Integrate with email service (SendGrid, AWS SES, etc.)

    def send_push_notification(self, user_id: str, insight: Insight):
        """
        Send push notification for high-priority insight

        Args:
            user_id: User identifier
            insight: Insight to notify about
        """
        if insight.priority == 'high':
            print(f"🔔 Pushing notification to user {user_id}: {insight.title}")
            # TODO: Integrate with push notification service (Firebase, OneSignal, etc.)

    def _format_digest_html(self, insights: List[Insight]) -> str:
        """Format insights as HTML email"""
        html = "<html><body>"
        html += "<h2>📊 Your Daily Analytics Digest</h2>"

        for idx, insight in enumerate(insights, 1):
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[insight.priority]
            html += f"<div style='margin: 20px 0; padding: 15px; border-left: 4px solid #667eea;'>"
            html += f"<h3>{priority_emoji} {idx}. {insight.title}</h3>"
            html += f"<p>{insight.description}</p>"
            html += f"</div>"

        html += "</body></html>"
        return html


class InsightScheduler:
    """
    Schedules insight generation and delivery
    """

    def __init__(self, db_manager, generator: InsightGenerator, notifier: InsightNotifier):
        self.db_manager = db_manager
        self.generator = generator
        self.notifier = notifier

    def schedule_daily_digest(self, time_str: str = "08:00"):
        """
        Schedule daily digest generation and delivery

        Args:
            time_str: Time to send digest (HH:MM format)
        """
        schedule.every().day.at(time_str).do(self._generate_and_send_digests)
        print(f"📅 Scheduled daily digest for {time_str}")

    def _generate_and_send_digests(self):
        """Generate and send digests for all tenants"""
        print(f"🚀 Generating daily digests at {datetime.now()}")

        tenants = self.db_manager.get_all_tenants()

        for tenant_id in tenants:
            try:
                # Generate insights
                insights = self.generator.generate_daily_insights(tenant_id, top_n=5)

                # Get users for this tenant (placeholder - integrate with user management)
                tenant_users = self._get_tenant_users(tenant_id)

                # Send digest to each user
                for user in tenant_users:
                    # Filter insights by user role
                    user_insights = [
                        i for i in insights
                        if user['role'] in i.user_roles or 'all' in i.user_roles
                    ]

                    if user_insights:
                        self.notifier.send_daily_digest(user['email'], user_insights)

            except Exception as e:
                print(f"Error generating digest for {tenant_id}: {e}")

    def _get_tenant_users(self, tenant_id: str) -> List[Dict]:
        """Get users for tenant (placeholder)"""
        # TODO: Integrate with actual user management system
        return [
            {'email': 'manager@example.com', 'role': 'manager'},
            {'email': 'executive@example.com', 'role': 'executive'}
        ]

    def start(self):
        """Start the scheduler"""
        print("🎯 Insight scheduler started")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
