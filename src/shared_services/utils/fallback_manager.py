#!/usr/bin/env python3
"""
Fallback Mechanisms Documentation and Monitoring System
======================================================

Documents, monitors, and manages all fallback mechanisms across the AI Trading Machine.
Ensures data integrity and provides recovery procedures for when primary systems fail.

Author: AI Trading Machine
Licensed by SJ Trading
"""

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.ai_trading_machine.utils.logger import setup_logger

logger = setup_logger(__name__)


class FallbackType(Enum):
    """Types of fallback mechanisms"""

    DATA_SOURCE = "data_source"
    CLOUD_STORAGE = "cloud_storage"
    CONFIGURATION = "configuration"
    MODEL_REGISTRY = "model_registry"
    SIGNAL_GENERATION = "signal_generation"
    LOGGING = "logging"


class FallbackSeverity(Enum):
    """Severity levels for fallback activation"""

    LOW = "low"  # Minor degradation, full functionality
    MEDIUM = "medium"  # Some features affected
    HIGH = "high"  # Significant functionality lost
    CRITICAL = "critical"  # Core functionality compromised


@dataclass
class FallbackMechanism:
    """Represents a fallback mechanism"""

    name: str
    component: str
    fallback_type: FallbackType
    severity: FallbackSeverity
    trigger_conditions: list[str]
    fallback_action: str
    recovery_procedure: str
    monitoring_enabled: bool
    file_locations: list[str]
    dependencies: list[str]
    last_activated: Optional[str] = None
    activation_count: int = 0


