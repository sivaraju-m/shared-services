"""
# GCP Cost Monitoring and Optimization Scanner
#
# SJ-VERIFY
# - Path: /ai-trading-machine/src/ai_trading_machine/utils
# - Type: cost_monitor
# - Checks: types,gcp,billing,optimization
#
# Purpose: Cost optimization scanner for unused resources and billing alerts
"""

import logging
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Cost alert severity levels"""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class ResourceType(Enum):
    """GCP resource types for cost monitoring"""

    CLOUD_RUN = "cloud_run"
    COMPUTE_ENGINE = "compute_engine"
    CLOUD_STORAGE = "cloud_storage"
    BIGQUERY = "bigquery"
    FIRESTORE = "firestore"
    PUB_SUB = "pub_sub"
    CLOUD_FUNCTIONS = "cloud_functions"
    LOAD_BALANCER = "load_balancer"


class CostThresholdType(Enum):
    """Type of cost threshold to monitor"""

    ABSOLUTE = "absolute"
    PERCENTAGE = "percentage"
    RATE_OF_CHANGE = "rate_of_change"


@dataclass
class CostThreshold:
    """Cost threshold configuration"""

    type: CostThresholdType
    value: float
    notification_channels: List[str] = None


@dataclass
class CostMonitorConfig:
    """Configuration for cost monitoring"""

    project_id: str
    billing_account_id: Optional[str] = None
    thresholds: List[CostThreshold] = None
    check_frequency_hours: int = 24
    last_check: Optional[datetime] = None


@dataclass
class CostAlert:
    """Cost monitoring alert"""

    alert_id: str
    level: AlertLevel
    resource_type: ResourceType
    resource_name: str
    message: str
    current_cost: float
    threshold: float
    recommendation: str
    timestamp: datetime


@dataclass
class UnusedResource:
    """Unused or underutilized resource"""

    resource_id: str
    resource_type: ResourceType
    resource_name: str
    location: str
    usage_metrics: dict[str, float]
    estimated_monthly_cost: float
    recommendation: str
    confidence_score: float


@dataclass
class BillingThreshold:
    """Billing alert threshold configuration"""

    threshold_pct: float
    monthly_budget: float
    alert_level: AlertLevel
    notification_channels: list[str]


def get_current_costs(project_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Get current costs for a GCP project

    Args:
        project_id: GCP project ID
        days: Number of days to look back

    Returns:
        Dictionary with cost information
    """
    # This would normally use the GCP Billing API
    # For this implementation, we'll return mock data
    return {
        "project_id": project_id,
        "total_cost": 123.45,
        "currency": "USD",
        "period_days": days,
        "services": {
            "Compute Engine": 78.90,
            "BigQuery": 23.45,
            "Cloud Storage": 12.34,
            "Other": 8.76,
        },
        "timestamp": datetime.now().isoformat(),
    }


def check_cost_thresholds(
    costs: Dict[str, Any], thresholds: List[CostThreshold]
) -> List[Dict[str, Any]]:
    """
    Check if any cost thresholds have been exceeded

    Args:
        costs: Current cost information
        thresholds: List of thresholds to check

    Returns:
        List of alerts for exceeded thresholds
    """
    alerts = []
    for threshold in thresholds:
        if threshold.type == CostThresholdType.ABSOLUTE:
            if costs["total_cost"] > threshold.value:
                alerts.append(
                    {
                        "type": "threshold_exceeded",
                        "threshold_type": threshold.type.value,
                        "threshold_value": threshold.value,
                        "current_value": costs["total_cost"],
                        "message": f"Cost threshold exceeded: {costs['total_cost']} > {threshold.value} {costs['currency']}",
                    }
                )
    return alerts


