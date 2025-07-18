#!/usr/bin/env python3
"""
Infrastructure Completeness Checker
==================================

Checks completeness of Terraform infrastructure and generates status report.
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class InfraComponent:
    """Infrastructure component definition"""

    name: str
    path: str
    required: bool
    description: str
    dependencies: list[str]
    cost_optimized: bool = False


@dataclass
class InfraStatus:
    """Infrastructure component status"""

    component: InfraComponent
    exists: bool
    terraform_valid: bool
    resource_count: int
    issues: list[str]
    recommendations: list[str]


class InfrastructureChecker:
    """Check infrastructure completeness and status"""

    def __init__(self, infra_dir: str = "infra"):
        self.infra_dir = Path(infra_dir)
        self.logs_dir = Path("logs") / "infrastructure_checks"
        self.logs_dir.mkdir(exist_ok=True)

        # Define required infrastructure components
        self.required_components = [
            InfraComponent(
                name="bigquery",
                path="modules/bq",
                required=True,
                description="BigQuery datasets and tables for data storage",
                dependencies=["iam"],
            ),
            InfraComponent(
                name="bigquery_cost_optimized",
                path="modules/bq_cost_optimized",
                required=True,
                description="Cost-optimized BigQuery configuration",
                dependencies=["bigquery"],
                cost_optimized=True,
            ),
            InfraComponent(
                name="firestore",
                path="modules/firestore",
                required=True,
                description="Firestore database for real-time data",
                dependencies=["iam"],
            ),
            InfraComponent(
                name="gcs",
                path="modules/gcs",
                required=True,
                description="Google Cloud Storage buckets",
                dependencies=["iam"],
            ),
            InfraComponent(
                name="gcs_cost_optimized",
                path="modules/gcs_cost_optimized",
                required=True,
                description="Cost-optimized GCS configuration",
                dependencies=["gcs"],
                cost_optimized=True,
            ),
            InfraComponent(
                name="cloudrun",
                path="modules/cloudrun",
                required=True,
                description="Cloud Run services for API endpoints",
                dependencies=["iam", "gcs"],
            ),
            InfraComponent(
                name="cloudrun_cost_optimized",
                path="modules/cloudrun_cost_optimized",
                required=True,
                description="Cost-optimized Cloud Run configuration",
                dependencies=["cloudrun"],
                cost_optimized=True,
            ),
            InfraComponent(
                name="github_actions",
                path="modules/github_actions",
                required=True,
                description="GitHub Actions service account and permissions",
                dependencies=["iam"],
            ),
            InfraComponent(
                name="iam",
                path="modules/iam",
                required=True,
                description="IAM roles and service accounts",
                dependencies=[],
            ),
            InfraComponent(
                name="secrets",
                path="modules/secrets",
                required=True,
                description="Secret Manager for sensitive configuration",
                dependencies=["iam"],
            ),
            InfraComponent(
                name="scheduler",
                path="modules/scheduler",
                required=True,
                description="Cloud Scheduler for automated jobs",
                dependencies=["cloudrun", "iam"],
            ),
            InfraComponent(
                name="cost_monitoring",
                path="modules/cost_monitoring",
                required=True,
                description="Cost monitoring and alerting",
                dependencies=["iam"],
                cost_optimized=True,
            ),
            InfraComponent(
                name="signal_validation",
                path="modules/signal_validation",
                required=False,
                description="Signal validation infrastructure",
                dependencies=["cloudrun", "bigquery"],
            ),
            InfraComponent(
                name="vpc",
                path="modules/vpc",
                required=False,
                description="VPC networking configuration",
                dependencies=[],
            ),
            InfraComponent(
                name="pubsub",
                path="modules/pubsub",
                required=False,
                description="Pub/Sub topics for event streaming",
                dependencies=["iam"],
            ),
        ]

        logger.info(
            "Infrastructure checker initialized with {len(self.required_components)} components"
        )

    def check_terraform_syntax(self, component_path: Path) -> tuple[bool, list[str]]:
        """Check Terraform syntax for a component"""
        issues = []

        try:
            if not component_path.exists():
                return False, ["Component directory does not exist"]

            # Check for main.tf file
            main_tf = component_path / "main.t"
            if not main_tf.exists():
                issues.append("Missing main.tf file")

            # Check for variables.tf
            variables_tf = component_path / "variables.t"
            if not variables_tf.exists():
                issues.append("Missing variables.tf file")

            # Check for outputs.tf
            outputs_tf = component_path / "outputs.t"
            if not outputs_tf.exists():
                issues.append("Missing outputs.tf file")

            # Run terraform validate if possible
            try:
                result = subprocess.run(
                    ["terraform", "validate"],
                    cwd=component_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode != 0:
                    issues.append("Terraform validation failed: {result.stderr}")

            except subprocess.TimeoutExpired:
                issues.append("Terraform validation timed out")
            except FileNotFoundError:
                issues.append("Terraform CLI not available")
            except Exception as e:
                issues.append("Error running terraform validate: {e}")

            return len(issues) == 0, issues

        except Exception as e:
            return False, ["Error checking syntax: {e}"]

    def count_terraform_resources(self, component_path: Path) -> int:
        """Count Terraform resources in a component"""
        try:
            resource_count = 0

            for tf_file in component_path.glob("*.t"):
                try:
                    with open(tf_file) as f:
                        content = f.read()

                    # Simple resource counting (count "resource" blocks)
                    lines = content.split("\n")
                    for line in lines:
                        stripped = line.strip()
                        if stripped.startswith('resource "') and "{" in stripped:
                            resource_count += 1

                except Exception as e:
                    logger.warning("Error reading {tf_file}: {e}")

            return resource_count

        except Exception as e:
            logger.error("Error counting resources in {component_path}: {e}")
            return 0

    def generate_component_recommendations(self, status: InfraStatus) -> list[str]:
        """Generate recommendations for a component"""
        recommendations = []

        try:
            component = status.component

            if not status.exists:
                recommendations.append(
                    "Create {component.name} module in {component.path}"
                )
                recommendations.append("Implement {component.description}")

            if status.exists and not status.terraform_valid:
                recommendations.append("Fix Terraform syntax errors")
                recommendations.append(
                    "Add missing standard files (variables.tf, outputs.tf)"
                )

            if status.resource_count == 0:
                recommendations.append("Add Terraform resources to the module")

            if component.cost_optimized and status.resource_count < 3:
                recommendations.append("Implement cost optimization features")
                recommendations.append("Add resource scheduling and scaling policies")

            if component.required and len(status.issues) > 0:
                recommendations.append("Address issues as this is a required component")

        except Exception as e:
            logger.error("Error generating recommendations: {e}")
            recommendations.append("Review component manually")

        return recommendations

    def check_component_status(self, component: InfraComponent) -> InfraStatus:
        """Check status of a single infrastructure component"""
        try:
            component_path = self.infra_dir / component.path
            exists = component_path.exists()

            terraform_valid = False
            issues = []
            resource_count = 0

            if exists:
                terraform_valid, syntax_issues = self.check_terraform_syntax(
                    component_path
                )
                issues.extend(syntax_issues)
                resource_count = self.count_terraform_resources(component_path)
            else:
                issues.append("Component does not exist")

            # Check dependencies
            for dep_name in component.dependencies:
                dep_component = next(
                    (c for c in self.required_components if c.name == dep_name), None
                )
                if dep_component:
                    dep_path = self.infra_dir / dep_component.path
                    if not dep_path.exists():
                        issues.append("Missing dependency: {dep_name}")

            status = InfraStatus(
                component=component,
                exists=exists,
                terraform_valid=terraform_valid,
                resource_count=resource_count,
                issues=issues,
                recommendations=[],
            )

            status.recommendations = self.generate_component_recommendations(status)

            return status

        except Exception as e:
            logger.error("Error checking component {component.name}: {e}")
            return InfraStatus(
                component=component,
                exists=False,
                terraform_valid=False,
                resource_count=0,
                issues=["Check failed: {e}"],
                recommendations=["Manual review required"],
            )

    def check_infrastructure_completeness(self) -> dict[str, Any]:
        """Check completeness of entire infrastructure"""
        try:
            completeness_report = {
                "timestamp": datetime.now().isoformat(),
                "total_components": len(self.required_components),
                "required_components": len(
                    [c for c in self.required_components if c.required]
                ),
                "optional_components": len(
                    [c for c in self.required_components if not c.required]
                ),
                "component_status": [],
                "summary": {
                    "existing_components": 0,
                    "valid_components": 0,
                    "components_with_resources": 0,
                    "cost_optimized_components": 0,
                    "total_issues": 0,
                    "required_missing": 0,
                    "completion_percentage": 0.0,
                },
                "recommendations": [],
                "next_steps": [],
            }

            # Check each component
            for component in self.required_components:
                status = self.check_component_status(component)

                # Add to report
                component_data = {
                    "name": component.name,
                    "path": component.path,
                    "required": component.required,
                    "cost_optimized": component.cost_optimized,
                    "exists": status.exists,
                    "terraform_valid": status.terraform_valid,
                    "resource_count": status.resource_count,
                    "issues": status.issues,
                    "recommendations": status.recommendations,
                }
                completeness_report["component_status"].append(component_data)

                # Update summary
                if status.exists:
                    completeness_report["summary"]["existing_components"] += 1

                if status.terraform_valid:
                    completeness_report["summary"]["valid_components"] += 1

                if status.resource_count > 0:
                    completeness_report["summary"]["components_with_resources"] += 1

                if component.cost_optimized and status.exists:
                    completeness_report["summary"]["cost_optimized_components"] += 1

                completeness_report["summary"]["total_issues"] += len(status.issues)

                if component.required and not status.exists:
                    completeness_report["summary"]["required_missing"] += 1

            # Calculate completion percentage
            existing_required = len(
                [
                    c
                    for c in completeness_report["component_status"]
                    if c["required"] and c["exists"]
                ]
            )
            total_required = completeness_report["required_components"]

            if total_required > 0:
                completeness_report["summary"]["completion_percentage"] = (
                    existing_required / total_required
                ) * 100

            # Generate overall recommendations
            if completeness_report["summary"]["required_missing"] > 0:
                completeness_report["recommendations"].append(
                    "🚨 {completeness_report['summary']['required_missing']} required components are missing"
                )

            if completeness_report["summary"]["total_issues"] > 0:
                completeness_report["recommendations"].append(
                    "🔧 Fix {completeness_report['summary']['total_issues']} infrastructure issues"
                )

            cost_optimized_existing = len(
                [
                    c
                    for c in completeness_report["component_status"]
                    if c["cost_optimized"] and c["exists"]
                ]
            )
            total_cost_optimized = len(
                [c for c in self.required_components if c.cost_optimized]
            )

            if cost_optimized_existing < total_cost_optimized:
                missing_cost_opt = total_cost_optimized - cost_optimized_existing
                completeness_report["recommendations"].append(
                    "💰 Implement {missing_cost_opt} cost optimization components"
                )

            if completeness_report["summary"]["completion_percentage"] < 100:
                completeness_report["recommendations"].append(
                    "📋 Complete missing infrastructure components for full deployment"
                )

            # Generate next steps
            missing_required = [
                c
                for c in completeness_report["component_status"]
                if c["required"] and not c["exists"]
            ]

            if missing_required:
                completeness_report["next_steps"].append(
                    "1. Create missing required components:"
                )
                for comp in missing_required[:3]:  # Show top 3
                    completeness_report["next_steps"].append("   • {comp['name']}")

            components_with_issues = [
                c
                for c in completeness_report["component_status"]
                if c["exists"] and len(c["issues"]) > 0
            ]

            if components_with_issues:
                completeness_report["next_steps"].append(
                    "2. Fix components with issues:"
                )
                for comp in components_with_issues[:3]:  # Show top 3
                    completeness_report["next_steps"].append(
                        "   • {comp['name']} ({len(comp['issues'])} issues)"
                    )

            if not missing_required and not components_with_issues:
                completeness_report["next_steps"].append(
                    "✅ Infrastructure appears complete"
                )
                completeness_report["next_steps"].append("🚀 Ready for deployment")

            # Save report
            report_file = (
                self.logs_dir
                / "infrastructure_completeness_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(report_file, "w") as f:
                json.dump(completeness_report, f, indent=2)

            logger.info("Infrastructure completeness report saved: {report_file}")
            return completeness_report

        except Exception as e:
            logger.error("Error checking infrastructure completeness: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error_message": str(e),
            }

    def run_infrastructure_audit(self) -> bool:
        """Run complete infrastructure audit"""
        try:
            logger.info("Starting infrastructure audit")

            completeness_report = self.check_infrastructure_completeness()

            if completeness_report.get("status") == "error":
                print(
                    "❌ Infrastructure audit failed: {completeness_report.get('error_message')}"
                )
                return False

            # Print summary
            summary = completeness_report.get("summary", {})

            print("\n🏗️ Infrastructure Completeness Report")
            print("======================================")
            print("Total Components: {completeness_report.get('total_components')}")
            print(
                "Required Components: {completeness_report.get('required_components')}"
            )
            print("Completion: {summary.get('completion_percentage', 0):.1f}%")
            print("Existing: {summary.get('existing_components')}")
            print("Valid: {summary.get('valid_components')}")
            print("With Resources: {summary.get('components_with_resources')}")
            print("Cost Optimized: {summary.get('cost_optimized_components')}")
            print("Total Issues: {summary.get('total_issues')}")

            recommendations = completeness_report.get("recommendations", [])
            if recommendations:
                print("\n💡 Recommendations:")
                for rec in recommendations:
                    print("  {rec}")

            next_steps = completeness_report.get("next_steps", [])
            if next_steps:
                print("\n📋 Next Steps:")
                for step in next_steps:
                    print("  {step}")

            # Return success if completion > 80%
            completion_pct = summary.get("completion_percentage", 0)
            return completion_pct >= 80.0

        except Exception as e:
            logger.error("Error running infrastructure audit: {e}")
            print("❌ Infrastructure audit error: {e}")
            return False


def main():
    """Run infrastructure completeness check"""
    checker = InfrastructureChecker()
    success = checker.run_infrastructure_audit()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
