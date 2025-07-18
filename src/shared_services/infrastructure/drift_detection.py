"""
Automated Infrastructure Drift Detection System
Monitors and alerts on infrastructure drift using terraform and cloud APIs
"""

import difflib
import hashlib
import json
import logging
import os
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DriftSeverity(Enum):
    """Drift severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DriftType(Enum):
    """Types of infrastructure drift"""

    CONFIGURATION = "configuration"
    RESOURCE_COUNT = "resource_count"
    RESOURCE_STATE = "resource_state"
    SECURITY = "security"
    COST = "cost"
    PERMISSIONS = "permissions"


@dataclass
class DriftEvent:
    """Infrastructure drift event"""

    id: str
    timestamp: datetime
    drift_type: DriftType
    severity: DriftSeverity
    resource_type: str
    resource_name: str
    expected_value: str
    actual_value: str
    diff: str
    terraform_module: Optional[str] = None
    remediation_script: Optional[str] = None
    auto_fix_available: bool = False
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None


@dataclass
class InfraSnapshot:
    """Infrastructure state snapshot"""

    timestamp: datetime
    terraform_state_hash: str
    resource_count: int
    resources: dict[str, Any]
    configuration_hash: str
    cost_estimate: Optional[float] = None


class TerraformDriftDetector:
    """Terraform-based drift detection"""

    def __init__(self, terraform_dir: str, state_backend: Optional[str] = None):
        self.terraform_dir = Path(terraform_dir)
        self.state_backend = state_backend

        if not self.terraform_dir.exists():
            raise ValueError("Terraform directory does not exist: {terraform_dir}")

    def check_drift(self) -> tuple[bool, list[dict[str, Any]]]:
        """Run terraform plan to check for drift"""
        try:
            # Change to terraform directory
            original_cwd = os.getcwd()
            os.chdir(self.terraform_dir)

            # Run terraform plan with detailed output
            cmd = [
                "terraform",
                "plan",
                "-detailed-exitcode",
                "-out=tfplan.out",
                "-json",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            os.chdir(original_cwd)

            # Parse terraform plan output
            has_drift = result.returncode == 2  # 2 means changes detected
            drift_details = []

            if has_drift and result.stdout:
                try:
                    plan_json = json.loads(result.stdout)
                    drift_details = self._parse_terraform_plan(plan_json)
                except json.JSONDecodeError as e:
                    logger.error("Failed to parse terraform plan JSON: {e}")

            return has_drift, drift_details

        except subprocess.TimeoutExpired:
            logger.error("Terraform plan timed out")
            return False, []
        except Exception as e:
            logger.error("Failed to check terraform drift: {e}")
            return False, []
        finally:
            os.chdir(original_cwd)

    def _parse_terraform_plan(self, plan_json: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse terraform plan JSON to extract drift details"""
        drift_details = []

        try:
            resource_changes = plan_json.get("resource_changes", [])

            for change in resource_changes:
                if change.get("change", {}).get("actions") not in [["no-op"], ["read"]]:
                    resource_type = change.get("type", "unknown")
                    resource_name = change.get("name", "unknown")
                    actions = change.get("change", {}).get("actions", [])

                    before = change.get("change", {}).get("before", {})
                    after = change.get("change", {}).get("after", {})

                    drift_detail = {
                        "resource_type": resource_type,
                        "resource_name": resource_name,
                        "actions": actions,
                        "before": before,
                        "after": after,
                        "drift_type": self._classify_drift_type(actions, before, after),
                        "severity": self._assess_drift_severity(resource_type, actions),
                    }

                    drift_details.append(drift_detail)

        except Exception as e:
            logger.error("Error parsing terraform plan: {e}")

        return drift_details

    def _classify_drift_type(
        self, actions: list[str], before: dict, after: dict
    ) -> DriftType:
        """Classify the type of drift based on changes"""
        if "create" in actions or "destroy" in actions:
            return DriftType.RESOURCE_COUNT
        elif "update" in actions:
            # Check if it's a security-related change
            security_fields = ["security_group", "iam_policy", "firewall", "acl"]
            if any(
                field in str(before) or field in str(after) for field in security_fields
            ):
                return DriftType.SECURITY
            return DriftType.CONFIGURATION
        else:
            return DriftType.RESOURCE_STATE

    def _assess_drift_severity(
        self, resource_type: str, actions: list[str]
    ) -> DriftSeverity:
        """Assess severity of drift based on resource type and actions"""
        critical_resources = [
            "google_compute_firewall",
            "google_project_iam_binding",
            "google_sql_database_instance",
        ]

        if resource_type in critical_resources:
            if "destroy" in actions:
                return DriftSeverity.CRITICAL
            elif "create" in actions or "update" in actions:
                return DriftSeverity.HIGH

        if "destroy" in actions:
            return DriftSeverity.HIGH
        elif "create" in actions:
            return DriftSeverity.MEDIUM
        elif "update" in actions:
            return DriftSeverity.MEDIUM

        return DriftSeverity.LOW


