"""CloudWatch Monitoring Stack for Supply Chain Agentic AI Application

This stack creates:
- CloudWatch dashboards for agent performance visualization
- CloudWatch alarms for error rates, latency, and cost thresholds
- Log groups with appropriate retention policies
- Metric filters for custom metrics
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_logs as logs,
)
from constructs import Construct
from typing import Dict, Any, Optional, List


class MonitoringStack(Stack):
    """CloudWatch monitoring and alerting stack"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Dict[str, Any],
        **kwargs
    ) -> None:
        """Initialize monitoring stack
        
        Args:
            scope: CDK scope
            construct_id: Stack identifier
            config: Configuration dictionary from ConfigurationManager
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.namespace = f"{config['project']['prefix']}/Agents"
        
        # Create SNS topic for alarms if email configured
        self.alarm_topic = None
        alarm_email = config.get('monitoring', {}).get('alarm_email')
        if alarm_email:
            self.alarm_topic = self._create_alarm_topic(alarm_email)
        
        # Create dashboards if enabled
        if config.get('monitoring', {}).get('dashboard_enabled', True):
            self.agent_dashboard = self._create_agent_dashboard()
            self.cost_dashboard = self._create_cost_dashboard()
        
        # Create alarms
        self._create_alarms()
    
    def _create_alarm_topic(self, email: str) -> sns.Topic:
        """Create SNS topic for alarm notifications
        
        Args:
            email: Email address for notifications
            
        Returns:
            SNS Topic
        """
        topic = sns.Topic(
            self,
            "AlarmTopic",
            topic_name=f"{self.config['project']['prefix']}-alarms",
            display_name="Supply Chain Agent Alarms"
        )
        
        topic.add_subscription(
            sns_subscriptions.EmailSubscription(email)
        )
        
        return topic
    
    def _create_agent_dashboard(self) -> cloudwatch.Dashboard:
        """Create CloudWatch dashboard for agent performance
        
        Returns:
            CloudWatch Dashboard
        """
        dashboard = cloudwatch.Dashboard(
            self,
            "AgentDashboard",
            dashboard_name=f"{self.config['project']['prefix']}-agents"
        )
        
        # Define personas
        personas = ["warehouse_manager", "field_engineer", "procurement_specialist"]
        agents = ["sql_agent", "inventory_optimizer", "logistics_agent", "supplier_analyzer"]
        
        # Query Latency by Persona
        latency_widget = cloudwatch.GraphWidget(
            title="Query Latency by Persona (ms)",
            left=[
                cloudwatch.Metric(
                    namespace=self.namespace,
                    metric_name="QueryLatency",
                    statistic="Average",
                    dimensions_map={"Persona": persona},
                    label=persona.replace('_', ' ').title(),
                    period=Duration.minutes(5)
                ) for persona in personas
            ],
            width=12,
            height=6
        )
        
        # Query Count and Success Rate
        query_count_widget = cloudwatch.GraphWidget(
            title="Query Count by Success Status",
            left=[
                cloudwatch.Metric(
                    namespace=self.namespace,
                    metric_name="QueryCount",
                    statistic="Sum",
                    dimensions_map={"Success": "True"},
                    label="Successful",
                    period=Duration.minutes(5),
                    color=cloudwatch.Color.GREEN
                ),
                cloudwatch.Metric(
                    namespace=self.namespace,
                    metric_name="QueryCount",
                    statistic="Sum",
                    dimensions_map={"Success": "False"},
                    label="Failed",
                    period=Duration.minutes(5),
                    color=cloudwatch.Color.RED
                )
            ],
            width=12,
            height=6
        )
        
        # Token Usage by Agent
        token_widget = cloudwatch.GraphWidget(
            title="Token Usage by Agent",
            left=[
                cloudwatch.Metric(
                    namespace=self.namespace,
                    metric_name="TokenUsage",
                    statistic="Sum",
                    dimensions_map={"Agent": agent},
                    label=agent.replace('_', ' ').title(),
                    period=Duration.minutes(5)
                ) for agent in agents
            ],
            width=12,
            height=6
        )
        
        # Error Count by Agent
        error_widget = cloudwatch.GraphWidget(
            title="Error Count by Agent",
            left=[
                cloudwatch.Metric(
                    namespace=self.namespace,
                    metric_name="ErrorCount",
                    statistic="Sum",
                    dimensions_map={"Agent": agent},
                    label=agent.replace('_', ' ').title(),
                    period=Duration.minutes(5)
                ) for agent in agents
            ],
            width=12,
            height=6
        )
        
        # Tool Execution Time
        tool_exec_widget = cloudwatch.GraphWidget(
            title="Tool Execution Time (ms)",
            left=[
                cloudwatch.Metric(
                    namespace=self.namespace,
                    metric_name="ToolExecutionTime",
                    statistic="Average",
                    period=Duration.minutes(5),
                    label="Avg Tool Execution Time"
                )
            ],
            width=12,
            height=6
        )
        
        # Intent Classification Distribution
        intent_widget = cloudwatch.GraphWidget(
            title="Intent Classification Distribution",
            left=[
                cloudwatch.Metric(
                    namespace=self.namespace,
                    metric_name="IntentClassification",
                    statistic="Sum",
                    dimensions_map={"Intent": intent},
                    label=intent.replace('_', ' ').title(),
                    period=Duration.minutes(5)
                ) for intent in ["sql_query", "optimization", "both"]
            ],
            width=12,
            height=6
        )
        
        # Latency Percentiles
        latency_percentile_widget = cloudwatch.GraphWidget(
            title="Query Latency Percentiles (ms)",
            left=[
                cloudwatch.Metric(
                    namespace=self.namespace,
                    metric_name="QueryLatency",
                    statistic="p50",
                    label="p50",
                    period=Duration.minutes(5),
                    color=cloudwatch.Color.BLUE
                ),
                cloudwatch.Metric(
                    namespace=self.namespace,
                    metric_name="QueryLatency",
                    statistic="p95",
                    label="p95",
                    period=Duration.minutes(5),
                    color=cloudwatch.Color.ORANGE
                ),
                cloudwatch.Metric(
                    namespace=self.namespace,
                    metric_name="QueryLatency",
                    statistic="p99",
                    label="p99",
                    period=Duration.minutes(5),
                    color=cloudwatch.Color.RED
                )
            ],
            width=12,
            height=6
        )
        
        # Success Rate Single Value
        success_rate_widget = cloudwatch.SingleValueWidget(
            title="Overall Success Rate",
            metrics=[
                cloudwatch.MathExpression(
                    expression="(success / (success + failed)) * 100",
                    using_metrics={
                        "success": cloudwatch.Metric(
                            namespace=self.namespace,
                            metric_name="QueryCount",
                            statistic="Sum",
                            dimensions_map={"Success": "True"},
                            period=Duration.hours(1)
                        ),
                        "failed": cloudwatch.Metric(
                            namespace=self.namespace,
                            metric_name="QueryCount",
                            statistic="Sum",
                            dimensions_map={"Success": "False"},
                            period=Duration.hours(1)
                        )
                    },
                    label="Success Rate %"
                )
            ],
            width=6,
            height=6
        )
        
        # Total Queries Single Value
        total_queries_widget = cloudwatch.SingleValueWidget(
            title="Total Queries (Last Hour)",
            metrics=[
                cloudwatch.Metric(
                    namespace=self.namespace,
                    metric_name="QueryCount",
                    statistic="Sum",
                    period=Duration.hours(1)
                )
            ],
            width=6,
            height=6
        )
        
        # Add widgets to dashboard
        dashboard.add_widgets(latency_widget, query_count_widget)
        dashboard.add_widgets(token_widget, error_widget)
        dashboard.add_widgets(tool_exec_widget, intent_widget)
        dashboard.add_widgets(latency_percentile_widget)
        dashboard.add_widgets(success_rate_widget, total_queries_widget)
        
        return dashboard
    
    def _create_cost_dashboard(self) -> cloudwatch.Dashboard:
        """Create CloudWatch dashboard for cost tracking
        
        Returns:
            CloudWatch Dashboard
        """
        dashboard = cloudwatch.Dashboard(
            self,
            "CostDashboard",
            dashboard_name=f"{self.config['project']['prefix']}-costs"
        )
        
        agents = ["sql_agent", "inventory_optimizer", "logistics_agent", "supplier_analyzer"]
        
        # Token usage is a proxy for cost
        token_cost_widget = cloudwatch.GraphWidget(
            title="Token Usage (Cost Proxy) by Agent",
            left=[
                cloudwatch.Metric(
                    namespace=self.namespace,
                    metric_name="TokenUsage",
                    statistic="Sum",
                    dimensions_map={"Agent": agent},
                    label=agent.replace('_', ' ').title(),
                    period=Duration.hours(1)
                ) for agent in agents
            ],
            width=12,
            height=6
        )
        
        # Total tokens per day
        daily_tokens_widget = cloudwatch.GraphWidget(
            title="Daily Token Usage",
            left=[
                cloudwatch.Metric(
                    namespace=self.namespace,
                    metric_name="TokenUsage",
                    statistic="Sum",
                    period=Duration.days(1),
                    label="Total Tokens"
                )
            ],
            width=12,
            height=6
        )
        
        # Query count by persona (usage patterns)
        usage_by_persona_widget = cloudwatch.GraphWidget(
            title="Query Count by Persona",
            left=[
                cloudwatch.Metric(
                    namespace=self.namespace,
                    metric_name="QueryCount",
                    statistic="Sum",
                    dimensions_map={"Persona": persona},
                    label=persona.replace('_', ' ').title(),
                    period=Duration.hours(1)
                ) for persona in ["warehouse_manager", "field_engineer", "procurement_specialist"]
            ],
            width=12,
            height=6
        )
        
        # Average tokens per query
        avg_tokens_widget = cloudwatch.GraphWidget(
            title="Average Tokens per Query",
            left=[
                cloudwatch.MathExpression(
                    expression="tokens / queries",
                    using_metrics={
                        "tokens": cloudwatch.Metric(
                            namespace=self.namespace,
                            metric_name="TokenUsage",
                            statistic="Sum",
                            period=Duration.hours(1)
                        ),
                        "queries": cloudwatch.Metric(
                            namespace=self.namespace,
                            metric_name="QueryCount",
                            statistic="Sum",
                            period=Duration.hours(1)
                        )
                    },
                    label="Avg Tokens/Query"
                )
            ],
            width=12,
            height=6
        )
        
        dashboard.add_widgets(token_cost_widget, daily_tokens_widget)
        dashboard.add_widgets(usage_by_persona_widget, avg_tokens_widget)
        
        return dashboard
    
    def _create_alarms(self):
        """Create CloudWatch alarms for monitoring"""
        
        # High error rate alarm
        error_rate_alarm = cloudwatch.Alarm(
            self,
            "HighErrorRateAlarm",
            alarm_name=f"{self.config['project']['prefix']}-high-error-rate",
            alarm_description="Alert when error rate exceeds 10%",
            metric=cloudwatch.MathExpression(
                expression="(errors / total) * 100",
                using_metrics={
                    "errors": cloudwatch.Metric(
                        namespace=self.namespace,
                        metric_name="QueryCount",
                        statistic="Sum",
                        dimensions_map={"Success": "False"},
                        period=Duration.minutes(5)
                    ),
                    "total": cloudwatch.Metric(
                        namespace=self.namespace,
                        metric_name="QueryCount",
                        statistic="Sum",
                        period=Duration.minutes(5)
                    )
                }
            ),
            threshold=10,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # High latency alarm
        latency_alarm = cloudwatch.Alarm(
            self,
            "HighLatencyAlarm",
            alarm_name=f"{self.config['project']['prefix']}-high-latency",
            alarm_description="Alert when p95 latency exceeds 5 seconds",
            metric=cloudwatch.Metric(
                namespace=self.namespace,
                metric_name="QueryLatency",
                statistic="p95",
                period=Duration.minutes(5)
            ),
            threshold=5000,  # 5 seconds in milliseconds
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        # High token usage alarm (cost control)
        token_alarm = cloudwatch.Alarm(
            self,
            "HighTokenUsageAlarm",
            alarm_name=f"{self.config['project']['prefix']}-high-token-usage",
            alarm_description="Alert when hourly token usage exceeds threshold",
            metric=cloudwatch.Metric(
                namespace=self.namespace,
                metric_name="TokenUsage",
                statistic="Sum",
                period=Duration.hours(1)
            ),
            threshold=100000,  # Adjust based on expected usage
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        # Add SNS actions if topic exists
        if self.alarm_topic:
            error_rate_alarm.add_alarm_action(
                cw_actions.SnsAction(self.alarm_topic)
            )
            latency_alarm.add_alarm_action(
                cw_actions.SnsAction(self.alarm_topic)
            )
            token_alarm.add_alarm_action(
                cw_actions.SnsAction(self.alarm_topic)
            )
        
        self.error_rate_alarm = error_rate_alarm
        self.latency_alarm = latency_alarm
        self.token_alarm = token_alarm
