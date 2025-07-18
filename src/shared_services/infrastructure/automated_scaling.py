#!/usr/bin/env python3
"""
Automated Scaling Configuration System
=====================================

Configures automated scaling for GCP resources to optimize costs and performance.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
from pathlib import Path
from typing import Any

# Set up logging
logger = logging.getLogger(__name__)


class ScalingPolicy(Enum):
    """Scaling policy types"""

    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    CUSTOM = "custom"


@dataclass
class ScalingRule:
    """Scaling rule definition"""

    resource_type: str
    metric_name: str
    threshold_up: float
    threshold_down: float
    scale_up_amount: int
    scale_down_amount: int
    cooldown_period: int  # seconds
    min_instances: int
    max_instances: int


@dataclass
class SchedulingRule:
    """Resource scheduling rule"""

    resource_type: str
    start_time: time
    end_time: time
    target_capacity: int
    days_of_week: list[str]  # Mon, Tue, etc.
    timezone: str


class AutomatedScalingManager:
    """Manage automated scaling configurations"""

    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.scaling_dir = self.logs_dir / "automated_scaling"
        self.scaling_dir.mkdir(exist_ok=True)

        # Define scaling policies
        self.scaling_policies = {
            ScalingPolicy.AGGRESSIVE: {
                "description": "Fast scaling for high-traffic periods",
                "scale_up_threshold": 60.0,  # % CPU/memory
                "scale_down_threshold": 30.0,
                "scale_up_amount": 2,  # instances
                "scale_down_amount": 1,
                "cooldown_up": 60,  # seconds
                "cooldown_down": 300,
                "max_scale_factor": 5.0,  # max 5x original capacity
            },
            ScalingPolicy.BALANCED: {
                "description": "Balanced scaling for normal operations",
                "scale_up_threshold": 70.0,
                "scale_down_threshold": 40.0,
                "scale_up_amount": 1,
                "scale_down_amount": 1,
                "cooldown_up": 120,
                "cooldown_down": 600,
                "max_scale_factor": 3.0,
            },
            ScalingPolicy.CONSERVATIVE: {
                "description": "Gradual scaling for cost optimization",
                "scale_up_threshold": 80.0,
                "scale_down_threshold": 50.0,
                "scale_up_amount": 1,
                "scale_down_amount": 1,
                "cooldown_up": 300,
                "cooldown_down": 900,
                "max_scale_factor": 2.0,
            },
        }

        # Define trading schedule (Indian market hours)
        self.trading_schedule = [
            SchedulingRule(
                resource_type="cloud_run_service",
                start_time=time(9, 0),  # 9:00 AM
                end_time=time(15, 30),  # 3:30 PM
                target_capacity=100,  # % capacity
                days_of_week=["Mon", "Tue", "Wed", "Thu", "Fri"],
                timezone="Asia/Kolkata",
            ),
            SchedulingRule(
                resource_type="cloud_run_service",
                start_time=time(8, 30),  # Pre-market prep
                end_time=time(9, 0),
                target_capacity=80,
                days_of_week=["Mon", "Tue", "Wed", "Thu", "Fri"],
                timezone="Asia/Kolkata",
            ),
            SchedulingRule(
                resource_type="cloud_run_service",
                start_time=time(15, 30),  # Post-market analysis
                end_time=time(17, 0),
                target_capacity=60,
                days_of_week=["Mon", "Tue", "Wed", "Thu", "Fri"],
                timezone="Asia/Kolkata",
            ),
            SchedulingRule(
                resource_type="cloud_run_service",
                start_time=time(17, 0),  # Off-hours
                end_time=time(8, 30),
                target_capacity=20,  # Minimum capacity
                days_of_week=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                timezone="Asia/Kolkata",
            ),
        ]

        logger.info("Automated scaling manager initialized")

    def generate_cloud_run_scaling_config(
        self, service_name: str, policy: ScalingPolicy = ScalingPolicy.BALANCED
    ) -> dict[str, Any]:
        """Generate Cloud Run scaling configuration"""
        try:
            policy_config = self.scaling_policies[policy]

            scaling_config = {
                "service_name": service_name,
                "scaling_policy": policy.value,
                "auto_scaling": {
                    "min_instances": 0,  # Scale to zero for cost optimization
                    "max_instances": 10,
                    "target_cpu_utilization": policy_config["scale_up_threshold"],
                    "target_memory_utilization": policy_config["scale_up_threshold"],
                    "target_concurrent_requests": 100,
                    "scale_down_delay": f"{policy_config['cooldown_down']}s",
                },
                "resource_limits": {
                    "cpu": "1000m",  # 1 vCPU
                    "memory": "2Gi",  # 2GB RAM
                    "timeout": "300s",  # 5 minutes
                },
                "traffic_allocation": {"latest_revision": 100},
                "revision_settings": {
                    "max_idle_instances": 2,
                    "execution_environment": "gen2",
                },
            }

            return scaling_config

        except Exception:
            logger.error("Error generating Cloud Run config")
            return {}

    def generate_cloud_scheduler_config(self) -> list[dict[str, Any]]:
        """Generate Cloud Scheduler configurations for resource scheduling"""
        try:
            scheduler_configs = []

            for rule in self.trading_schedule:
                # Create scale-up job
                scale_up_config = {
                    "name": 'scale-up-{rule.resource_type}-{rule.start_time.strftime("%H%M")}',
                    "description": "Scale up {rule.resource_type} at {rule.start_time}",
                    "schedule": self._time_to_cron(rule.start_time, rule.days_of_week),
                    "timezone": rule.timezone,
                    "target": {
                        "type": "http",
                        "uri": "/api/scaling/scale-up",
                        "method": "POST",
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps(
                            {
                                "resource_type": rule.resource_type,
                                "target_capacity": rule.target_capacity,
                                "action": "scale_up",
                            }
                        ),
                    },
                    "retry_config": {
                        "retry_count": 3,
                        "max_backoff_duration": "60s",
                        "min_backoff_duration": "5s",
                        "max_doublings": 3,
                    },
                }
                scheduler_configs.append(scale_up_config)

                # Create scale-down job
                if rule.end_time:
                    scale_down_config = {
                        "name": 'scale-down-{rule.resource_type}-{rule.end_time.strftime("%H%M")}',
                        "description": "Scale down {rule.resource_type} at {rule.end_time}",
                        "schedule": self._time_to_cron(
                            rule.end_time, rule.days_of_week
                        ),
                        "timezone": rule.timezone,
                        "target": {
                            "type": "http",
                            "uri": "/api/scaling/scale-down",
                            "method": "POST",
                            "headers": {"Content-Type": "application/json"},
                            "body": json.dumps(
                                {
                                    "resource_type": rule.resource_type,
                                    "target_capacity": 20,  # Minimum capacity
                                    "action": "scale_down",
                                }
                            ),
                        },
                        "retry_config": {
                            "retry_count": 3,
                            "max_backoff_duration": "60s",
                            "min_backoff_duration": "5s",
                            "max_doublings": 3,
                        },
                    }
                    scheduler_configs.append(scale_down_config)

            return scheduler_configs

        except Exception:
            logger.error("Error generating scheduler config")
            return []

    def _time_to_cron(self, time_obj: time, days_of_week: list[str]) -> str:
        """Convert time and days to cron expression"""
        try:
            # Create cron expression: minute hour day month day_of_week
            cron_expr = "{time_obj.minute} {time_obj.hour} * * {day_map}"

            return cron_expr

        except Exception:
            logger.error("Error converting time to cron")
            return "0 9 * * 1-5"  # Default: 9 AM weekdays

    def generate_bigquery_scaling_config(self) -> dict[str, Any]:
        """Generate BigQuery optimization configuration"""
        try:
            config = {
                "dataset_settings": {
                    "default_table_expiration_ms": 31536000000,  # 1 year in milliseconds
                    "default_partition_expiration_ms": 2592000000,  # 30 days
                    "location": "us-central1",  # Mumbai region for lower latency
                    "storage_billing_model": "LOGICAL",
                },
                "query_optimization": {
                    "use_query_cache": True,
                    "use_legacy_sql": False,
                    "maximum_bytes_billed": 1073741824,  # 1GB limit per query
                    "job_timeout_ms": 600000,  # 10 minutes
                    "dry_run_enabled": True,
                },
                "cost_controls": {
                    "daily_bytes_limit": 10737418240,  # 10GB daily limit
                    "monthly_bytes_limit": 322122547200,  # 300GB monthly limit
                    "cost_alert_threshold": 50.0,  # USD
                    "auto_scaling_enabled": True,
                },
                "performance_settings": {
                    "clustering_enabled": True,
                    "partitioning_strategy": "date_column",
                    "materialized_views": True,
                    "streaming_buffer_optimization": True,
                },
            }

            return config

        except Exception:
            logger.error("Error generating BigQuery config")
            return {}

    def generate_gcs_lifecycle_config(self) -> dict[str, Any]:
        """Generate GCS lifecycle and scaling configuration"""
        try:
            config = {
                "lifecycle_rules": [
                    {
                        "action": {
                            "type": "SetStorageClass",
                            "storageClass": "NEARLINE",
                        },
                        "condition": {
                            "age": 30,  # Move to Nearline after 30 days
                            "matches_storage_class": ["STANDARD"],
                        },
                    },
                    {
                        "action": {
                            "type": "SetStorageClass",
                            "storageClass": "COLDLINE",
                        },
                        "condition": {
                            "age": 90,  # Move to Coldline after 90 days
                            "matches_storage_class": ["NEARLINE"],
                        },
                    },
                    {
                        "action": {
                            "type": "SetStorageClass",
                            "storageClass": "ARCHIVE",
                        },
                        "condition": {
                            "age": 365,  # Move to Archive after 1 year
                            "matches_storage_class": ["COLDLINE"],
                        },
                    },
                    {
                        "action": {"type": "Delete"},
                        "condition": {
                            "age": 2555,  # Delete after 7 years (SEBI requirement)
                            "matches_storage_class": ["ARCHIVE"],
                        },
                    },
                ],
                "cost_optimization": {
                    "uniform_bucket_level_access": True,
                    "public_access_prevention": "enforced",
                    "default_storage_class": "STANDARD",
                    "versioning_enabled": True,
                    "retention_policy": {
                        "retention_period_seconds": 2592000  # 30 days minimum
                    },
                },
                "performance_settings": {
                    "location": "asia-south1",
                    "turbo_replication": False,  # Cost optimization
                    "cache_control": "public, max-age=3600",
                },
            }

            return config

        except Exception:
            logger.error("Error generating GCS config")
            return {}

    def create_terraform_scaling_modules(self) -> dict[str, str]:
        """Create Terraform modules for automated scaling"""
        try:
            modules = {}

            # Cloud Run autoscaling module
            modules[
                "cloud_run_autoscaling"
            ] = """