class CloudResourceMonitor:
    """Monitor cloud resources for drift outside of terraform"""

    def __init__(self, project_id: str):
        self.project_id = project_id

    def check_gcp_resource_drift(self) -> list[dict[str, Any]]:
        """Check for GCP resource drift using Cloud Asset Inventory"""
        drift_events = []

        try:
            # This would integrate with Google Cloud Asset Inventory
            # For now, implementing basic checks

            # Check for untagged resources
            untagged_resources = self._find_untagged_resources()
            for resource in untagged_resources:
                drift_events.append(
                    {
                        "resource_type": resource["type"],
                        "resource_name": resource["name"],
                        "drift_type": DriftType.CONFIGURATION,
                        "severity": DriftSeverity.MEDIUM,
                        "issue": "Missing required tags",
                        "expected": "Required tags present",
                        "actual": "Tags missing or incomplete",
                    }
                )

            # Check for cost anomalies
            cost_anomalies = self._detect_cost_anomalies()
            for anomaly in cost_anomalies:
                drift_events.append(
                    {
                        "resource_type": anomaly["service"],
                        "resource_name": anomaly["resource"],
                        "drift_type": DriftType.COST,
                        "severity": (
                            DriftSeverity.HIGH
                            if anomaly["increase"] > 50
                            else DriftSeverity.MEDIUM
                        ),
                        "issue": "Cost increase of {anomaly['increase']:.1f}%",
                        "expected": "${anomaly['expected']:.2f}",
                        "actual": f"${anomaly['actual']:.2f}",
                    }
                )

        except Exception as e:
            logger.error("Failed to check GCP resource drift: {e}")

        return drift_events

    def _find_untagged_resources(self) -> list[dict[str, str]]:
        """Find resources without required tags"""
        # Placeholder implementation
        # In production, this would use Cloud Asset Inventory API
        return []

    def _detect_cost_anomalies(self) -> list[dict[str, Any]]:
        """Detect cost anomalies that might indicate drift"""
        # Placeholder implementation
        # In production, this would use Cloud Billing API
        return []


