#!/usr/bin/env python3
"""
Infrastructure Monitoring and Alerting System
============================================

Sets up comprehensive monitoring and alerting for infrastructure health.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Set up logging
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MonitoringRule:
    """Infrastructure monitoring rule"""

    name: str
    resource_type: str
    metric_name: str
    threshold: float
    comparison: str  # "greater_than", "less_than", etc.
    duration: str  # "5m", "10m", etc.
    severity: AlertSeverity
    description: str


@dataclass
class AlertChannel:
    """Alert notification channel"""

    name: str
    type: str  # "email", "slack", "pager", etc.
    target: str
    severity_filter: list[AlertSeverity]


class InfrastructureMonitoringManager:
    """Manage infrastructure monitoring and alerting"""

    def __init__(self, project_id: str, logs_dir: str = "logs"):
        self.project_id = project_id
        self.logs_dir = Path(logs_dir)
        self.monitoring_dir = self.logs_dir / "infrastructure_monitoring"
        self.monitoring_dir.mkdir(exist_ok=True)

        # Define alert channels
        self.alert_channels = [
            AlertChannel(
                name="trading-team-email",
                type="email",
                target="trading-team@company.com",
                severity_filter=[
                    AlertSeverity.INFO,
                    AlertSeverity.WARNING,
                    AlertSeverity.ERROR,
                    AlertSeverity.CRITICAL,
                ],
            ),
            AlertChannel(
                name="oncall-pager",
                type="pager",
                target="oncall-team",
                severity_filter=[AlertSeverity.ERROR, AlertSeverity.CRITICAL],
            ),
            AlertChannel(
                name="slack-alerts",
                type="slack",
                target="#trading-alerts",
                severity_filter=[
                    AlertSeverity.WARNING,
                    AlertSeverity.ERROR,
                    AlertSeverity.CRITICAL,
                ],
            ),
            AlertChannel(
                name="slack-critical",
                type="slack",
                target="#trading-critical",
                severity_filter=[AlertSeverity.CRITICAL],
            ),
        ]

        # Define monitoring rules
        self.monitoring_rules = [
            # Cloud Run monitoring
            MonitoringRule(
                name="cloud_run_high_cpu",
                resource_type="cloud_run_service",
                metric_name="cpu_utilization",
                threshold=80.0,
                comparison="greater_than",
                duration="5m",
                severity=AlertSeverity.WARNING,
                description="Cloud Run service CPU utilization is high",
            ),
            MonitoringRule(
                name="cloud_run_high_memory",
                resource_type="cloud_run_service",
                metric_name="memory_utilization",
                threshold=85.0,
                comparison="greater_than",
                duration="3m",
                severity=AlertSeverity.WARNING,
                description="Cloud Run service memory utilization is high",
            ),
            MonitoringRule(
                name="cloud_run_error_rate",
                resource_type="cloud_run_service",
                metric_name="error_rate",
                threshold=5.0,
                comparison="greater_than",
                duration="2m",
                severity=AlertSeverity.ERROR,
                description="Cloud Run service error rate is elevated",
            ),
            MonitoringRule(
                name="cloud_run_no_instances",
                resource_type="cloud_run_service",
                metric_name="instance_count",
                threshold=0,
                comparison="equal",
                duration="10m",
                severity=AlertSeverity.CRITICAL,
                description="Cloud Run service has no running instances",
            ),
            # BigQuery monitoring
            MonitoringRule(
                name="bigquery_query_failures",
                resource_type="bigquery",
                metric_name="job_failure_rate",
                threshold=10.0,
                comparison="greater_than",
                duration="5m",
                severity=AlertSeverity.ERROR,
                description="BigQuery job failure rate is high",
            ),
            MonitoringRule(
                name="bigquery_cost_spike",
                resource_type="bigquery",
                metric_name="daily_cost",
                threshold=100.0,
                comparison="greater_than",
                duration="1h",
                severity=AlertSeverity.WARNING,
                description="BigQuery daily cost is unusually high",
            ),
            MonitoringRule(
                name="bigquery_slot_utilization",
                resource_type="bigquery",
                metric_name="slot_utilization",
                threshold=90.0,
                comparison="greater_than",
                duration="10m",
                severity=AlertSeverity.WARNING,
                description="BigQuery slot utilization is high",
            ),
            # Cloud Storage monitoring
            MonitoringRule(
                name="gcs_api_errors",
                resource_type="storage_bucket",
                metric_name="api_error_rate",
                threshold=5.0,
                comparison="greater_than",
                duration="5m",
                severity=AlertSeverity.ERROR,
                description="Cloud Storage API error rate is elevated",
            ),
            MonitoringRule(
                name="gcs_storage_growth",
                resource_type="storage_bucket",
                metric_name="storage_size_gb",
                threshold=1000.0,
                comparison="greater_than",
                duration="24h",
                severity=AlertSeverity.WARNING,
                description="Cloud Storage bucket size is growing rapidly",
            ),
            # Firestore monitoring
            MonitoringRule(
                name="firestore_read_errors",
                resource_type="firestore",
                metric_name="read_error_rate",
                threshold=2.0,
                comparison="greater_than",
                duration="5m",
                severity=AlertSeverity.ERROR,
                description="Firestore read error rate is elevated",
            ),
            MonitoringRule(
                name="firestore_write_latency",
                resource_type="firestore",
                metric_name="write_latency_p99",
                threshold=1000.0,
                comparison="greater_than",
                duration="5m",
                severity=AlertSeverity.WARNING,
                description="Firestore write latency is high",
            ),
            # Infrastructure cost monitoring
            MonitoringRule(
                name="infrastructure_daily_cost",
                resource_type="billing",
                metric_name="daily_cost",
                threshold=200.0,
                comparison="greater_than",
                duration="6h",
                severity=AlertSeverity.WARNING,
                description="Daily infrastructure cost is unusually high",
            ),
            MonitoringRule(
                name="infrastructure_monthly_cost",
                resource_type="billing",
                metric_name="monthly_cost",
                threshold=3000.0,
                comparison="greater_than",
                duration="24h",
                severity=AlertSeverity.ERROR,
                description="Monthly infrastructure cost exceeds budget",
            ),
        ]

        logger.info(
            "Infrastructure monitoring manager initialized with {len(self.monitoring_rules)} rules"
        )

    def generate_cloud_monitoring_config(self) -> dict[str, Any]:
        """Generate Google Cloud Monitoring configuration"""
        try:
            config = {
                "notification_channels": [
                    {
                        "display_name": channel.name,
                        "type": "monitoring.{channel.type}",
                        "labels": {"address": channel.target},
                        "enabled": True,
                    }
                    for channel in self.alert_channels
                ],
                "alert_policies": [],
                "dashboards": {
                    "infrastructure_overview": {
                        "display_name": "Infrastructure Overview",
                        "grid_layout": {
                            "widgets": [
                                {
                                    "title": "Cloud Run CPU Utilization",
                                    "xy_chart": {
                                        "data_sets": [
                                            {
                                                "time_series_query": {
                                                    "time_series_filter": {
                                                        "filter": 'resource.type="cloud_run_revision"',
                                                        "aggregation": {
                                                            "alignment_period": "60s",
                                                            "per_series_aligner": "ALIGN_MEAN",
                                                        },
                                                    }
                                                }
                                            }
                                        ]
                                    },
                                },
                                {
                                    "title": "BigQuery Job Status",
                                    "xy_chart": {
                                        "data_sets": [
                                            {
                                                "time_series_query": {
                                                    "time_series_filter": {
                                                        "filter": 'resource.type="bigquery_project"',
                                                        "aggregation": {
                                                            "alignment_period": "300s",
                                                            "per_series_aligner": "ALIGN_RATE",
                                                        },
                                                    }
                                                }
                                            }
                                        ]
                                    },
                                },
                                {
                                    "title": "Daily Infrastructure Cost",
                                    "xy_chart": {
                                        "data_sets": [
                                            {
                                                "time_series_query": {
                                                    "time_series_filter": {
                                                        "filter": 'resource.type="global"',
                                                        "aggregation": {
                                                            "alignment_period": "3600s",
                                                            "per_series_aligner": "ALIGN_SUM",
                                                        },
                                                    }
                                                }
                                            }
                                        ]
                                    },
                                },
                            ]
                        },
                    }
                },
                "uptime_checks": [
                    {
                        "display_name": "Trading API Health Check",
                        "monitored_resource": {
                            "type": "uptime_url",
                            "labels": {
                                "project_id": self.project_id,
                                "host": "trading-api.example.com",
                            },
                        },
                        "http_check": {
                            "path": "/health",
                            "port": 443,
                            "use_ssl": True,
                            "validate_ssl": True,
                        },
                        "period": "60s",
                        "timeout": "10s",
                    }
                ],
            }

            # Generate alert policies from monitoring rules
            for rule in self.monitoring_rules:
                alert_policy = {
                    "display_name": rule.name,
                    "documentation": {
                        "content": rule.description,
                        "mime_type": "text/markdown",
                    },
                    "conditions": [
                        {
                            "display_name": "{rule.name}_condition",
                            "condition_threshold": {
                                "filter": self._get_metric_filter(rule),
                                "comparison": self._get_comparison_operator(
                                    rule.comparison
                                ),
                                "threshold_value": rule.threshold,
                                "duration": self._convert_duration(rule.duration),
                                "aggregations": [
                                    {
                                        "alignment_period": "60s",
                                        "per_series_aligner": "ALIGN_MEAN",
                                    }
                                ],
                            },
                        }
                    ],
                    "notification_channels": [
                        "projects/{self.project_id}/notificationChannels/{channel.name}"
                        for channel in self.alert_channels
                        if rule.severity in channel.severity_filter
                    ],
                    "alert_strategy": {
                        "auto_close": "1800s"  # Auto-close after 30 minutes
                    },
                    "severity": rule.severity.value.upper(),
                }
                config["alert_policies"].append(alert_policy)

            return config

        except Exception as e:
            logger.error("Error generating cloud monitoring config: {e}")
            return {}

    def _get_metric_filter(self, rule: MonitoringRule) -> str:
        """Get metric filter for monitoring rule"""
        filter_map = {
            "cloud_run_service": 'resource.type="cloud_run_revision" AND resource.labels.project_id="{self.project_id}"',
            "bigquery": 'resource.type="bigquery_project" AND resource.labels.project_id="{self.project_id}"',
            "storage_bucket": 'resource.type="gcs_bucket" AND resource.labels.project_id="{self.project_id}"',
            "firestore": 'resource.type="firestore_database" AND resource.labels.project_id="{self.project_id}"',
            "billing": f'resource.type="global" AND resource.labels.project_id="{self.project_id}"',
        }

        return filter_map.get(
            rule.resource_type, 'resource.labels.project_id="{self.project_id}"'
        )

    def _get_comparison_operator(self, comparison: str) -> str:
        """Convert comparison string to monitoring API operator"""
        operator_map = {
            "greater_than": "COMPARISON_GREATER_THAN",
            "less_than": "COMPARISON_LESS_THAN",
            "equal": "COMPARISON_EQUAL",
            "not_equal": "COMPARISON_NOT_EQUAL",
            "greater_equal": "COMPARISON_GREATER_THAN_OR_EQUAL",
            "less_equal": "COMPARISON_LESS_THAN_OR_EQUAL",
        }

        return operator_map.get(comparison, "COMPARISON_GREATER_THAN")

    def _convert_duration(self, duration: str) -> str:
        """Convert duration string to seconds"""
        duration_map = {
            "1m": "60s",
            "2m": "120s",
            "3m": "180s",
            "5m": "300s",
            "10m": "600s",
            "15m": "900s",
            "30m": "1800s",
            "1h": "3600s",
            "6h": "21600s",
            "24h": "86400s",
        }

        return duration_map.get(duration, "300s")

    def generate_terraform_monitoring_module(self) -> str:
        """Generate Terraform module for monitoring setup"""
        try:
            terraform_content = """
