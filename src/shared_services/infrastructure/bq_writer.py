#!/usr/bin/env python3
"""
BigQuery Writer Module for AI Trading Machine
Handles schema management and data insertion for backtest results
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
import json
import time

try:
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound, GoogleCloudError

    has_bigquery = True
except ImportError:
    bigquery = None
    NotFound = Exception
    GoogleCloudError = Exception
    has_bigquery = False
    logging.warning(
        "google-cloud-bigquery not installed. BigQuery functionality disabled."
    )

logger = logging.getLogger(__name__)


class BigQueryWriter:
    """
    BigQuery Writer for backtest results with robust error handling and retry logic
    """

    def __init__(
        self,
        project_id: str,
        dataset_id: str,
        table_id: str,
        write_mode: str = "append",
        max_retries: int = 3,
    ):
        """
        Initialize BigQuery writer

        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID
            write_mode: 'append' or 'replace'
            max_retries: Maximum retry attempts for failed writes
        """
        if not has_bigquery:
            raise ImportError(
                "google-cloud-bigquery is required for BigQuery functionality"
            )

        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.write_mode = write_mode
        self.max_retries = max_retries

        # Initialize BigQuery client
        self.client = bigquery.Client(project=project_id)
        self.dataset_ref = self.client.dataset(dataset_id)
        self.table_ref = self.dataset_ref.table(table_id)

        # Ensure dataset and table exist
        self._ensure_dataset_exists()
        self._ensure_table_exists()

        logger.info(
            f"BigQuery Writer initialized: {project_id}.{dataset_id}.{table_id}"
        )

    def _get_table_schema(self) -> List[Any]:
        """Define the enhanced BigQuery table schema for strategy results with approval workflow"""
        if not has_bigquery:
            return []
        return [
            # Identification
            bigquery.SchemaField("run_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("execution_timestamp", "TIMESTAMP", mode="REQUIRED"),
            # Strategy Information
            bigquery.SchemaField("strategy_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("strategy_version", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("strategy_category", "STRING", mode="NULLABLE"),
            # Scenario Information
            bigquery.SchemaField("scenario_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("scenario_type", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("scenario_start_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("scenario_end_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("scenario_duration_days", "INTEGER", mode="NULLABLE"),
            # Parameters
            bigquery.SchemaField("parameters", "JSON", mode="REQUIRED"),
            bigquery.SchemaField("parameter_hash", "STRING", mode="NULLABLE"),
            # Core Performance Metrics
            bigquery.SchemaField("total_return", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("cagr", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("sharpe_ratio", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("calmar_ratio", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("sortino_ratio", "FLOAT", mode="NULLABLE"),
            # Risk Metrics
            bigquery.SchemaField("max_drawdown", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("volatility", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("downside_volatility", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("var_95", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("cvar_95", "FLOAT", mode="NULLABLE"),
            # Trading Metrics
            bigquery.SchemaField("num_trades", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("win_rate", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("avg_trade_return", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("avg_win", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("avg_loss", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("profit_factor", "FLOAT", mode="NULLABLE"),
            # Benchmark Comparison
            bigquery.SchemaField("benchmark_return", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("excess_return", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("alpha", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("beta", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("information_ratio", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("tracking_error", "FLOAT", mode="NULLABLE"),
            # Operational Metrics
            bigquery.SchemaField("execution_time_seconds", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("data_quality_score", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("backtest_start_date", "DATE", mode="NULLABLE"),
            bigquery.SchemaField("backtest_end_date", "DATE", mode="NULLABLE"),
            # Success Metrics & Scoring
            bigquery.SchemaField("composite_score", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("risk_adjusted_score", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("consistency_score", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("drawdown_score", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("return_score", "FLOAT", mode="NULLABLE"),
            # Approval Workflow
            bigquery.SchemaField("approved", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("approval_score", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("approval_reason", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("approved_by", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("approval_date", "TIMESTAMP", mode="NULLABLE"),
            # Risk Assessment
            bigquery.SchemaField("risk_level", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("max_position_size", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("recommended_allocation", "FLOAT", mode="NULLABLE"),
            # Live Trading Status
            bigquery.SchemaField("live_trading_eligible", "BOOLEAN", mode="NULLABLE"),
            bigquery.SchemaField("live_trading_start_date", "DATE", mode="NULLABLE"),
            bigquery.SchemaField("live_trading_end_date", "DATE", mode="NULLABLE"),
            bigquery.SchemaField("live_trading_status", "STRING", mode="NULLABLE"),
            # Market Conditions
            bigquery.SchemaField("market_regime", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("volatility_regime", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("liquidity_score", "FLOAT", mode="NULLABLE"),
            # Metadata
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("tags", "STRING", mode="REPEATED"),
            bigquery.SchemaField("notes", "STRING", mode="NULLABLE"),
            # Environment
            bigquery.SchemaField("environment", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("compute_resource", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("data_source", "STRING", mode="NULLABLE"),
        ]

    def _ensure_dataset_exists(self) -> None:
        """Ensure the BigQuery dataset exists"""
        try:
            self.client.get_dataset(self.dataset_ref)
            logger.info(f"Dataset {self.dataset_id} already exists")
        except NotFound:
            dataset = bigquery.Dataset(self.dataset_ref)
            dataset.location = "US"  # Default location
            dataset = self.client.create_dataset(dataset, timeout=30)
            logger.info(f"Created dataset {self.dataset_id}")

    def _ensure_table_exists(self) -> None:
        """Ensure the BigQuery table exists with proper schema"""
        try:
            table = self.client.get_table(self.table_ref)
            logger.info(f"Table {self.table_id} already exists")

            # Optionally verify schema compatibility
            self._verify_schema_compatibility(table)

        except NotFound:
            schema = self._get_table_schema()
            table = bigquery.Table(self.table_ref, schema=schema)

            # Add table description
            table.description = (
                "AI Trading Machine backtest results with comprehensive metrics"
            )

            # Partition by timestamp for better query performance
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY, field="timestamp"
            )

            # Cluster by strategy_name and scenario_name
            table.clustering_fields = ["strategy_name", "scenario_name"]

            table = self.client.create_table(table, timeout=30)
            logger.info(
                f"Created table {self.table_id} with partitioning and clustering"
            )

    def _verify_schema_compatibility(self, table: Any) -> None:
        """Verify existing table schema is compatible with our requirements"""
        existing_fields = {field.name: field for field in table.schema}
        required_fields = {field.name: field for field in self._get_table_schema()}

        missing_fields = set(required_fields.keys()) - set(existing_fields.keys())
        if missing_fields:
            logger.warning(f"Table schema missing fields: {missing_fields}")
            # In production, you might want to add these fields or raise an error

    def insert_result(
        self, result_dict: Dict[str, Any], run_id: Optional[str] = None
    ) -> bool:
        """
        Insert a single backtest result into BigQuery

        Args:
            result_dict: Dictionary containing backtest results
            run_id: Optional run ID, generated if not provided

        Returns:
            bool: True if successful, False otherwise
        """
        if run_id is None:
            run_id = str(uuid.uuid4())

        # Prepare the row for insertion
        row = self._prepare_row(result_dict, run_id)

        # Insert with retry logic
        for attempt in range(self.max_retries):
            try:
                errors = self.client.insert_rows_json(
                    self.client.get_table(self.table_ref), [row]
                )

                if not errors:
                    logger.info(f"Successfully inserted result for run_id: {run_id}")
                    return True
                else:
                    logger.error(f"BigQuery insert errors: {errors}")
                    return False

            except GoogleCloudError as e:
                logger.error(f"BigQuery error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to insert after {self.max_retries} attempts")
                    return False
            except Exception as e:
                logger.error(f"Unexpected error during BigQuery insert: {e}")
                return False

        return False

    def insert_batch_results(
        self, results: List[Dict[str, Any]], run_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Insert multiple backtest results in batch

        Args:
            results: List of result dictionaries
            run_ids: Optional list of run IDs

        Returns:
            Dict with success/failure statistics
        """
        if run_ids is None:
            run_ids = [str(uuid.uuid4()) for _ in results]

        if len(results) != len(run_ids):
            raise ValueError("Number of results must match number of run_ids")

        # Prepare all rows
        rows = []
        for result_dict, run_id in zip(results, run_ids):
            row = self._prepare_row(result_dict, run_id)
            rows.append(row)

        # Insert batch with retry logic
        for attempt in range(self.max_retries):
            try:
                errors = self.client.insert_rows_json(
                    self.client.get_table(self.table_ref), rows
                )

                if not errors:
                    logger.info(f"Successfully inserted batch of {len(rows)} results")
                    return {
                        "success": True,
                        "inserted_count": len(rows),
                        "failed_count": 0,
                        "errors": [],
                    }
                else:
                    logger.error(f"BigQuery batch insert errors: {errors}")
                    return {
                        "success": False,
                        "inserted_count": 0,
                        "failed_count": len(rows),
                        "errors": errors,
                    }

            except GoogleCloudError as e:
                logger.error(f"BigQuery batch error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                else:
                    logger.error(
                        f"Failed to insert batch after {self.max_retries} attempts"
                    )
                    return {
                        "success": False,
                        "inserted_count": 0,
                        "failed_count": len(rows),
                        "errors": [str(e)],
                    }

        return {
            "success": False,
            "inserted_count": 0,
            "failed_count": len(rows),
            "errors": ["Max retries exceeded"],
        }

    def _prepare_row(self, result_dict: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        """Prepare a result dictionary for BigQuery insertion"""

        # Extract parameters as JSON
        param_set = result_dict.get("parameters", {})
        if isinstance(param_set, dict):
            param_set_json = json.dumps(param_set)
        else:
            param_set_json = str(param_set)

        # Current timestamp
        timestamp = datetime.now().isoformat()

        # Prepare the row with all possible fields
        row = {
            "run_id": run_id,
            "strategy_name": result_dict.get("strategy_name", "unknown"),
            "scenario_name": result_dict.get("scenario_name", "default"),
            "param_set": param_set_json,
            "timestamp": timestamp,
            # Performance metrics
            "cagr": self._safe_float(result_dict.get("cagr")),
            "sharpe_ratio": self._safe_float(result_dict.get("sharpe_ratio")),
            "drawdown": self._safe_float(result_dict.get("drawdown")),
            "win_rate": self._safe_float(result_dict.get("win_rate")),
            "pnl_total": self._safe_float(result_dict.get("pnl_total")),
            "num_trades": self._safe_int(result_dict.get("num_trades")),
            # Additional metrics
            "total_return": self._safe_float(result_dict.get("total_return")),
            "volatility": self._safe_float(result_dict.get("volatility")),
            "calmar_ratio": self._safe_float(result_dict.get("calmar_ratio")),
            "max_drawdown": self._safe_float(result_dict.get("max_drawdown")),
            "avg_trade_return": self._safe_float(result_dict.get("avg_trade_return")),
            "profit_factor": self._safe_float(result_dict.get("profit_factor")),
            "recovery_factor": self._safe_float(result_dict.get("recovery_factor")),
            "execution_time_seconds": self._safe_float(
                result_dict.get("execution_time_seconds")
            ),
            "market_exposure": self._safe_float(result_dict.get("market_exposure")),
            "benchmark_return": self._safe_float(result_dict.get("benchmark_return")),
            "alpha": self._safe_float(result_dict.get("alpha")),
            "beta": self._safe_float(result_dict.get("beta")),
            "information_ratio": self._safe_float(result_dict.get("information_ratio")),
            "tracking_error": self._safe_float(result_dict.get("tracking_error")),
        }

        # Remove None values to avoid BigQuery issues
        row = {k: v for k, v in row.items() if v is not None}

        return row

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float, handling None and invalid values"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int, handling None and invalid values"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def query_best_strategies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query the best performing strategies by Sharpe ratio

        Args:
            limit: Number of top strategies to return

        Returns:
            List of strategy results sorted by Sharpe ratio
        """
        query = f"""
        SELECT 
            strategy_name,
            scenario_name,
            param_set,
            sharpe_ratio,
            cagr,
            drawdown,
            win_rate,
            pnl_total,
            num_trades,
            timestamp
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        WHERE sharpe_ratio IS NOT NULL
        ORDER BY sharpe_ratio DESC
        LIMIT {limit}
        """

        try:
            results = self.client.query(query).to_dataframe()
            return results.to_dict("records")
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def get_strategy_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary across all strategies"""
        query = f"""
        SELECT 
            strategy_name,
            scenario_name,
            COUNT(*) as total_runs,
            AVG(sharpe_ratio) as avg_sharpe,
            MAX(sharpe_ratio) as max_sharpe,
            AVG(cagr) as avg_cagr,
            AVG(drawdown) as avg_drawdown,
            AVG(win_rate) as avg_win_rate,
            MAX(timestamp) as last_run
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        GROUP BY strategy_name, scenario_name
        ORDER BY avg_sharpe DESC
        """

        try:
            results = self.client.query(query).to_dataframe()
            return {
                "summary": results.to_dict("records"),
                "total_strategies": len(results),
                "query_timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Summary query failed: {e}")
            return {"error": str(e)}

    def clear_table(self) -> bool:
        """Clear all data from the table (use with caution)"""
        if self.write_mode != "replace":
            logger.warning("Clear operation requires write_mode='replace'")
            return False

        try:
            query = f"DELETE FROM `{self.project_id}.{self.dataset_id}.{self.table_id}` WHERE TRUE"
            self.client.query(query).result()
            logger.info("Table cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to clear table: {e}")
            return False
