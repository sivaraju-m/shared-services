#!/usr/bin/env python3
"""
GCP Resource Tagging and Cost Attribution System
===============================================

Ensures proper resource tagging for cost attribution and monitoring.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class ResourceTag:
    """GCP resource tag definition"""

    key: str
    value: str
    required: bool
    description: str


@dataclass
class TaggingRule:
    """Tagging rule for specific resource types"""

    resource_type: str
    required_tags: list[ResourceTag]
    optional_tags: list[ResourceTag]
    cost_allocation: bool


class GCPResourceTagger:
    """Manage GCP resource tagging for cost attribution"""

    def __init__(self, project_id: str, logs_dir: str = "logs"):
        self.project_id = project_id
        self.logs_dir = Path(logs_dir)
        self.tagging_dir = self.logs_dir / "resource_tagging"
        self.tagging_dir.mkdir(exist_ok=True)

        # Define standard tags
        self.standard_tags = [
            ResourceTag("environment", "production", True, "Deployment environment"),
            ResourceTag("project", "ai-trading-machine", True, "Project name"),
            ResourceTag("component", "", True, "System component"),
            ResourceTag("owner", "trading-team", True, "Owning team"),
            ResourceTag("cost-center", "trading-operations", True, "Cost allocation"),
            ResourceTag("created-by", "terraform", False, "Creation method"),
            ResourceTag("managed-by", "terraform", False, "Management tool"),
            ResourceTag("backup-required", "true", False, "Backup requirement"),
            ResourceTag(
                "data-classification", "confidential", False, "Data sensitivity"
            ),
            ResourceTag("compliance", "sebi", False, "Compliance requirements"),
        ]

        # Define tagging rules by resource type
        self.tagging_rules = [
            TaggingRule(
                resource_type="bigquery_dataset",
                required_tags=[
                    ResourceTag(
                        "component", "data-storage", True, "Data storage component"
                    ),
                    ResourceTag(
                        "data-type", "trading-signals", True, "Type of data stored"
                    ),
                ],
                optional_tags=[
                    ResourceTag(
                        "retention-days", "365", False, "Data retention period"
                    ),
                    ResourceTag("pii-data", "false", False, "Contains PII data"),
                ],
                cost_allocation=True,
            ),
            TaggingRule(
                resource_type="cloud_run_service",
                required_tags=[
                    ResourceTag(
                        "component", "api-service", True, "API service component"
                    ),
                    ResourceTag("service-type", "trading-api", True, "Service type"),
                ],
                optional_tags=[
                    ResourceTag(
                        "scaling-policy", "auto", False, "Scaling configuration"
                    ),
                    ResourceTag(
                        "traffic-allocation", "100", False, "Traffic percentage"
                    ),
                ],
                cost_allocation=True,
            ),
            TaggingRule(
                resource_type="storage_bucket",
                required_tags=[
                    ResourceTag(
                        "component", "object-storage", True, "Object storage component"
                    ),
                    ResourceTag("storage-class", "standard", True, "Storage class"),
                ],
                optional_tags=[
                    ResourceTag(
                        "lifecycle-policy", "enabled", False, "Lifecycle management"
                    ),
                    ResourceTag(
                        "public-access", "false", False, "Public access setting"
                    ),
                ],
                cost_allocation=True,
            ),
            TaggingRule(
                resource_type="firestore_database",
                required_tags=[
                    ResourceTag(
                        "component",
                        "realtime-database",
                        True,
                        "Real-time database component",
                    ),
                    ResourceTag("database-type", "document", True, "Database type"),
                ],
                optional_tags=[
                    ResourceTag("backup-frequency", "daily", False, "Backup frequency"),
                    ResourceTag(
                        "read-consistency", "strong", False, "Read consistency level"
                    ),
                ],
                cost_allocation=True,
            ),
            TaggingRule(
                resource_type="cloud_scheduler_job",
                required_tags=[
                    ResourceTag(
                        "component", "automation", True, "Automation component"
                    ),
                    ResourceTag("schedule-type", "trading-job", True, "Job type"),
                ],
                optional_tags=[
                    ResourceTag(
                        "retry-policy", "enabled", False, "Retry configuration"
                    ),
                    ResourceTag("timezone", "asia-kolkata", False, "Job timezone"),
                ],
                cost_allocation=False,
            ),
        ]

        logger.info("GCP resource tagger initialized")

    def generate_terraform_tags(
        self, resource_type: str, component_name: str
    ) -> dict[str, str]:
        """Generate Terraform tags for a resource"""
        try:
            tags = {}

            # Add standard tags
            for tag in self.standard_tags:
                if tag.key == "component":
                    tags[tag.key] = component_name
                else:
                    tags[tag.key] = tag.value

            # Add resource-specific tags
            rule = next(
                (r for r in self.tagging_rules if r.resource_type == resource_type),
                None,
            )
            if rule:
                for tag in rule.required_tags + rule.optional_tags:
                    if tag.key not in tags:  # Don't override standard tags
                        tags[tag.key] = tag.value

            return tags

        except Exception as e:
            logger.error("Error generating tags for {resource_type}: {e}")
            return {}

    def create_terraform_locals_file(self) -> str:
        """Create Terraform locals file with standard tags"""
        try:
            locals_content = """# Standard resource tags for cost attribution
