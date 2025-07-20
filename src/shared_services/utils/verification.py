"""Verification utilities for backtesting results and data integrity."""

import logging
from typing import Any, Dict, List, Optional, Union

import pandas as pd


def verify_backtest_output(
    results: dict[str, Any], required_fields: set = {"signal", "confidence", "returns"}
) -> bool:
    """
    Verify backtest output meets requirements.

    Args:
        results: Backtest results dictionary
        required_fields: Set of required result fields

    Returns:
        bool: True if verification passes
    """
    if not results:
        logging.error("❌ Empty results")
        return False

    missing_fields = required_fields - set(results.keys())
    if missing_fields:
        logging.error("❌ Missing required fields: {missing_fields}")
        return False

    # Verify signal values
    if "signal" in results and results["signal"] not in {-1, 0, 1}:
        logging.error("❌ Invalid signal value: {results['signal']}")
        return False

    # Verify confidence
    if "confidence" in results and not (0 <= results["confidence"] <= 1):
        logging.error("❌ Invalid confidence value: {results['confidence']}")
        return False

    logging.info("✅ Result verification passed")
    return True


def verify_data_integrity(
    data: Union[pd.DataFrame, Dict[str, Any]],
    required_columns: Optional[List[str]] = None,
    min_rows: int = 1,
    check_duplicates: bool = True,
    check_nulls: bool = True,
) -> Dict[str, Any]:
    """
    Verify the integrity of data used in the trading system.

    Args:
        data: DataFrame or dictionary containing the data to verify
        required_columns: List of columns that must be present
        min_rows: Minimum number of rows required
        check_duplicates: Whether to check for duplicate rows
        check_nulls: Whether to check for null values

    Returns:
        Dict with verification results:
            - passed (bool): Overall verification result
            - issues (List[str]): List of issues found
            - metrics (Dict): Data metrics like row count, columns, etc.
    """
    result = {
        "passed": True,
        "issues": [],
        "metrics": {
            "row_count": 0,
            "column_count": 0,
            "duplicate_count": 0,
            "null_count": 0,
        },
    }

    # Convert dict to DataFrame if necessary
    if isinstance(data, dict):
        try:
            data = pd.DataFrame(data)
        except Exception as e:
            result["passed"] = False
            result["issues"].append(f"Failed to convert dict to DataFrame: {str(e)}")
            return result

    # Check if data is empty
    if data.empty:
        result["passed"] = False
        result["issues"].append("Data is empty")
        return result

    # Check row count
    row_count = len(data)
    result["metrics"]["row_count"] = row_count
    if row_count < min_rows:
        result["passed"] = False
        result["issues"].append(
            f"Insufficient data: {row_count} rows (minimum {min_rows})"
        )

    # Check columns
    result["metrics"]["column_count"] = len(data.columns)
    if required_columns:
        missing_cols = set(required_columns) - set(data.columns)
        if missing_cols:
            result["passed"] = False
            result["issues"].append(f"Missing required columns: {missing_cols}")

    # Check for duplicates
    if check_duplicates:
        duplicate_count = data.duplicated().sum()
        result["metrics"]["duplicate_count"] = duplicate_count
        if duplicate_count > 0:
            result["issues"].append(f"Found {duplicate_count} duplicate rows")
            # Don't fail for duplicates, just warn

    # Check for nulls
    if check_nulls:
        null_count = data.isna().sum().sum()
        result["metrics"]["null_count"] = null_count
        if null_count > 0:
            columns_with_nulls = [col for col in data.columns if data[col].isna().any()]
            result["issues"].append(
                f"Found {null_count} null values in columns: {columns_with_nulls}"
            )
            # Don't fail for nulls, just warn

    # Log summary
    if result["passed"]:
        logging.info(
            f"✅ Data integrity verification passed: {row_count} rows, {len(data.columns)} columns"
        )
    else:
        logging.error(f"❌ Data integrity verification failed: {result['issues']}")

    return result