class FallbackManager:
    """
    Manages and monitors all fallback mechanisms
    """

    def __init__(self):
        """Initialize fallback manager"""
        self.mechanisms: dict[str, FallbackMechanism] = {}
        self.activation_log: list[dict[str, Any]] = []

        # Create monitoring directory
        self.monitoring_dir = "logs/fallback_monitoring"
        os.makedirs(self.monitoring_dir, exist_ok=True)

        # Initialize known fallback mechanisms
        self._register_known_fallbacks()

        logger.info("Fallback manager initialized with monitoring")

    def _register_known_fallbacks(self) -> None:
        """Register all known fallback mechanisms in the system"""

        # Cloud Storage Fallbacks
        self.register_fallback(
            FallbackMechanism(
                name="firestore_to_local_backup",
                component="signal_logger",
                fallback_type=FallbackType.CLOUD_STORAGE,
                severity=FallbackSeverity.MEDIUM,
                trigger_conditions=[
                    "Firestore credentials unavailable",
                    "Network connectivity issues",
                    "Firestore API quota exceeded",
                ],
                fallback_action="Save signals to local JSON files in logs/signal_backups/",
                recovery_procedure="Upload backed up signals when Firestore is available",
                monitoring_enabled=True,
                file_locations=["src/ai_trading_machine/persist/signal_logger.py"],
                dependencies=["google-cloud-firestore"],
            )
        )

        self.register_fallback(
            FallbackMechanism(
                name="bigquery_to_local_backup",
                component="signal_logger",
                fallback_type=FallbackType.CLOUD_STORAGE,
                severity=FallbackSeverity.MEDIUM,
                trigger_conditions=[
                    "BigQuery credentials unavailable",
                    "BigQuery API quota exceeded",
                    "Network connectivity issues",
                ],
                fallback_action="Save trade data to local CSV files in logs/bigquery_backups/",
                recovery_procedure="Upload CSV data to BigQuery when available",
                monitoring_enabled=True,
                file_locations=["src/ai_trading_machine/persist/signal_logger.py"],
                dependencies=["google-cloud-bigquery"],
            )
        )

        # Signal Generation Fallbacks
        self.register_fallback(
            FallbackMechanism(
                name="strategy_file_missing_fallback",
                component="signal_fusion_engine",
                fallback_type=FallbackType.SIGNAL_GENERATION,
                severity=FallbackSeverity.HIGH,
                trigger_conditions=[
                    "Strategy signal file not found",
                    "Invalid JSON in strategy file",
                ],
                fallback_action="Generate default strategy signal with neutral action",
                recovery_procedure="Check strategy signal generation pipeline",
                monitoring_enabled=True,
                file_locations=["flow/generate_final_signal.py"],
                dependencies=["strategy_signals"],
            )
        )

        self.register_fallback(
            FallbackMechanism(
                name="ml_prediction_missing_fallback",
                component="signal_fusion_engine",
                fallback_type=FallbackType.SIGNAL_GENERATION,
                severity=FallbackSeverity.HIGH,
                trigger_conditions=[
                    "ML prediction file not found",
                    "Invalid ML prediction format",
                ],
                fallback_action="Generate default ML prediction with confidence 0.5",
                recovery_procedure="Check ML prediction pipeline and model training",
                monitoring_enabled=True,
                file_locations=["flow/generate_final_signal.py"],
                dependencies=["ml_predictions"],
            )
        )

        self.register_fallback(
            FallbackMechanism(
                name="nlp_sentiment_missing_fallback",
                component="signal_fusion_engine",
                fallback_type=FallbackType.SIGNAL_GENERATION,
                severity=FallbackSeverity.MEDIUM,
                trigger_conditions=[
                    "NLP sentiment file not found",
                    "News sentiment analysis failed",
                ],
                fallback_action="Use neutral sentiment (0.5) for signal fusion",
                recovery_procedure="Check news ingestion and sentiment analysis pipeline",
                monitoring_enabled=True,
                file_locations=["flow/generate_final_signal.py"],
                dependencies=["nlp_sentiment"],
            )
        )

        # Model Registry Fallbacks
        self.register_fallback(
            FallbackMechanism(
                name="vertex_ai_to_local_registry",
                component="model_registry",
                fallback_type=FallbackType.MODEL_REGISTRY,
                severity=FallbackSeverity.LOW,
                trigger_conditions=["Vertex AI unavailable", "GCP credentials issues"],
                fallback_action="Use local file-based model registry",
                recovery_procedure="Sync local models to Vertex AI when available",
                monitoring_enabled=True,
                file_locations=["src/ai_trading_machine/ml/model_registry/__init__.py"],
                dependencies=["google-cloud-aiplatform"],
            )
        )

        # Data Source Fallbacks
        self.register_fallback(
            FallbackMechanism(
                name="kiteconnect_to_yahoo_finance",
                component="data_feeds",
                fallback_type=FallbackType.DATA_SOURCE,
                severity=FallbackSeverity.MEDIUM,
                trigger_conditions=[
                    "KiteConnect API unavailable",
                    "Rate limit exceeded",
                    "Authentication failure",
                ],
                fallback_action="Switch to Yahoo Finance for market data",
                recovery_procedure="Check KiteConnect credentials and connectivity",
                monitoring_enabled=True,
                file_locations=["src/ai_trading_machine/feeds/realtime_data_feed.py"],
                dependencies=["kiteconnect", "yfinance"],
            )
        )

        # Configuration Fallbacks
        self.register_fallback(
            FallbackMechanism(
                name="config_file_missing_fallback",
                component="configuration_manager",
                fallback_type=FallbackType.CONFIGURATION,
                severity=FallbackSeverity.HIGH,
                trigger_conditions=[
                    "Configuration file not found",
                    "Invalid YAML/JSON config",
                ],
                fallback_action="Use hardcoded default configuration values",
                recovery_procedure="Restore configuration files from backup",
                monitoring_enabled=True,
                file_locations=["configs/trading_config.yaml", "configs/nifty50.json"],
                dependencies=["config_files"],
            )
        )

        logger.info("Registered {len(self.mechanisms)} fallback mechanisms")

    def register_fallback(self, mechanism: FallbackMechanism) -> None:
        """Register a fallback mechanism"""
        self.mechanisms[mechanism.name] = mechanism

    def activate_fallback(
        self,
        fallback_name: str,
        trigger_reason: str,
        context: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Activate a specific fallback mechanism"""

        if fallback_name not in self.mechanisms:
            logger.error("Unknown fallback mechanism: {fallback_name}")
            return False

        mechanism = self.mechanisms[fallback_name]
        activation_time = datetime.now().isoformat()

        # Log activation
        activation_record = {
            "timestamp": activation_time,
            "fallback_name": fallback_name,
            "component": mechanism.component,
            "trigger_reason": trigger_reason,
            "severity": mechanism.severity.value,
            "context": context or {},
        }

        self.activation_log.append(activation_record)

        # Update mechanism
        mechanism.last_activated = activation_time
        mechanism.activation_count += 1

        # Log to file
        self._log_activation(activation_record)

        # Send alert based on severity
        if mechanism.severity in [FallbackSeverity.HIGH, FallbackSeverity.CRITICAL]:
            self._send_fallback_alert(mechanism, trigger_reason)

        logger.warning("Fallback activated: {fallback_name} - {trigger_reason}")

        return True

    def _log_activation(self, activation_record: dict[str, Any]) -> None:
        """Log fallback activation to file"""

        try:
            log_file = "{self.monitoring_dir}/fallback_activations.json"

            # Load existing logs
            activations = []
            if os.path.exists(log_file):
                with open(log_file) as f:
                    activations = json.load(f)

            # Add new activation
            activations.append(activation_record)

            # Keep only last 1000 activations
            if len(activations) > 1000:
                activations = activations[-1000:]

            # Save updated logs
            with open(log_file, "w") as f:
                json.dump(activations, f, indent=2)

        except Exception as e:
            logger.error("Failed to log fallback activation: {e}")

    def _send_fallback_alert(
        self, mechanism: FallbackMechanism, trigger_reason: str
    ) -> None:
        """Send alert for high-severity fallback activation"""

        try:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "alert_type": "FALLBACK_ACTIVATION",
                "severity": mechanism.severity.value,
                "mechanism_name": mechanism.name,
                "component": mechanism.component,
                "trigger_reason": trigger_reason,
                "recovery_procedure": mechanism.recovery_procedure,
                "requires_attention": mechanism.severity == FallbackSeverity.CRITICAL,
            }

            alert_file = "{self.monitoring_dir}/fallback_alerts_{datetime.now().strftime('%Y%m%d')}.json"

            # Append to daily alert file
            alerts = []
            if os.path.exists(alert_file):
                with open(alert_file) as f:
                    alerts = json.load(f)

            alerts.append(alert)

            with open(alert_file, "w") as f:
                json.dump(alerts, f, indent=2)

            if mechanism.severity == FallbackSeverity.CRITICAL:
                logger.critical(
                    "CRITICAL FALLBACK ALERT: {mechanism.name} - {trigger_reason}"
                )

        except Exception as e:
            logger.error("Failed to send fallback alert: {e}")

    def get_fallback_status(self) -> dict[str, Any]:
        """Get current status of all fallback mechanisms"""

        status = {
            "total_mechanisms": len(self.mechanisms),
            "monitoring_enabled": len(
                [m for m in self.mechanisms.values() if m.monitoring_enabled]
            ),
            "recently_activated": [],
            "never_activated": [],
            "high_frequency_activations": [],
            "by_severity": {"critical": [], "high": [], "medium": [], "low": []},
        }

        # Analyze mechanisms
        for name, mechanism in self.mechanisms.items():
            # Group by severity
            status["by_severity"][mechanism.severity.value].append(name)

            # Check activation history
            if mechanism.last_activated is None:
                status["never_activated"].append(name)
            else:
                last_activated = datetime.fromisoformat(mechanism.last_activated)

                # Recently activated (last 24 hours)
                if datetime.now() - last_activated < timedelta(hours=24):
                    status["recently_activated"].append(
                        {
                            "name": name,
                            "last_activated": mechanism.last_activated,
                            "activation_count": mechanism.activation_count,
                        }
                    )

                # High frequency (more than 10 activations)
                if mechanism.activation_count > 10:
                    status["high_frequency_activations"].append(
                        {
                            "name": name,
                            "activation_count": mechanism.activation_count,
                            "component": mechanism.component,
                        }
                    )

        return status

    def generate_fallback_documentation(self) -> str:
        """Generate comprehensive fallback documentation"""

        doc_content = """# AI Trading Machine - Fallback Mechanisms Documentation

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This document describes all fallback mechanisms implemented in the AI Trading Machine to ensure system reliability and data integrity when primary systems fail.

## Registered Fallback Mechanisms ({len(self.mechanisms)})

"""

        # Group by type
        by_type = {}
        for mechanism in self.mechanisms.values():
            fallback_type = mechanism.fallback_type.value
            if fallback_type not in by_type:
                by_type[fallback_type] = []
            by_type[fallback_type].append(mechanism)

        for fallback_type, mechanisms in by_type.items():
            doc_content += (
                "\n### {fallback_type.replace('_', ' ').title()} Fallbacks\n\n"
            )

            for mechanism in mechanisms:
                doc_content += "#### {mechanism.name}\n\n"
                doc_content += "- **Component**: {mechanism.component}\n"
                doc_content += "- **Severity**: {mechanism.severity.value.upper()}\n"
                doc_content += "- **Monitoring**: {'Enabled' if mechanism.monitoring_enabled else 'Disabled'}\n"
                doc_content += "- **Activation Count**: {mechanism.activation_count}\n"

                if mechanism.last_activated:
                    doc_content += "- **Last Activated**: {mechanism.last_activated}\n"

                doc_content += "\n**Trigger Conditions**:\n"
                for condition in mechanism.trigger_conditions:
                    doc_content += "- {condition}\n"

                doc_content += "\n**Fallback Action**: {mechanism.fallback_action}\n\n"
                doc_content += (
                    "**Recovery Procedure**: {mechanism.recovery_procedure}\n\n"
                )

                if mechanism.file_locations:
                    doc_content += "**Implementation Files**:\n"
                    for file_path in mechanism.file_locations:
                        doc_content += "- `{file_path}`\n"

                if mechanism.dependencies:
                    doc_content += (
                        "\n**Dependencies**: {', '.join(mechanism.dependencies)}\n"
                    )

                doc_content += "\n---\n\n"

        # Add monitoring information
        doc_content += """## Monitoring and Alerts

### Monitoring Locations
- **Activation Logs**: `logs/fallback_monitoring/fallback_activations.json`
- **Daily Alerts**: `logs/fallback_monitoring/fallback_alerts_YYYYMMDD.json`

### Alert Severities
- **LOW**: Minor degradation, full functionality maintained
- **MEDIUM**: Some features affected, manual review recommended
- **HIGH**: Significant functionality lost, immediate attention required
- **CRITICAL**: Core functionality compromised, urgent intervention needed

### Recovery Procedures

1. **Check System Health**: Review recent logs and alert files
2. **Identify Root Cause**: Examine trigger conditions and error messages
3. **Restore Primary Systems**: Follow component-specific recovery procedures
4. **Verify Data Integrity**: Ensure no data loss during fallback period
5. **Update Monitoring**: Review and improve fallback mechanisms if needed

## Best Practices

1. **Regular Testing**: Test fallback mechanisms monthly
2. **Data Backup**: Ensure all fallback data is backed up and recoverable
3. **Alert Response**: Respond to high-severity fallback alerts within 1 hour
4. **Documentation**: Keep fallback procedures updated with system changes
5. **Monitoring Review**: Weekly review of fallback activation patterns

---

*This documentation is automatically generated and updated by the Fallback Manager.*
"""

        return doc_content

    def create_fallback_tests(self) -> str:
        """Create automated tests for fallback mechanisms"""

        test_content = '''#!/usr/bin/env python3
"""
Automated Fallback Mechanism Tests
=================================

Tests all registered fallback mechanisms to ensure they work correctly.
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

from src.ai_trading_machine.utils.fallback_manager import FallbackManager


class TestFallbackMechanisms(unittest.TestCase):
    """Test all fallback mechanisms"""

    def setUp(self):
        """Set up test environment"""
        self.fallback_manager = FallbackManager()

    def test_fallback_registration(self):
        """Test that all fallbacks are properly registered"""
        self.assertGreater(len(self.fallback_manager.mechanisms), 0)

        # Check required fallbacks exist
        required_fallbacks = [
            'firestore_to_local_backup',
            'bigquery_to_local_backup',
            'strategy_file_missing_fallback',
            'ml_prediction_missing_fallback'
        ]

        for fallback_name in required_fallbacks:
            self.assertIn(fallback_name, self.fallback_manager.mechanisms)

'''

        # Generate test for each mechanism
        for name, mechanism in self.mechanisms.items():
            test_name = name.replace("-", "_")
            test_content += '''
    def test_{test_name}_activation(self):
        """Test {name} fallback activation"""
        # Test activation
        result = self.fallback_manager.activate_fallback(
            '{name}',
            'Test activation'
        )
        self.assertTrue(result)

        # Check activation was logged
        self.assertEqual(
            self.fallback_manager.mechanisms['{name}'].activation_count,
            1
        )
'''

        test_content += '''
    def test_fallback_status_report(self):
        """Test fallback status reporting"""
        status = self.fallback_manager.get_fallback_status()

        self.assertIn('total_mechanisms', status)
        self.assertIn('by_severity', status)
        self.assertGreater(status['total_mechanisms'], 0)

    def test_fallback_documentation_generation(self):
        """Test documentation generation"""
        doc = self.fallback_manager.generate_fallback_documentation()

        self.assertIn('Fallback Mechanisms Documentation', doc)
        self.assertIn('Recovery Procedures', doc)


if __name__ == '__main__':
    unittest.main()
'''

        return test_content


def setup_fallback_monitoring():
    """Set up comprehensive fallback monitoring system"""

    print("🔄 Setting Up Fallback Mechanisms Monitoring")
    print("=" * 60)

    # Initialize fallback manager
    manager = FallbackManager()

    print("✅ Fallback manager initialized")
    print("   Registered mechanisms: {len(manager.mechanisms)}")

    # Generate documentation
    doc_content = manager.generate_fallback_documentation()
    doc_file = "docs/fallback_mechanisms.md"
    os.makedirs(os.path.dirname(doc_file), exist_ok=True)

    with open(doc_file, "w") as f:
        f.write(doc_content)

    print("📄 Documentation generated: {doc_file}")

    # Generate tests
    test_content = manager.create_fallback_tests()
    test_file = "tests/test_fallback_mechanisms.py"
    os.makedirs(os.path.dirname(test_file), exist_ok=True)

    with open(test_file, "w") as f:
        f.write(test_content)

    print("🧪 Tests generated: {test_file}")

    # Get status report
    status = manager.get_fallback_status()

    print("\n📊 Fallback Status:")
    print("   Total mechanisms: {status['total_mechanisms']}")
    print("   Monitoring enabled: {status['monitoring_enabled']}")
    print("   Never activated: {len(status['never_activated'])}")

    print("\n🔢 By Severity:")
    for severity, mechanisms in status["by_severity"].items():
        if mechanisms:
            print("   {severity.upper()}: {len(mechanisms)} mechanisms")

    # Save status report
    status_file = "logs/fallback_monitoring/status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)

    print("\n📈 Status report saved: {status_file}")

    print("\n✨ Fallback monitoring setup complete!")
    print("   Monitoring directory: logs/fallback_monitoring/")
    print("   Documentation: docs/fallback_mechanisms.md")
    print("   Tests: tests/test_fallback_mechanisms.py")

    return manager


if __name__ == "__main__":
    setup_fallback_monitoring()