# Generated automatically - do not edit manually

locals {
  # Standard tags applied to all resources
  standard_tags = {
"""

            for tag in self.standard_tags:
                if tag.required:
                    if tag.key == "component":
                        locals_content += "    {tag.key} = var.component_name\n"
                    else:
                        locals_content += f'    {tag.key} = "{tag.value}"\n'

            locals_content += """  }

  # Component-specific tag combinations
  trading_api_tags = merge(local.standard_tags, {
    component     = "trading-api"
    service-type  = "api-endpoint"
    scaling-policy = "auto"
  })

  data_storage_tags = merge(local.standard_tags, {
    component       = "data-storage"
    data-type      = "trading-data"
    retention-days = "365"
  })

  ml_model_tags = merge(local.standard_tags, {
    component    = "ml-models"
    model-type   = "trading-signal"
    version-control = "enabled"
  })

  monitoring_tags = merge(local.standard_tags, {
    component      = "monitoring"
    alert-enabled  = "true"
    dashboard-type = "operational"
  })

  cost_optimization_tags = merge(local.standard_tags, {
    component         = "cost-optimization"
    scheduling-enabled = "true"
    auto-scaling      = "enabled"
  })
}

# Variables for tag customization
variable "component_name" {
  description = "Name of the component for tagging"
  type        = string
  default     = "ai-trading-machine"
}

variable "environment" {
  description = "Environment for resource tagging"
  type        = string
  default     = "production"
}

variable "additional_tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}
"""

            return locals_content

        except Exception as e:
            logger.error("Error creating locals file: {e}")
            return ""

    def generate_cost_attribution_queries(self) -> list[dict[str, str]]:
        """Generate BigQuery queries for cost attribution"""
        try:
            queries = []

            # Cost by component query
            queries.append(
                {
                    "name": "cost_by_component",
                    "description": "Total cost breakdown by system component",
                    "query": """
SELECT
  labels.value AS component,
  SUM(cost) AS total_cost,
  SUM(usage.amount) AS total_usage,
  COUNT(*) AS resource_count,
  DATE(usage_start_time) AS usage_date
FROM `{project_id}.cloud_billing_export.gcp_billing_export_v1_{billing_table}`
CROSS JOIN UNNEST(labels) AS labels
WHERE labels.key = 'component'
  AND usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY component, usage_date
ORDER BY total_cost DESC
                """.strip(),
                }
            )

            # Cost by service type query
            queries.append(
                {
                    "name": "cost_by_service",
                    "description": "Cost breakdown by GCP service",
                    "query": """
SELECT
  service.description AS service_name,
  SUM(cost) AS total_cost,
  SUM(usage.amount) AS total_usage,
  COUNT(DISTINCT labels.value) AS component_count
FROM `{project_id}.cloud_billing_export.gcp_billing_export_v1_{billing_table}`
CROSS JOIN UNNEST(labels) AS labels
WHERE labels.key = 'project'
  AND labels.value = 'ai-trading-machine'
  AND usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY service_name
ORDER BY total_cost DESC
                """.strip(),
                }
            )

            # Daily cost trend query
            queries.append(
                {
                    "name": "daily_cost_trend",
                    "description": "Daily cost trend for the project",
                    "query": """
SELECT
  DATE(usage_start_time) AS usage_date,
  SUM(cost) AS daily_cost,
  labels.value AS component,
  service.description AS service_name
FROM `{project_id}.cloud_billing_export.gcp_billing_export_v1_{billing_table}`
CROSS JOIN UNNEST(labels) AS labels
WHERE labels.key = 'component'
  AND usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY usage_date, component, service_name
ORDER BY usage_date DESC, daily_cost DESC
                """.strip(),
                }
            )

            # Resource utilization query
            queries.append(
                {
                    "name": "resource_utilization",
                    "description": "Resource utilization and cost efficiency",
                    "query": """
