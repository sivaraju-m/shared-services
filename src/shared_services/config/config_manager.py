"""
Configuration Manager for Shared Services
=========================================

This module provides centralized configuration management across all 
trading system components with support for YAML, JSON, and environment variables.
"""

import json
import os
import yaml
from typing import Any, Dict, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Centralized configuration management for trading system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path
        self.config_data = {}
        self.default_configs = self._get_default_configs()
        
        if config_path and os.path.exists(config_path):
            self._load_config_file(config_path)
        else:
            logger.info("Using default configuration settings")
            self.config_data = self.default_configs.copy()
    
    def _get_default_configs(self) -> Dict[str, Any]:
        """Get default configuration settings."""
        return {
            'daily_runner': {
                'watchlist': [
                    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR",
                    "ICICIBANK", "KOTAKBANK", "BHARTIARTL", "ITC", "SBIN"
                ],
                'strategies': ['rsi', 'momentum', 'sma'],
                'execution_interval_minutes': 5,
                'max_concurrent_executions': 10
            },
            'strategies': {
                'rsi': {
                    'period': 14,
                    'oversold': 30,
                    'overbought': 70,
                    'enabled': True
                },
                'momentum': {
                    'window': 20,
                    'threshold': 0.02,
                    'enabled': True
                },
                'sma': {
                    'fast_period': 10,
                    'slow_period': 30,
                    'enabled': True
                }
            },
            'market_hours': {
                'start_time': '09:15',
                'end_time': '15:30',
                'timezone': 'Asia/Kolkata'
            },
            'logging': {
                'level': 'INFO',
                'enable_file_logging': True,
                'log_rotation': True
            }
        }
    
    def _load_config_file(self, config_path: str) -> None:
        """Load configuration from file."""
        try:
            with open(config_path, 'r') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    file_config = yaml.safe_load(f)
                elif config_path.endswith('.json'):
                    file_config = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {config_path}")
            
            # Merge with defaults
            self.config_data = self._merge_configs(self.default_configs, file_config)
            logger.info(f"Configuration loaded from: {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            logger.info("Using default configuration")
            self.config_data = self.default_configs.copy()
    
    def _merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge override config with default config."""
        merged = default.copy()
        
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def get_config(self, section: str, default: Any = None) -> Any:
        """
        Get configuration for a specific section.
        
        Args:
            section: Configuration section name
            default: Default value if section not found
            
        Returns:
            Configuration value or default
        """
        return self.config_data.get(section, default)
    
    def get_strategy_config(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Strategy configuration or None
        """
        strategies_config = self.get_config('strategies', {})
        return strategies_config.get(strategy_name)
    
    def get_watchlist(self) -> list:
        """Get the trading watchlist."""
        daily_config = self.get_config('daily_runner', {})
        return daily_config.get('watchlist', [])
    
    def get_enabled_strategies(self) -> list:
        """Get list of enabled strategies."""
        strategies_config = self.get_config('strategies', {})
        enabled_strategies = []
        
        for strategy_name, config in strategies_config.items():
            if config.get('enabled', True):  # Default to enabled
                enabled_strategies.append(strategy_name)
        
        return enabled_strategies
    
    def update_config(self, section: str, config: Dict[str, Any]) -> None:
        """
        Update configuration for a section.
        
        Args:
            section: Configuration section name
            config: New configuration data
        """
        self.config_data[section] = config
        logger.info(f"Configuration updated for section: {section}")
    
    def save_config(self, output_path: str) -> bool:
        """
        Save current configuration to file.
        
        Args:
            output_path: Path to save configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w') as f:
                if output_path.endswith('.yaml') or output_path.endswith('.yml'):
                    yaml.dump(self.config_data, f, default_flow_style=False, indent=2)
                elif output_path.endswith('.json'):
                    json.dump(self.config_data, f, indent=2)
                else:
                    raise ValueError(f"Unsupported output format: {output_path}")
            
            logger.info(f"Configuration saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get the complete configuration."""
        return self.config_data.copy()
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the current configuration.
        
        Returns:
            Validation result with status and any issues
        """
        issues = []
        
        # Validate required sections
        required_sections = ['daily_runner', 'strategies', 'market_hours']
        for section in required_sections:
            if section not in self.config_data:
                issues.append(f"Missing required section: {section}")
        
        # Validate watchlist
        watchlist = self.get_watchlist()
        if not watchlist or len(watchlist) == 0:
            issues.append("Watchlist is empty")
        
        # Validate strategies
        enabled_strategies = self.get_enabled_strategies()
        if not enabled_strategies:
            issues.append("No strategies are enabled")
        
        # Validate market hours
        market_config = self.get_config('market_hours', {})
        if 'start_time' not in market_config or 'end_time' not in market_config:
            issues.append("Market hours configuration incomplete")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'sections_count': len(self.config_data),
            'strategies_count': len(self.get_enabled_strategies()),
            'watchlist_size': len(self.get_watchlist())
        }