# Cloud Run Autoscaling Module
resource "google_cloud_run_service" "autoscaling_service" {
  name     = var.service_name
  location = var.region

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"         = var.min_instances
        "autoscaling.knative.dev/maxScale"         = var.max_instances
        "autoscaling.knative.dev/targetCPUUtilizationPercentage" = var.target_cpu_utilization
        "run.googleapis.com/execution-environment" = "gen2"
        "run.googleapis.com/cpu-throttling"        = "false"
      }
      labels = local.standard_tags
    }

    spec {
      container_concurrency = var.max_concurrent_requests
      timeout_seconds      = var.timeout_seconds
      service_account_name = var.service_account_email

      containers {
        image = var.container_image

        resources {
          limits = {
            cpu    = var.cpu_limit
            memory = var.memory_limit
          }
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "target_cpu_utilization" {
  description = "Target CPU utilization percentage"
  type        = number
  default     = 70
}
"""

            # Cloud Scheduler module for resource scheduling
            modules[
                "cloud_scheduler"
            ] = """
# Cloud Scheduler Module for Resource Scheduling
resource "google_cloud_scheduler_job" "scaling_jobs" {
  for_each = var.scheduling_rules

  name             = each.value.name
  description      = each.value.description
  schedule         = each.value.schedule
  time_zone        = each.value.timezone
  attempt_deadline = "60s"

  retry_config {
    retry_count          = 3
    max_backoff_duration = "60s"
    min_backoff_duration = "5s"
    max_doublings        = 3
  }

  http_target {
    http_method = each.value.method
    uri         = "${var.api_endpoint}${each.value.path}"

    headers = {
      "Content-Type" = "application/json"
    }

    body = base64encode(each.value.body)

    oidc_token {
      service_account_email = var.scheduler_service_account
      audience              = var.api_endpoint
    }
  }
}

variable "scheduling_rules" {
  description = "Map of scheduling rules"
  type = map(object({
    name        = string
    description = string
    schedule    = string
    timezone    = string
    method      = string
    path        = string
    body        = string
  }))
}
"""

            # BigQuery cost optimization module
            modules[
                "bigquery_optimization"
            ] = """
# BigQuery Cost Optimization Module
resource "google_bigquery_dataset" "optimized_dataset" {
  dataset_id                  = var.dataset_id
  friendly_name              = var.dataset_name
  description                = var.dataset_description
  location                   = var.location
  default_table_expiration_ms = var.default_table_expiration_ms
  delete_contents_on_destroy  = false

  labels = local.standard_tags

  access {
    role          = "OWNER"
    user_by_email = var.dataset_owner_email
  }

  access {
    role   = "READER"
    domain = var.organization_domain
  }
}

resource "google_bigquery_job" "query_optimization" {
  job_id = "query_optimization_${random_id.job_id.hex}"

  query {
    query = "SELECT * FROM `${google_bigquery_dataset.optimized_dataset.dataset_id}.*` LIMIT 0"

    default_dataset {
      dataset_id = google_bigquery_dataset.optimized_dataset.dataset_id
      project_id = var.project_id
    }

    maximum_bytes_billed = var.max_query_bytes
    use_query_cache      = true
    use_legacy_sql       = false
  }
}

resource "random_id" "job_id" {
  byte_length = 8
}
"""

            return modules

        except Exception:
            logger.error("Error creating Terraform modules")
            return {}

    def generate_scaling_configuration_report(self) -> dict[str, Any]:
        """Generate comprehensive scaling configuration report"""
        try:
            config_report = {
                "timestamp": datetime.now().isoformat(),
                "scaling_configurations": {
                    "cloud_run": self.generate_cloud_run_scaling_config("trading-api"),
                    "bigquery": self.generate_bigquery_scaling_config(),
                    "gcs": self.generate_gcs_lifecycle_config(),
                },
                "scheduling_rules": [
                    {
                        "resource_type": rule.resource_type,
                        "start_time": rule.start_time.strftime("%H:%M"),
                        "end_time": rule.end_time.strftime("%H:%M"),
                        "target_capacity": rule.target_capacity,
                        "days": rule.days_of_week,
                        "timezone": rule.timezone,
                    }
                    for rule in self.trading_schedule
                ],
                "scheduler_jobs": self.generate_cloud_scheduler_config(),
                "cost_optimization": {
                    "estimated_monthly_savings": {
                        "cloud_run": {"min": 200, "max": 500, "currency": "USD"},
                        "bigquery": {"min": 100, "max": 300, "currency": "USD"},
                        "gcs": {"min": 50, "max": 150, "currency": "USD"},
                    },
                    "scaling_policies": {
                        policy.value: config
                        for policy, config in self.scaling_policies.items()
                    },
                },
                "terraform_modules": self.create_terraform_scaling_modules(),
                "monitoring": {
                    "metrics_to_track": [
                        "cloud_run_instance_count",
                        "bigquery_bytes_processed",
                        "gcs_storage_usage",
                        "cost_per_component",
                        "scaling_events",
                    ],
                    "alert_conditions": [
                        "scaling_failures",
                        "cost_threshold_exceeded",
                        "performance_degradation",
                        "resource_starvation",
                    ],
                },
            }

            # Save configuration report
            report_file = (
                self.scaling_dir
                / "scaling_configuration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(report_file, "w") as f:
                json.dump(config_report, f, indent=2)

            logger.info("Scaling configuration report saved: {report_file}")
            return config_report

        except Exception:
            logger.error("Error generating scaling configuration")
            return {"timestamp": datetime.now().isoformat(), "error": "Unknown error"}

    def run_scaling_setup(self) -> bool:
        """Run complete automated scaling setup"""
        try:
            logger.info("Starting automated scaling setup")

            # Generate configuration report
            config_report = self.generate_scaling_configuration_report()

            # Create Terraform modules
            modules = self.create_terraform_scaling_modules()
            for module_name, module_content in modules.items():
                module_dir = Path("infra") / "modules" / "autoscaling_{module_name}"
                module_dir.mkdir(parents=True, exist_ok=True)
                module_file = module_dir / "main.t"
                with open(module_file, "w") as f:
                    f.write(module_content)
                logger.info("Terraform module created: {module_file}")

            print("\n⚡ Automated Scaling Setup")
            print("==========================")
            print("Scaling Policies: {len(self.scaling_policies)}")
            print("Scheduling Rules: {len(self.trading_schedule)}")
            print("Scheduler Jobs: {len(config_report.get('scheduler_jobs', []))}")
            print("Terraform Modules: {len(modules)}")

            # Print estimated savings
            cost_opt = config_report.get("cost_optimization", {})
            savings = cost_opt.get("estimated_monthly_savings", {})

            print("\n💰 Estimated Monthly Savings:")
            for service, saving in savings.items():
                print(
                    "  {service.capitalize()}: ${saving.get('min', 0)}-${saving.get('max', 0)} USD"
                )

            print("\n📁 Files Generated:")
            print("  • infra/modules/autoscaling_* - Terraform scaling modules")
            print("  • logs/automated_scaling/ - Configuration reports")

            print("\n📋 Next Steps:")
            print("  1. Review generated Terraform modules")
            print("  2. Apply scaling configurations to infrastructure")
            print("  3. Set up monitoring for scaling events")
            print("  4. Test scaling policies in staging environment")

            return True

        except Exception:
            logger.error("Error running scaling setup")
            print("❌ Scaling setup error")
            return False


def main():
    """Run automated scaling setup"""
    scaling_manager = AutomatedScalingManager()
    success = scaling_manager.run_scaling_setup()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