WITH resource_costs AS (
  SELECT
    labels.value AS component,
    resource.name AS resource_name,
    SUM(cost) AS resource_cost,
    SUM(usage.amount) AS resource_usage,
    service.description AS service_name
  FROM `{project_id}.cloud_billing_export.gcp_billing_export_v1_{billing_table}`
  CROSS JOIN UNNEST(labels) AS labels
  WHERE labels.key = 'component'
    AND usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  GROUP BY component, resource_name, service_name
)
SELECT
  component,
  service_name,
  COUNT(*) AS resource_count,
  SUM(resource_cost) AS total_cost,
  AVG(resource_cost) AS avg_cost_per_resource,
  SUM(resource_usage) AS total_usage
FROM resource_costs
GROUP BY component, service_name
ORDER BY total_cost DESC
                """.strip(),
                }
            )

            return queries

        except Exception as e:
            logger.error("Error generating cost attribution queries: {e}")
            return []

    def validate_resource_tagging(self) -> dict[str, Any]:
        """Validate that resources are properly tagged"""
        try:
            validation_report = {
                "timestamp": datetime.now().isoformat(),
                "project_id": self.project_id,
                "validation_results": [],
                "summary": {
                    "total_resources_checked": 0,
                    "properly_tagged": 0,
                    "missing_tags": 0,
                    "tag_compliance_rate": 0.0,
                },
                "recommendations": [],
            }

            # This would integrate with actual GCP APIs in production
            # For now, we'll create a framework for validation

            resource_types_to_check = [
                "bigquery_dataset",
                "cloud_run_service",
                "storage_bucket",
                "firestore_database",
                "cloud_scheduler_job",
            ]

            for resource_type in resource_types_to_check:
                # Placeholder for actual GCP resource checking
                # In production, this would use GCP APIs to list and check resources
                validation_result = {
                    "resource_type": resource_type,
                    "resources_found": 0,  # Would be populated by actual API calls
                    "properly_tagged": 0,
                    "missing_required_tags": [],
                    "recommendations": [],
                }

                # Add recommendations based on resource type
                rule = next(
                    (r for r in self.tagging_rules if r.resource_type == resource_type),
                    None,
                )
                if rule:
                    for tag in rule.required_tags:
                        if tag.required:
                            validation_result["recommendations"].append(
                                "Ensure all {resource_type} resources have {tag.key} tag"
                            )

                validation_report["validation_results"].append(validation_result)

            # Generate overall recommendations
            validation_report["recommendations"].extend(
                [
                    "🏷️ Apply standard tags to all GCP resources",
                    "📊 Set up cost attribution dashboard using tagged resources",
                    "🔄 Implement automated tagging in Terraform modules",
                    "📈 Monitor cost trends by component and service",
                    "⚡ Use tags for resource scheduling and optimization",
                ]
            )

            # Save validation report
            report_file = (
                self.tagging_dir
                / "tagging_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(report_file, "w") as f:
                json.dump(validation_report, f, indent=2)

            logger.info("Tagging validation report saved: {report_file}")
            return validation_report

        except Exception as e:
            logger.error("Error validating resource tagging: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "project_id": self.project_id,
            }

    def generate_tagging_terraform_module(self) -> str:
        """Generate Terraform module for consistent resource tagging"""
        try:
            module_content = """# Resource Tagging Module
# Provides consistent tagging across all GCP resources

terraform {
  required_version = ">= 1.3"
}

locals {
  # Merge standard tags with custom tags
  resource_tags = merge(
    {
      environment      = var.environment
      project         = var.project_name
      component       = var.component_name
      owner           = var.owner_team
      cost-center     = var.cost_center
      managed-by      = "terraform"
      created-by      = "terraform"
    },
    var.additional_tags
  )

  # Component-specific tag sets
  api_tags = merge(local.resource_tags, {
    component     = "${var.component_name}-api"
    service-type  = "api-endpoint"
    scaling-policy = "auto"
  })

  storage_tags = merge(local.resource_tags, {
    component      = "${var.component_name}-storage"
    data-type      = var.data_type
    retention-days = var.retention_days
  })

  compute_tags = merge(local.resource_tags, {
    component       = "${var.component_name}-compute"
    instance-type   = var.instance_type
    auto-scaling    = "enabled"
  })
}

# Variables
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name for tagging"
  type        = string
  default     = "ai-trading-machine"
}

variable "component_name" {
  description = "Component name"
  type        = string
}

variable "owner_team" {
  description = "Owning team"
  type        = string
  default     = "trading-team"
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "trading-operations"
}

variable "data_type" {
  description = "Type of data for storage resources"
  type        = string
  default     = "trading-data"
}

variable "retention_days" {
  description = "Data retention period in days"
  type        = string
  default     = "365"
}

variable "instance_type" {
  description = "Compute instance type"
  type        = string
  default     = "standard"
}

variable "additional_tags" {
  description = "Additional tags to apply"
  type        = map(string)
  default     = {}
}

# Outputs
output "standard_tags" {
  description = "Standard resource tags"
  value       = local.resource_tags
}