# Infrastructure Monitoring Module
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

# Notification channels
resource "google_monitoring_notification_channel" "email_channel" {
  display_name = "Trading Team Email"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }

  enabled = true
}

resource "google_monitoring_notification_channel" "slack_channel" {
  count = var.slack_webhook_url != "" ? 1 : 0

  display_name = "Slack Alerts"
  type         = "slack"

  labels = {
    channel_name = var.slack_channel
    url          = var.slack_webhook_url
  }

  enabled = true
}

# Cloud Run monitoring
resource "google_monitoring_alert_policy" "cloud_run_cpu" {
  display_name = "Cloud Run High CPU"
  combiner     = "OR"
  enabled      = true

  conditions {
    display_name = "Cloud Run CPU > 80%"

    condition_threshold {
      filter          = "resource.type=\\"cloud_run_revision\\" resource.label.project_id=\\"${var.project_id}\\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 0.8

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = [
    google_monitoring_notification_channel.email_channel.name
  ]

  alert_strategy {
    auto_close = "1800s"
  }
}

# BigQuery monitoring
resource "google_monitoring_alert_policy" "bigquery_cost" {
  display_name = "BigQuery High Cost"
  combiner     = "OR"
  enabled      = true

  conditions {
    display_name = "BigQuery Daily Cost > $100"

    condition_threshold {
      filter          = "resource.type=\\"bigquery_project\\" resource.label.project_id=\\"${var.project_id}\\""
      duration        = "3600s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 100

      aggregations {
        alignment_period   = "3600s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = [
    google_monitoring_notification_channel.email_channel.name
  ]
}

# Uptime checks
resource "google_monitoring_uptime_check_config" "api_health" {
  display_name = "Trading API Health Check"
  timeout      = "10s"
  period       = "60s"

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.api_host
    }
  }

  http_check {
    path         = "/health"
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }
}

# Monitoring dashboard
resource "google_monitoring_dashboard" "infrastructure" {
  dashboard_json = jsonencode({
    displayName = "Infrastructure Monitoring"

    gridLayout = {
      widgets = [
        {
          title = "Cloud Run Instances"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\\"cloud_run_revision\\""
                  aggregation = {
                    alignmentPeriod    = "60s"
                    perSeriesAligner   = "ALIGN_MEAN"
                  }
                }
              }
            }]
          }
        },
        {
          title = "BigQuery Jobs"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\\"bigquery_project\\""
                  aggregation = {
                    alignmentPeriod    = "300s"
                    perSeriesAligner   = "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        }
      ]
    }
  })
}