class ConfigurationDriftDetector:
    """Detect drift in configuration files and settings"""

    def __init__(self, config_paths: list[str]):
        self.config_paths = [Path(p) for p in config_paths]
        self.baseline_hashes = {}

    def create_baseline(self):
        """Create baseline configuration hashes"""
        for config_path in self.config_paths:
            if config_path.exists():
                content_hash = self._hash_config_file(config_path)
                self.baseline_hashes[str(config_path)] = content_hash

    def check_config_drift(self) -> list[dict[str, Any]]:
        """Check for configuration file drift"""
        drift_events = []

        for config_path in self.config_paths:
            if not config_path.exists():
                drift_events.append(
                    {
                        "resource_type": "configuration_file",
                        "resource_name": str(config_path),
                        "drift_type": DriftType.CONFIGURATION,
                        "severity": DriftSeverity.HIGH,
                        "issue": "Configuration file missing",
                        "expected": "File exists",
                        "actual": "File not found",
                    }
                )
                continue

            current_hash = self._hash_config_file(config_path)
            baseline_hash = self.baseline_hashes.get(str(config_path))

            if baseline_hash and current_hash != baseline_hash:
                # Generate diff
                try:
                    with open(config_path) as f:
                        current_content = f.readlines()

                    # For this example, we'll assume we have the baseline content
                    # In production, you'd store this in a database or version control
                    diff = "Configuration changed (baseline comparison needed)"

                    drift_events.append(
                        {
                            "resource_type": "configuration_file",
                            "resource_name": str(config_path),
                            "drift_type": DriftType.CONFIGURATION,
                            "severity": DriftSeverity.MEDIUM,
                            "issue": "Configuration file modified",
                            "expected": "Hash: {baseline_hash}",
                            "actual": f"Hash: {current_hash}",
                            "dif": diff,
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to generate diff for {config_path}: {e}")

        return drift_events

    def _hash_config_file(self, config_path: Path) -> str:
        """Generate hash of configuration file"""
        try:
            with open(config_path, "rb") as f:
                content = f.read()
            return hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.error("Failed to hash config file {config_path}: {e}")
            return ""


class DriftDetectionManager:
    """Central manager for infrastructure drift detection"""

    def __init__(self, config_path: str = "configs/drift_detection_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.db_path = self.config.get("database", {}).get(
            "path", "data/drift_detection.db"
        )

        # Initialize detectors
        self.terraform_detector = None
        self.cloud_monitor = None
        self.config_detector = None

        self._init_detectors()
        self._init_database()

    def _load_config(self) -> dict[str, Any]:
        """Load drift detection configuration"""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load drift detection config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration"""
        return {
            "terraform": {
                "enabled": True,
                "directory": "infra",
                "check_interval_minutes": 60,
            },
            "cloud_resources": {
                "enabled": True,
                "project_id": "ai-trading-machine",
                "check_interval_minutes": 30,
            },
            "configuration": {
                "enabled": True,
                "paths": ["configs/", "src/ai_trading_machine/"],
                "check_interval_minutes": 15,
            },
            "alerting": {
                "enabled": True,
                "webhook_url": None,
                "email_recipients": [],
                "severity_threshold": "medium",
            },
            "database": {"path": "data/drift_detection.db", "retention_days": 90},
        }

    def _init_detectors(self):
        """Initialize drift detectors based on configuration"""
        try:
            # Terraform detector
            if self.config.get("terraform", {}).get("enabled"):
                terraform_dir = self.config["terraform"]["directory"]
                if os.path.exists(terraform_dir):
                    self.terraform_detector = TerraformDriftDetector(terraform_dir)
                else:
                    logger.warning("Terraform directory not found: {terraform_dir}")

            # Cloud resource monitor
            if self.config.get("cloud_resources", {}).get("enabled"):
                project_id = self.config["cloud_resources"]["project_id"]
                self.cloud_monitor = CloudResourceMonitor(project_id)

            # Configuration detector
            if self.config.get("configuration", {}).get("enabled"):
                config_paths = self.config["configuration"]["paths"]
                expanded_paths = []
                for path in config_paths:
                    if os.path.isdir(path):
                        # Add all config files in directory
                        for ext in [".json", ".yaml", ".yml", ".toml"]:
                            expanded_paths.extend(Path(path).rglob("*{ext}"))
                    else:
                        expanded_paths.append(path)

                self.config_detector = ConfigurationDriftDetector(
                    [str(p) for p in expanded_paths]
                )
                self.config_detector.create_baseline()

        except Exception as e:
            logger.error("Failed to initialize drift detectors: {e}")

    def _init_database(self):
        """Initialize SQLite database for drift tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Drift events table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS drift_events (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    drift_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_name TEXT NOT NULL,
                    expected_value TEXT NOT NULL,
                    actual_value TEXT NOT NULL,
                    diff TEXT,
                    terraform_module TEXT,
                    remediation_script TEXT,
                    auto_fix_available INTEGER DEFAULT 0,
                    resolved INTEGER DEFAULT 0,
                    resolution_timestamp TEXT
                )
            """
            )

            # Infrastructure snapshots table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS infra_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    terraform_state_hash TEXT,
                    resource_count INTEGER,
                    resources TEXT,
                    configuration_hash TEXT,
                    cost_estimate REAL
                )
            """
            )

            conn.commit()
            conn.close()
            logger.info("Drift detection database initialized")
        except Exception as e:
            logger.error("Failed to initialize drift detection database: {e}")

    def run_drift_detection(self) -> list[DriftEvent]:
        """Run comprehensive drift detection"""
        all_drift_events = []

        try:
            # Terraform drift detection
            if self.terraform_detector:
                logger.info("Running terraform drift detection...")
                has_terraform_drift, terraform_details = (
                    self.terraform_detector.check_drift()
                )

                if has_terraform_drift:
                    for detail in terraform_details:
                        drift_event = DriftEvent(
                            id=self._generate_drift_id(detail),
                            timestamp=datetime.now(),
                            drift_type=detail["drift_type"],
                            severity=detail["severity"],
                            resource_type=detail["resource_type"],
                            resource_name=detail["resource_name"],
                            expected_value=json.dumps(detail.get("before", {})),
                            actual_value=json.dumps(detail.get("after", {})),
                            diff=self._generate_diff(
                                detail.get("before"), detail.get("after")
                            ),
                            terraform_module="main",
                        )
                        all_drift_events.append(drift_event)

            # Cloud resource drift detection
            if self.cloud_monitor:
                logger.info("Running cloud resource drift detection...")
                cloud_drift_events = self.cloud_monitor.check_gcp_resource_drift()

                for event in cloud_drift_events:
                    drift_event = DriftEvent(
                        id=self._generate_drift_id(event),
                        timestamp=datetime.now(),
                        drift_type=event["drift_type"],
                        severity=event["severity"],
                        resource_type=event["resource_type"],
                        resource_name=event["resource_name"],
                        expected_value=event.get("expected", ""),
                        actual_value=event.get("actual", ""),
                        diff=event.get("issue", ""),
                    )
                    all_drift_events.append(drift_event)

            # Configuration drift detection
            if self.config_detector:
                logger.info("Running configuration drift detection...")
                config_drift_events = self.config_detector.check_config_drift()

                for event in config_drift_events:
                    drift_event = DriftEvent(
                        id=self._generate_drift_id(event),
                        timestamp=datetime.now(),
                        drift_type=event["drift_type"],
                        severity=event["severity"],
                        resource_type=event["resource_type"],
                        resource_name=event["resource_name"],
                        expected_value=event.get("expected", ""),
                        actual_value=event.get("actual", ""),
                        diff=event.get("di", ""),
                    )
                    all_drift_events.append(drift_event)

            # Store drift events
            self._store_drift_events(all_drift_events)

            # Send alerts for high-severity events
            high_severity_events = [
                event
                for event in all_drift_events
                if event.severity in [DriftSeverity.CRITICAL, DriftSeverity.HIGH]
            ]

            if high_severity_events:
                self._send_drift_alerts(high_severity_events)

            logger.info(
                "Drift detection completed. Found {len(all_drift_events)} drift events"
            )

        except Exception as e:
            logger.error("Failed to run drift detection: {e}")

        return all_drift_events

    def _generate_drift_id(self, event_data: dict[str, Any]) -> str:
        """Generate unique ID for drift event"""
        content = "{event_data.get('resource_type', '')}-{event_data.get('resource_name', '')}-{datetime.now().strftime('%Y%m%d')}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _generate_diff(self, before: Any, after: Any) -> str:
        """Generate diff between before and after states"""
        try:
            before_str = json.dumps(before, indent=2, sort_keys=True) if before else ""
            after_str = json.dumps(after, indent=2, sort_keys=True) if after else ""

            diff_lines = list(
                difflib.unified_diff(
                    before_str.splitlines(keepends=True),
                    after_str.splitlines(keepends=True),
                    fromfile="before",
                    tofile="after",
                )
            )

            return "".join(diff_lines)
        except Exception as e:
            logger.error("Failed to generate diff: {e}")
            return "Diff generation failed"

    def _store_drift_events(self, drift_events: list[DriftEvent]):
        """Store drift events in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for event in drift_events:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO drift_events
                    (id, timestamp, drift_type, severity, resource_type, resource_name,
                     expected_value, actual_value, diff, terraform_module,
                     remediation_script, auto_fix_available, resolved)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        event.id,
                        event.timestamp.isoformat(),
                        event.drift_type.value,
                        event.severity.value,
                        event.resource_type,
                        event.resource_name,
                        event.expected_value,
                        event.actual_value,
                        event.diff,
                        event.terraform_module,
                        event.remediation_script,
                        int(event.auto_fix_available),
                        int(event.resolved),
                    ),
                )

            conn.commit()
            conn.close()
            logger.info("Stored {len(drift_events)} drift events")
        except Exception as e:
            logger.error("Failed to store drift events: {e}")

    def _send_drift_alerts(self, drift_events: list[DriftEvent]):
        """Send alerts for drift events"""
        try:
            alerting_config = self.config.get("alerting", {})
            if not alerting_config.get("enabled"):
                return

            # Format alert message
            alert_message = self._format_drift_alert(drift_events)

            # Send webhook alert
            webhook_url = alerting_config.get("webhook_url")
            if webhook_url:
                self._send_webhook_alert(webhook_url, alert_message)

            # Send email alerts (if configured)
            email_recipients = alerting_config.get("email_recipients", [])
            if email_recipients:
                self._send_email_alerts(email_recipients, alert_message)

            logger.info("Sent alerts for {len(drift_events)} drift events")
        except Exception as e:
            logger.error("Failed to send drift alerts: {e}")

    def _format_drift_alert(self, drift_events: list[DriftEvent]) -> str:
        """Format drift events into alert message"""
        message_lines = [
            "🚨 Infrastructure Drift Detected",
            "Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "Events: {len(drift_events)}",
            "",
        ]

        for event in drift_events[:10]:  # Limit to first 10 events
            message_lines.extend(
                [
                    "• {event.severity.value.upper()}: {event.resource_type}/{event.resource_name}",
                    "  Type: {event.drift_type.value}",
                    "  Expected: {event.expected_value[:100]}{'...' if len(event.expected_value) > 100 else ''}",
                    "  Actual: {event.actual_value[:100]}{'...' if len(event.actual_value) > 100 else ''}",
                    "",
                ]
            )

        if len(drift_events) > 10:
            message_lines.append("... and {len(drift_events) - 10} more events")

        return "\n".join(message_lines)

    def _send_webhook_alert(self, webhook_url: str, message: str):
        """Send webhook alert"""
        try:
            import requests

            payload = {
                "text": message,
                "timestamp": datetime.now().isoformat(),
                "alert_type": "infrastructure_drift",
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Webhook alert sent successfully")
        except Exception as e:
            logger.error("Failed to send webhook alert: {e}")

    def _send_email_alerts(self, recipients: list[str], message: str):
        """Send email alerts"""
        # Placeholder for email alerting
        # In production, this would integrate with an email service
        logger.info("Would send email alerts to {recipients}")

    def get_drift_history(self, days: int = 7) -> list[DriftEvent]:
        """Get drift history for specified number of days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            start_date = datetime.now() - timedelta(days=days)

            cursor.execute(
                """
                SELECT * FROM drift_events
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """,
                (start_date.isoformat(),),
            )

            rows = cursor.fetchall()
            conn.close()

            drift_events = []
            for row in rows:
                event = DriftEvent(
                    id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    drift_type=DriftType(row[2]),
                    severity=DriftSeverity(row[3]),
                    resource_type=row[4],
                    resource_name=row[5],
                    expected_value=row[6],
                    actual_value=row[7],
                    diff=row[8],
                    terraform_module=row[9],
                    remediation_script=row[10],
                    auto_fix_available=bool(row[11]),
                    resolved=bool(row[12]),
                    resolution_timestamp=(
                        datetime.fromisoformat(row[13]) if row[13] else None
                    ),
                )
                drift_events.append(event)

            return drift_events
        except Exception as e:
            logger.error("Failed to get drift history: {e}")
            return []


if __name__ == "__main__":
    # Example usage
    drift_manager = DriftDetectionManager()
    drift_events = drift_manager.run_drift_detection()

    print("Found {len(drift_events)} drift events:")
    for event in drift_events[:5]:  # Show first 5
        print("- {event.severity.value}: {event.resource_type}/{event.resource_name}")
        print("  {event.drift_type.value}: {event.diff[:100]}...")
        print()
