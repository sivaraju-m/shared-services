"""
Shared Services - Utilities Module

This module provides common utilities used across the AI Trading Machine ecosystem.
"""

# Export key utility modules
from shared_services.utils.logger import setup_logger, get_logger
from shared_services.utils.error_handling import handle_error, retry_on_error
from shared_services.utils.config_parser import parse_config, load_config
from shared_services.utils.gcp_secrets import get_secret, set_secret
from shared_services.utils.data_cleaner import clean_data
from shared_services.utils.verification import verify_data_integrity
from shared_services.utils.market_data_validator import validate_market_data
from shared_services.utils.sector_mapper import map_ticker_to_sector
from shared_services.utils.gcs_utils import upload_to_gcs, download_from_gcs
from shared_services.utils.fallback_manager import FallbackManager
from shared_services.utils.bq_logger import log_to_bigquery
from shared_services.utils.enhanced_logging import EnhancedLogger
from shared_services.utils.cost_monitor import monitor_costs
from shared_services.utils.error_handling_audit import audit_errors

# Define exported symbols
__all__ = [
    'setup_logger', 'get_logger',
    'handle_error', 'retry_on_error',
    'parse_config', 'load_config',
    'get_secret', 'set_secret',
    'clean_data',
    'verify_data_integrity',
    'validate_market_data',
    'map_ticker_to_sector',
    'upload_to_gcs', 'download_from_gcs',
    'FallbackManager',
    'log_to_bigquery',
    'EnhancedLogger',
    'monitor_costs',
    'audit_errors'
]