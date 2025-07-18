"""
Sector Mapping Utility for AI Trading Machine

This module provides sector classification and exposure management functionality
for stock symbols in the trading system.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class SectorInfo:
    """Information about a stock's sector classification"""

    sector_code: str
    sector_name: str
    subsector: str
    gics_equivalent: str
    risk_level: str
    correlation_group: str
    max_allocation_pct: float


@dataclass
class SectorExposure:
    """Current sector exposure information"""

    sector_code: str
    sector_name: str
    current_exposure_pct: float
    max_allowed_pct: float
    position_count: int
    total_value: float


class SectorMapper:
    """
    Utility class for managing stock-to-sector mapping and exposure validation
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize sector mapper with configuration

        Args:
            config_path: Path to sector mapping JSON file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.sector_mapping: dict[str, SectorInfo] = {}
        self.sector_definitions: dict[str, dict[str, Any]] = {}
        self.metadata: dict[str, Any] = {}

        self._load_sector_mapping()

    def _get_default_config_path(self) -> str:
        """Get default path to sector mapping configuration"""
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent
        config_path = (
            project_root / "configs" / "sectors" / "comprehensive_sector_mapping.json"
        )
        return str(config_path)

    def _load_sector_mapping(self) -> None:
        """Load sector mapping from JSON configuration file"""
        try:
            with open(self.config_path) as f:
                config = json.load(f)

            self.metadata = config.get("metadata", {})
            self.sector_definitions = config.get("sector_definitions", {})

            # Load stock mappings - support both formats
            stock_mappings = config.get("stock_mappings", {})
            simple_mappings = config.get("stock_to_sector_mapping", {})

            # Process detailed mappings first
            for symbol, mapping_data in stock_mappings.items():
                sector_code = mapping_data.get("sector")
                if sector_code and sector_code in self.sector_definitions:
                    sector_def = self.sector_definitions[sector_code]

                    self.sector_mapping[symbol] = SectorInfo(
                        sector_code=sector_code,
                        sector_name=sector_def.get("name", ""),
                        subsector=mapping_data.get("subsector", ""),
                        gics_equivalent=sector_def.get("gics_equivalent", ""),
                        risk_level=sector_def.get("risk_level", "Medium"),
                        correlation_group=sector_def.get("correlation_group", ""),
                        max_allocation_pct=sector_def.get("max_allocation_pct", 20.0),
                    )

            # Process simple mappings (symbol -> sector_code)
            for symbol, sector_code in simple_mappings.items():
                if sector_code and sector_code in self.sector_definitions:
                    sector_def = self.sector_definitions[sector_code]

                    self.sector_mapping[symbol] = SectorInfo(
                        sector_code=sector_code,
                        sector_name=sector_def.get("name", ""),
                        subsector="",  # Not available in simple format
                        gics_equivalent=sector_def.get("gics_equivalent", ""),
                        risk_level=sector_def.get("risk_level", "Medium"),
                        correlation_group=sector_def.get("correlation_group", ""),
                        max_allocation_pct=sector_def.get("max_allocation_pct", 20.0),
                    )

            logger.info(
                "✅ Loaded sector mapping for {len(self.sector_mapping)} symbols"
            )
            logger.info("📊 Available sectors: {list(self.sector_definitions.keys())}")

        except FileNotFoundError:
            logger.error("❌ Sector mapping file not found: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error("❌ Invalid JSON in sector mapping file: {e}")
            raise
        except Exception as e:
            logger.error("❌ Error loading sector mapping: {e}")
            raise

    def get_sector_info(self, symbol: str) -> Optional[SectorInfo]:
        """
        Get sector information for a given stock symbol

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')

        Returns:
            SectorInfo object or None if symbol not found
        """
        # Try exact match first
        symbol_upper = symbol.upper()
        if symbol_upper in self.sector_mapping:
            return self.sector_mapping[symbol_upper]

        # Try with .NS suffix removed (for Yahoo Finance symbols)
        if symbol_upper.endswith(".NS"):
            clean_symbol = symbol_upper[:-3]
            if clean_symbol in self.sector_mapping:
                return self.sector_mapping[clean_symbol]
        else:
            # Try adding .NS suffix if not present
            symbol_with_ns = symbol_upper + ".NS"
            if symbol_with_ns in self.sector_mapping:
                return self.sector_mapping[symbol_with_ns]

        logger.warning("⚠️ Sector mapping not found for symbol: {symbol}")
        return None

    def get_sector_code(self, symbol: str) -> Optional[str]:
        """Get sector code for a symbol"""
        sector_info = self.get_sector_info(symbol)
        return sector_info.sector_code if sector_info else None

    def get_max_sector_allocation(self, sector_code: str) -> float:
        """Get maximum allowed allocation percentage for a sector"""
        if sector_code in self.sector_definitions:
            return self.sector_definitions[sector_code].get("max_allocation_pct", 20.0)
        return 20.0  # Default limit

    def calculate_portfolio_sector_exposure(
        self, positions: dict[str, dict[str, Any]], portfolio_value: float
    ) -> dict[str, SectorExposure]:
        """
        Calculate current sector exposure across portfolio positions

        Args:
            positions: Dict of {symbol: {'value': float, 'shares': int, ...}}
            portfolio_value: Total portfolio value

        Returns:
            Dict of {sector_code: SectorExposure}
        """
        sector_exposures: dict[str, SectorExposure] = {}

        # Initialize sector exposures
        for sector_code, sector_def in self.sector_definitions.items():
            sector_exposures[sector_code] = SectorExposure(
                sector_code=sector_code,
                sector_name=sector_def["name"],
                current_exposure_pct=0.0,
                max_allowed_pct=sector_def.get("max_allocation_pct", 20.0),
                position_count=0,
                total_value=0.0,
            )

        # Calculate exposures from current positions
        for symbol, position_data in positions.items():
            sector_info = self.get_sector_info(symbol)
            if sector_info:
                position_value = position_data.get("value", 0.0)

                exposure = sector_exposures[sector_info.sector_code]
                exposure.total_value += position_value
                exposure.position_count += 1

                if portfolio_value > 0:
                    exposure.current_exposure_pct = (
                        exposure.total_value / portfolio_value
                    ) * 100

        return sector_exposures

    def validate_sector_exposure(
        self,
        symbol: str,
        new_position_value: float,
        current_positions: dict[str, dict[str, Any]],
        portfolio_value: float,
    ) -> tuple[bool, str]:
        """
        Validate if adding a new position would exceed sector exposure limits

        Args:
            symbol: Stock symbol for new position
            new_position_value: Value of new position
            current_positions: Current portfolio positions
            portfolio_value: Total portfolio value

        Returns:
            Tuple of (is_valid, reason)
        """
        sector_info = self.get_sector_info(symbol)
        if not sector_info:
            # If we don't have sector info, allow but warn
            return True, "No sector mapping found for {symbol} - allowing position"

        # Calculate current sector exposures
        sector_exposures = self.calculate_portfolio_sector_exposure(
            current_positions, portfolio_value
        )

        # Check impact of new position
        sector_code = sector_info.sector_code
        current_exposure = sector_exposures.get(sector_code)

        if current_exposure:
            new_total_value = current_exposure.total_value + new_position_value
            new_exposure_pct = (
                (new_total_value / portfolio_value) * 100 if portfolio_value > 0 else 0
            )

            max_allowed = current_exposure.max_allowed_pct

            if new_exposure_pct > max_allowed:
                return False, (
                    "Sector {sector_info.sector_name} exposure would be {new_exposure_pct:.1f}% "
                    "(limit: {max_allowed:.1f}%)"
                )

            logger.info(
                "✅ Sector validation passed for {symbol} in {sector_info.sector_name}: "
                "{new_exposure_pct:.1f}%/{max_allowed:.1f}%"
            )

        return True, "Sector exposure within limits"

    def get_sector_recommendations(
        self, current_positions: dict[str, dict[str, Any]], portfolio_value: float
    ) -> list[dict[str, Any]]:
        """
        Get sector allocation recommendations based on current portfolio

        Returns:
            List of sector recommendations with suggested actions
        """
        sector_exposures = self.calculate_portfolio_sector_exposure(
            current_positions, portfolio_value
        )

        recommendations = []

        for sector_code, exposure in sector_exposures.items():
            if (
                exposure.current_exposure_pct > exposure.max_allowed_pct * 0.9
            ):  # Near limit
                recommendations.append(
                    {
                        "sector": exposure.sector_name,
                        "action": "REDUCE",
                        "current_pct": exposure.current_exposure_pct,
                        "max_pct": exposure.max_allowed_pct,
                        "severity": (
                            "HIGH"
                            if exposure.current_exposure_pct > exposure.max_allowed_pct
                            else "MEDIUM"
                        ),
                    }
                )
            elif (
                exposure.current_exposure_pct < 5.0 and exposure.max_allowed_pct > 10.0
            ):  # Underweight
                recommendations.append(
                    {
                        "sector": exposure.sector_name,
                        "action": "INCREASE",
                        "current_pct": exposure.current_exposure_pct,
                        "max_pct": exposure.max_allowed_pct,
                        "severity": "LOW",
                    }
                )

        return recommendations

    def get_available_sectors(self) -> list[str]:
        """Get list of all available sector codes"""
        return list(self.sector_definitions.keys())

    def get_stocks_in_sector(self, sector_code: str) -> list[str]:
        """Get list of all stocks in a given sector"""
        return [
            symbol
            for symbol, sector_info in self.sector_mapping.items()
            if sector_info.sector_code == sector_code
        ]


# Global instance for easy access
_sector_mapper_instance = None


def get_sector_mapper() -> SectorMapper:
    """Get global sector mapper instance (singleton pattern)"""
    global _sector_mapper_instance
    if _sector_mapper_instance is None:
        _sector_mapper_instance = SectorMapper()
    return _sector_mapper_instance


def map_ticker_to_sector(ticker: str, default_sector: str = "Unknown") -> str:
    """
    Map a stock ticker to its corresponding sector.

    This function provides a simpler interface to get a sector name for a ticker
    without having to instantiate the SectorMapper class directly.

    Args:
        ticker (str): The stock ticker symbol
        default_sector (str, optional): Default sector if ticker not found. Defaults to "Unknown".

    Returns:
        str: The sector name for the given ticker
    """
    mapper = get_sector_mapper()
    sector_info = mapper.get_sector_info(ticker)

    if sector_info:
        return sector_info.sector_name
    return default_sector