output "api_tags" {
  description = "API service tags"
  value       = local.api_tags
}

output "storage_tags" {
  description = "Storage resource tags"
  value       = local.storage_tags
}

output "compute_tags" {
  description = "Compute resource tags"
  value       = local.compute_tags
}
"""

            return module_content

        except Exception as e:
            logger.error("Error generating tagging module: {e}")
            return ""

    def create_cost_monitoring_setup(self) -> dict[str, Any]:
        """Create cost monitoring and alerting setup"""
        try:
            setup_config = {
                "timestamp": datetime.now().isoformat(),
                "project_id": self.project_id,
                "cost_monitoring": {
                    "billing_export_dataset": "{self.project_id}_billing_export",
                    "cost_attribution_queries": self.generate_cost_attribution_queries(),
                    "alert_thresholds": {
                        "daily_cost_limit": 50.0,  # USD
                        "monthly_cost_limit": 1000.0,  # USD
                        "component_cost_limit": 200.0,  # USD per component
                        "anomaly_threshold": 50.0,  # % increase from baseline
                    },
                    "monitoring_dashboards": [
                        {
                            "name": "Cost by Component",
                            "description": "Breakdown of costs by system component",
                            "metrics": ["total_cost", "cost_trend", "resource_count"],
                        },
                        {
                            "name": "Service Cost Analysis",
                            "description": "Cost analysis by GCP service",
                            "metrics": [
                                "service_cost",
                                "usage_trend",
                                "efficiency_ratio",
                            ],
                        },
                        {
                            "name": "Resource Utilization",
                            "description": "Resource utilization and optimization opportunities",
                            "metrics": [
                                "utilization_rate",
                                "idle_resources",
                                "optimization_savings",
                            ],
                        },
                    ],
                },
                "tagging_enforcement": {
                    "required_tags": [
                        tag.key for tag in self.standard_tags if tag.required
                    ],
                    "validation_schedule": "daily",
                    "compliance_threshold": 95.0,  # % of resources properly tagged
                    "auto_remediation": True,
                },
                "cost_optimization": {
                    "scheduling_enabled": True,
                    "auto_scaling_enabled": True,
                    "lifecycle_management": True,
                    "rightsizing_recommendations": True,
                },
            }

            # Save setup configuration
            setup_file = (
                self.tagging_dir
                / "cost_monitoring_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(setup_file, "w") as f:
                json.dump(setup_config, f, indent=2)

            logger.info("Cost monitoring setup saved: {setup_file}")
            return setup_config

        except Exception as e:
            logger.error("Error creating cost monitoring setup: {e}")
            return {"timestamp": datetime.now().isoformat(), "error": str(e)}

    def run_tagging_audit(self) -> bool:
        """Run complete resource tagging audit"""
        try:
            logger.info("Starting resource tagging audit")

            # Generate Terraform locals
            locals_content = self.create_terraform_locals_file()
            if locals_content:
                locals_file = Path("infra") / "locals_tags.t"
                with open(locals_file, "w") as f:
                    f.write(locals_content)
                logger.info("Terraform locals file created: {locals_file}")

            # Generate tagging module
            module_content = self.generate_tagging_terraform_module()
            if module_content:
                module_dir = Path("infra") / "modules" / "resource_tagging"
                module_dir.mkdir(exist_ok=True)
                module_file = module_dir / "main.t"
                with open(module_file, "w") as f:
                    f.write(module_content)
                logger.info("Tagging module created: {module_file}")

            # Validate current tagging
            validation_report = self.validate_resource_tagging()

            # Create cost monitoring setup
            cost_setup = self.create_cost_monitoring_setup()

            print("\n🏷️ Resource Tagging Audit")
            print("==========================")
            print("Project: {self.project_id}")
            print("Standard Tags: {len(self.standard_tags)}")
            print("Tagging Rules: {len(self.tagging_rules)}")
            print(
                "Cost Attribution Queries: {len(cost_setup.get('cost_monitoring', {}).get('cost_attribution_queries', []))}"
            )

            # Print recommendations
            recommendations = validation_report.get("recommendations", [])
            if recommendations:
                print("\n💡 Recommendations:")
                for rec in recommendations:
                    print("  {rec}")

            print("\n📁 Files Generated:")
            print("  • infra/locals_tags.tf - Standard tag definitions")
            print("  • infra/modules/resource_tagging/main.tf - Tagging module")
            print("  • logs/resource_tagging/ - Validation and setup reports")

            return True

        except Exception as e:
            logger.error("Error running tagging audit: {e}")
            print("❌ Tagging audit error: {e}")
            return False


def main():
    """Run resource tagging audit"""
    project_id = "ai-trading-machine-prod"  # Default project ID
    tagger = GCPResourceTagger(project_id)
    success = tagger.run_tagging_audit()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