# Variables
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "alert_email" {
  description = "Email for alerts"
  type        = string
}

variable "slack_channel" {
  description = "Slack channel for alerts"
  type        = string
  default     = "#trading-alerts"
}

variable "slack_webhook_url" {
  description = "Slack webhook URL"
  type        = string
  default     = ""
}

variable "api_host" {
  description = "API host for uptime checks"
  type        = string
}

# Outputs
output "notification_channels" {
  description = "Created notification channels"
  value = {
    email = google_monitoring_notification_channel.email_channel.name
    slack = var.slack_webhook_url != "" ? google_monitoring_notification_channel.slack_channel[0].name : null
  }
}

output "alert_policies" {
  description = "Created alert policies"
  value = {
    cloud_run_cpu = google_monitoring_alert_policy.cloud_run_cpu.name
    bigquery_cost = google_monitoring_alert_policy.bigquery_cost.name
  }
}

output "dashboard_url" {
  description = "Monitoring dashboard URL"
  value = "https://console.cloud.google.com/monitoring/dashboards/custom/${google_monitoring_dashboard.infrastructure.id}?project=${var.project_id}"
}
"""

            return terraform_content

        except Exception as e:
            logger.error("Error generating Terraform monitoring module: {e}")
            return ""

    def generate_monitoring_setup_guide(self) -> dict[str, Any]:
        """Generate monitoring setup guide and documentation"""
        try:
            setup_guide = {
                "timestamp": datetime.now().isoformat(),
                "project_id": self.project_id,
                "overview": {
                    "description": "Comprehensive infrastructure monitoring and alerting setup",
                    "monitoring_rules": len(self.monitoring_rules),
                    "alert_channels": len(self.alert_channels),
                    "resource_types_covered": list(
                        {rule.resource_type for rule in self.monitoring_rules}
                    ),
                },
                "setup_steps": [
                    {
                        "step": 1,
                        "title": "Deploy Terraform Monitoring Module",
                        "description": "Apply the generated Terraform module to create monitoring resources",
                        "commands": [
                            "cd infra/modules/infrastructure_monitoring",
                            "terraform init",
                            'terraform plan -var="project_id=your-project-id" -var="alert_email=team@company.com" -var="api_host=your-api-host.com"',
                            "terraform apply",
                        ],
                    },
                    {
                        "step": 2,
                        "title": "Configure Alert Channels",
                        "description": "Set up notification channels for different alert types",
                        "details": [
                            "Email notifications for all severity levels",
                            "Slack integration for warnings and errors",
                            "PagerDuty for critical alerts",
                            "SMS for emergency notifications",
                        ],
                    },
                    {
                        "step": 3,
                        "title": "Customize Alert Thresholds",
                        "description": "Adjust alert thresholds based on your specific requirements",
                        "configuration_file": "monitoring_rules.json",
                    },
                    {
                        "step": 4,
                        "title": "Test Alert System",
                        "description": "Verify that alerts are working correctly",
                        "test_scenarios": [
                            "Trigger high CPU alert by load testing",
                            "Test cost alert with BigQuery query",
                            "Verify uptime check notifications",
                        ],
                    },
                    {
                        "step": 5,
                        "title": "Set Up Dashboards",
                        "description": "Create monitoring dashboards for operational visibility",
                        "dashboard_types": [
                            "Infrastructure overview",
                            "Cost monitoring",
                            "Performance metrics",
                            "Error tracking",
                        ],
                    },
                ],
                "monitoring_rules_summary": [
                    {
                        "name": rule.name,
                        "resource": rule.resource_type,
                        "metric": rule.metric_name,
                        "threshold": rule.threshold,
                        "severity": rule.severity.value,
                        "description": rule.description,
                    }
                    for rule in self.monitoring_rules
                ],
                "alert_channels_summary": [
                    {
                        "name": channel.name,
                        "type": channel.type,
                        "target": channel.target,
                        "severities": [s.value for s in channel.severity_filter],
                    }
                    for channel in self.alert_channels
                ],
                "best_practices": [
                    "🔔 Set appropriate alert thresholds to avoid alert fatigue",
                    "📊 Use dashboards for proactive monitoring",
                    "🔄 Regularly review and update monitoring rules",
                    "📱 Ensure critical alerts reach the right people",
                    "📈 Monitor both technical and business metrics",
                    "🚨 Test alert channels regularly",
                    "📝 Document runbooks for alert response",
                ],
                "cost_considerations": [
                    "Monitoring API calls: ~$0.01 per 1000 calls",
                    "Log ingestion: ~$0.50 per GB",
                    "Alert notifications: ~$0.10 per notification",
                    "Dashboard views: Free for first 5 dashboards",
                    "Estimated monthly cost: $20-50 for typical usage",
                ],
            }

            return setup_guide

        except Exception as e:
            logger.error("Error generating monitoring setup guide: {e}")
            return {"timestamp": datetime.now().isoformat(), "error": str(e)}

    def run_monitoring_setup(self) -> bool:
        """Run complete infrastructure monitoring setup"""
        try:
            logger.info("Starting infrastructure monitoring setup")

            # Generate Cloud Monitoring configuration
            monitoring_config = self.generate_cloud_monitoring_config()

            # Generate Terraform module
            terraform_module = self.generate_terraform_monitoring_module()

            # Generate setup guide
            setup_guide = self.generate_monitoring_setup_guide()

            # Save configurations
            config_file = (
                self.monitoring_dir
                / "monitoring_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(config_file, "w") as f:
                json.dump(monitoring_config, f, indent=2)

            guide_file = (
                self.monitoring_dir
                / "setup_guide_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(guide_file, "w") as f:
                json.dump(setup_guide, f, indent=2)

            # Create Terraform module file
            if terraform_module:
                module_dir = Path("infra") / "modules" / "infrastructure_monitoring"
                module_dir.mkdir(parents=True, exist_ok=True)
                module_file = module_dir / "main.t"
                with open(module_file, "w") as f:
                    f.write(terraform_module)
                logger.info("Terraform monitoring module created: {module_file}")

            print("\n📊 Infrastructure Monitoring Setup")
            print("===================================")
            print("Project: {self.project_id}")
            print("Monitoring Rules: {len(self.monitoring_rules)}")
            print("Alert Channels: {len(self.alert_channels)}")
            print("Alert Policies: {len(monitoring_config.get('alert_policies', []))}")

            # Print rule summary by severity
            severity_counts = {}
            for rule in self.monitoring_rules:
                severity = rule.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            print("\n📋 Rules by Severity:")
            for severity, count in severity_counts.items():
                print("  {severity.capitalize()}: {count}")

            # Print resource coverage
            resource_types = {rule.resource_type for rule in self.monitoring_rules}
            print("\n🏗️ Resource Types Monitored:")
            for resource_type in sorted(resource_types):
                count = len(
                    [
                        r
                        for r in self.monitoring_rules
                        if r.resource_type == resource_type
                    ]
                )
                print("  {resource_type}: {count} rules")

            print("\n📁 Files Generated:")
            print(
                "  • infra/modules/infrastructure_monitoring/main.tf - Terraform module"
            )
            print("  • logs/infrastructure_monitoring/ - Configuration and setup guide")

            print("\n📋 Next Steps:")
            print("  1. Review and customize monitoring thresholds")
            print("  2. Configure notification channels (email, Slack, etc.)")
            print("  3. Deploy Terraform monitoring module")
            print("  4. Test alert system and notification channels")
            print("  5. Set up monitoring dashboards")

            return True

        except Exception as e:
            logger.error("Error running monitoring setup: {e}")
            print("❌ Monitoring setup error: {e}")
            return False


def main():
    """Run infrastructure monitoring setup"""
    project_id = "ai-trading-machine-prod"  # Default project ID
    monitoring_manager = InfrastructureMonitoringManager(project_id)
    success = monitoring_manager.run_monitoring_setup()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