class GCPCostMonitor:
    """
    GCP Cost Monitoring and Optimization System

    Features:
    - Real-time cost monitoring
    - Unused resource detection
    - Budget alerts and notifications
    - Cost optimization recommendations
    - Automated resource cleanup suggestions
    """

    def __init__(
        self,
        project_id: str,
        monthly_budget: float = 200.0,  # $200 default budget
        alert_thresholds: Optional[list[BillingThreshold]] = None,
    ):
        """
        Initialize GCP cost monitor

        Args:
            project_id: GCP project ID
            monthly_budget: Monthly budget in USD
            alert_thresholds: Custom alert threshold configuration
        """
        self.project_id = project_id
        self.monthly_budget = monthly_budget

        # Default alert thresholds
        self.alert_thresholds = alert_thresholds or [
            BillingThreshold(75.0, monthly_budget, AlertLevel.WARNING, ["email"]),
            BillingThreshold(
                90.0, monthly_budget, AlertLevel.CRITICAL, ["email", "slack"]
            ),
            BillingThreshold(
                100.0, monthly_budget, AlertLevel.CRITICAL, ["email", "slack", "pager"]
            ),
        ]

        logger.info(
            "💰 Cost Monitor initialized for project {project_id} with ${monthly_budget} budget"
        )

    def setup_billing_alerts(self) -> dict[str, Any]:
        """
        Set up billing alerts for the project

        Returns:
            Configuration for billing alerts
        """
        alert_config = {
            "project_id": self.project_id,
            "monthly_budget": self.monthly_budget,
            "thresholds": [],
        }

        for threshold in self.alert_thresholds:
            threshold_config = {
                "threshold_percent": threshold.threshold_pct,
                "threshold_amount": (threshold.threshold_pct / 100)
                * self.monthly_budget,
                "alert_level": threshold.alert_level.value,
                "notification_channels": threshold.notification_channels,
                "terraform_config": self._generate_terraform_alert(threshold),
            }
            alert_config["thresholds"].append(threshold_config)

        logger.info(
            "📊 Configured {len(self.alert_thresholds)} billing alert thresholds"
        )
        return alert_config

    def _generate_terraform_alert(self, threshold: BillingThreshold) -> str:
        """Generate Terraform configuration for billing alert"""
        return """
resource "google_billing_budget" "trading_budget_{int(threshold.threshold_pct)}" {{
  billing_account = var.billing_account
  display_name    = "AI Trading Machine Budget Alert {threshold.threshold_pct}%"

  budget_filter {{
    projects = ["projects/${{var.project_id}}"]
  }}

  amount {{
    specified_amount {{
      currency_code = "USD"
      units         = "{int(self.monthly_budget)}"
    }}
  }}

  threshold_rules {{
    threshold_percent = {threshold.threshold_pct / 100}
    spend_basis      = "CURRENT_SPEND"
  }}

  all_updates_rule {{
    monitoring_notification_channels = var.notification_channels
    disable_default_iam_recipients   = false
  }}
}}"""

    def scan_unused_resources(self) -> list[UnusedResource]:
        """
        Scan for unused or underutilized GCP resources

        Returns:
            List of unused resources with recommendations
        """
        unused_resources = []

        # Scan different resource types
        unused_resources.extend(self._scan_cloud_run_services())
        unused_resources.extend(self._scan_compute_instances())
        unused_resources.extend(self._scan_storage_buckets())
        unused_resources.extend(self._scan_bigquery_datasets())
        unused_resources.extend(self._scan_firestore_databases())

        logger.info("🔍 Found {len(unused_resources)} potentially unused resources")
        return unused_resources

    def _scan_cloud_run_services(self) -> list[UnusedResource]:
        """Scan for unused Cloud Run services"""
        unused_services = []

        # Mock data - in real implementation, this would query GCP APIs
        mock_services = [
            {
                "name": "unused-strategy-service",
                "location": "us-central1",
                "request_count_7d": 0,
                "cpu_utilization": 0.0,
                "memory_utilization": 0.0,
                "estimated_cost": 15.0,
            },
            {
                "name": "dev-test-service",
                "location": "us-central1",
                "request_count_7d": 2,
                "cpu_utilization": 0.05,
                "memory_utilization": 0.03,
                "estimated_cost": 8.0,
            },
        ]

        for service in mock_services:
            # Identify unused services (no requests in 7 days)
            if service["request_count_7d"] == 0:
                confidence = 0.95
                recommendation = "DELETE - No requests in 7 days"
            elif service["request_count_7d"] < 10 and service["cpu_utilization"] < 0.1:
                confidence = 0.80
                recommendation = (
                    "REVIEW - Very low usage, consider scaling down or deleting"
                )
            else:
                continue

            unused_services.append(
                UnusedResource(
                    resource_id="cloud-run/{service['name']}",
                    resource_type=ResourceType.CLOUD_RUN,
                    resource_name=service["name"],
                    location=service["location"],
                    usage_metrics={
                        "requests_7d": service["request_count_7d"],
                        "cpu_utilization": service["cpu_utilization"],
                        "memory_utilization": service["memory_utilization"],
                    },
                    estimated_monthly_cost=service["estimated_cost"],
                    recommendation=recommendation,
                    confidence_score=confidence,
                )
            )

        return unused_services

    def _scan_compute_instances(self) -> list[UnusedResource]:
        """Scan for unused Compute Engine instances"""
        unused_instances = []

        # Mock data - in real implementation, this would query GCP APIs
        mock_instances = [
            {
                "name": "old-ml-training-vm",
                "zone": "us-central1-b",
                "status": "TERMINATED",
                "cpu_utilization_7d": 0.0,
                "disk_attached": True,
                "estimated_cost": 45.0,
            }
        ]

        for instance in mock_instances:
            if instance["status"] == "TERMINATED":
                unused_instances.append(
                    UnusedResource(
                        resource_id="compute/{instance['name']}",
                        resource_type=ResourceType.COMPUTE_ENGINE,
                        resource_name=instance["name"],
                        location=instance["zone"],
                        usage_metrics={
                            "status": instance["status"],
                            "cpu_utilization_7d": instance["cpu_utilization_7d"],
                        },
                        estimated_monthly_cost=instance["estimated_cost"],
                        recommendation="DELETE - Terminated instance with attached disk",
                        confidence_score=0.99,
                    )
                )

        return unused_instances

    def _scan_storage_buckets(self) -> list[UnusedResource]:
        """Scan for unused Cloud Storage buckets"""
        unused_buckets = []

        # Mock data
        mock_buckets = [
            {
                "name": "temp-test-bucket-20240101",
                "location": "us-central1",
                "size_gb": 0.5,
                "access_count_30d": 0,
                "creation_date": "2024-01-01",
                "estimated_cost": 0.02,
            }
        ]

        for bucket in mock_buckets:
            if bucket["access_count_30d"] == 0 and bucket["size_gb"] < 1:
                unused_buckets.append(
                    UnusedResource(
                        resource_id="storage/{bucket['name']}",
                        resource_type=ResourceType.CLOUD_STORAGE,
                        resource_name=bucket["name"],
                        location=bucket["location"],
                        usage_metrics={
                            "size_gb": bucket["size_gb"],
                            "access_count_30d": bucket["access_count_30d"],
                        },
                        estimated_monthly_cost=bucket["estimated_cost"],
                        recommendation="DELETE - Empty bucket with no recent access",
                        confidence_score=0.90,
                    )
                )

        return unused_buckets

    def _scan_bigquery_datasets(self) -> list[UnusedResource]:
        """Scan for unused BigQuery datasets"""
        unused_datasets = []

        # Mock data
        mock_datasets = [
            {
                "name": "temp_analysis_dataset",
                "location": "US",
                "size_gb": 2.1,
                "query_count_30d": 0,
                "last_modified": "2024-01-15",
                "estimated_cost": 0.05,
            }
        ]

        for dataset in mock_datasets:
            if dataset["query_count_30d"] == 0:
                unused_datasets.append(
                    UnusedResource(
                        resource_id="bigquery/{dataset['name']}",
                        resource_type=ResourceType.BIGQUERY,
                        resource_name=dataset["name"],
                        location=dataset["location"],
                        usage_metrics={
                            "size_gb": dataset["size_gb"],
                            "query_count_30d": dataset["query_count_30d"],
                        },
                        estimated_monthly_cost=dataset["estimated_cost"],
                        recommendation="REVIEW - No queries in 30 days, consider archiving",
                        confidence_score=0.75,
                    )
                )

        return unused_datasets

    def _scan_firestore_databases(self) -> list[UnusedResource]:
        """Scan for unused Firestore databases"""
        # For this demo, assume Firestore is actively used
        return []

    def analyze_cost_trends(self, days: int = 30) -> dict[str, Any]:
        """
        Analyze cost trends over the specified period

        Args:
            days: Number of days to analyze

        Returns:
            Cost trend analysis
        """
        # Mock cost data - in real implementation, this would query Cloud Billing API
        daily_costs = [
            {
                "date": "2024-06-01",
                "cost": 6.50,
                "services": {"cloud_run": 3.20, "bigquery": 1.80, "storage": 1.50},
            },
            {
                "date": "2024-06-02",
                "cost": 7.20,
                "services": {"cloud_run": 3.80, "bigquery": 2.10, "storage": 1.30},
            },
            {
                "date": "2024-06-03",
                "cost": 5.90,
                "services": {"cloud_run": 2.90, "bigquery": 1.50, "storage": 1.50},
            },
        ]

        total_cost = sum(day["cost"] for day in daily_costs)
        avg_daily_cost = total_cost / len(daily_costs)
        projected_monthly = avg_daily_cost * 30

        analysis = {
            "period_days": days,
            "total_cost": total_cost,
            "avg_daily_cost": avg_daily_cost,
            "projected_monthly": projected_monthly,
            "budget_utilization": (projected_monthly / self.monthly_budget) * 100,
            "trend": (
                "increasing"
                if daily_costs[-1]["cost"] > daily_costs[0]["cost"]
                else "decreasing"
            ),
            "cost_breakdown": self._calculate_service_breakdown(daily_costs),
            "recommendations": self._generate_cost_recommendations(projected_monthly),
        }

        return analysis

    def _calculate_service_breakdown(self, daily_costs: list[dict]) -> dict[str, float]:
        """Calculate cost breakdown by service"""
        service_totals = {}

        for day in daily_costs:
            for service, cost in day["services"].items():
                service_totals[service] = service_totals.get(service, 0) + cost

        return service_totals

    def _generate_cost_recommendations(self, projected_monthly: float) -> list[str]:
        """Generate cost optimization recommendations"""
        recommendations = []

        if projected_monthly > self.monthly_budget:
            overage = projected_monthly - self.monthly_budget
            recommendations.append("🚨 Projected to exceed budget by ${overage:.2f}")
            recommendations.append("Consider implementing auto-scaling policies")
            recommendations.append("Review and optimize BigQuery queries")
            recommendations.append("Enable Cloud Run scale-to-zero")

        if projected_monthly < self.monthly_budget * 0.5:
            recommendations.append(
                "💡 Running well under budget - consider upgrading resources for better performance"
            )

        recommendations.extend(
            [
                "📊 Set up committed use discounts for consistent workloads",
                "🗄️ Implement storage lifecycle policies",
                "⚡ Consider preemptible instances for ML training",
                "📈 Monitor and optimize BigQuery slot usage",
            ]
        )

        return recommendations

    def generate_optimization_report(self) -> dict[str, Any]:
        """
        Generate comprehensive cost optimization report

        Returns:
            Complete optimization report with recommendations
        """
        unused_resources = self.scan_unused_resources()
        cost_analysis = self.analyze_cost_trends()
        billing_config = self.setup_billing_alerts()

        # Calculate potential savings
        potential_monthly_savings = sum(
            r.estimated_monthly_cost for r in unused_resources
        )

        report = {
            "project_id": self.project_id,
            "generated_at": datetime.now().isoformat(),
            "monthly_budget": self.monthly_budget,
            "cost_analysis": cost_analysis,
            "unused_resources": {
                "count": len(unused_resources),
                "potential_monthly_savings": potential_monthly_savings,
                "resources": [
                    {
                        "name": r.resource_name,
                        "type": r.resource_type.value,
                        "monthly_cost": r.estimated_monthly_cost,
                        "recommendation": r.recommendation,
                        "confidence": r.confidence_score,
                    }
                    for r in unused_resources
                ],
            },
            "billing_alerts": billing_config,
            "optimization_score": self._calculate_optimization_score(
                cost_analysis, unused_resources
            ),
            "action_items": self._generate_action_items(
                unused_resources, cost_analysis
            ),
        }

        logger.info(
            "📋 Generated optimization report: ${potential_monthly_savings:.2f} potential savings"
        )
        return report

    def _calculate_optimization_score(
        self, cost_analysis: dict[str, Any], unused_resources: list[UnusedResource]
    ) -> dict[str, Any]:
        """Calculate overall optimization score (0-100)"""

        # Budget utilization score (lower is better)
        budget_score = max(0, 100 - cost_analysis["budget_utilization"])

        # Resource efficiency score (fewer unused resources is better)
        resource_efficiency = max(0, 100 - (len(unused_resources) * 10))

        # Cost trend score
        trend_score = 80 if cost_analysis["trend"] == "decreasing" else 60

        overall_score = (
            budget_score * 0.4 + resource_efficiency * 0.4 + trend_score * 0.2
        )

        return {
            "overall": round(overall_score, 1),
            "budget_utilization": round(budget_score, 1),
            "resource_efficiency": round(resource_efficiency, 1),
            "cost_trend": round(trend_score, 1),
            "grade": self._get_grade(overall_score),
        }

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _generate_action_items(
        self, unused_resources: list[UnusedResource], cost_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate prioritized action items"""
        actions = []

        # High-confidence unused resources
        high_confidence_resources = [
            r for r in unused_resources if r.confidence_score > 0.9
        ]
        if high_confidence_resources:
            total_savings = sum(
                r.estimated_monthly_cost for r in high_confidence_resources
            )
            actions.append(
                {
                    "priority": "HIGH",
                    "action": "Delete unused resources",
                    "description": f"Remove {len(high_confidence_resources)} unused resources",
                    "potential_savings": total_savings,
                    "effort": "LOW",
                }
            )

        # Budget management
        if cost_analysis["budget_utilization"] > 80:
            actions.append(
                {
                    "priority": "HIGH",
                    "action": "Implement cost controls",
                    "description": "Set up auto-scaling and resource limits",
                    "potential_savings": cost_analysis["projected_monthly"] * 0.2,
                    "effort": "MEDIUM",
                }
            )

        # Optimization opportunities
        actions.append(
            {
                "priority": "MEDIUM",
                "action": "Enable committed use discounts",
                "description": "Purchase 1-year commitments for stable workloads",
                "potential_savings": cost_analysis["projected_monthly"] * 0.3,
                "effort": "LOW",
            }
        )

        return actions


def monitor_costs(config: Union[CostMonitorConfig, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Monitor costs for a GCP project and generate alerts if thresholds are exceeded

    Args:
        config: Cost monitoring configuration

    Returns:
        Dictionary with monitoring results
    """
    if isinstance(config, dict):
        # Convert dict to CostMonitorConfig
        thresholds = []
        for t in config.get("thresholds", []):
            thresholds.append(CostThreshold(
                type=CostThresholdType(t["type"]),
                value=t["value"],
                notification_channels=t.get("notification_channels")
            ))

            config = CostMonitorConfig(
                project_id=config["project_id"],
                billing_account_id=config.get("billing_account_id"),
                thresholds=thresholds,
                check_frequency_hours=config.get("check_frequency_hours", 24),
                last_check=config.get("last_check")
            )

        # Get current costs
        costs = get_current_costs(config.project_id)

        # Check thresholds
        alerts = []
        if config.thresholds:
            alerts = check_cost_thresholds(costs, config.thresholds)

        # Update last check time
        config.last_check = datetime.now()

        # Build result
        result = {
            "project_id": config.project_id,
            "timestamp": datetime.now().isoformat(),
            "costs": costs,
            "alerts": alerts,
            "status": "alert" if alerts else "ok",
        }

        logger.info(
            f"Cost monitoring complete for {config.project_id}: {len(alerts)} alerts generated"
        )

        return result


def scan_unused_resources(
    project_id: str, monthly_budget: float = 200.0
) -> dict[str, Any]:
    """
    Convenience function to scan for unused GCP resources

    Args:
        project_id: GCP project ID
        monthly_budget: Monthly budget for cost analysis

    Returns:
        Dictionary with unused resources and recommendations
    """
    monitor = GCPCostMonitor(project_id, monthly_budget)
    unused = monitor.scan_unused_resources()

    return {
        "unused_resources": len(unused),
        "potential_savings": sum(r.estimated_monthly_cost for r in unused),
        "resources": [
            {
                "name": r.resource_name,
                "type": r.resource_type.value,
                "cost": r.estimated_monthly_cost,
                "recommendation": r.recommendation,
            }
            for r in unused
        ],
    }
