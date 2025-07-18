#!/usr/bin/env python3
"""
Enhanced BigQuery Writer Module for AI Trading Machine
Handles schema management, approval workflow, and cloud-based strategy execution
"""

import logging
import uuid
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

try:
    import numpy as np
    has_numpy = True
except ImportError:
    has_numpy = False

try:
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound
    has_bigquery = True
except ImportError:
    bigquery = None
    NotFound = Exception
    has_bigquery = False
    logging.warning("google-cloud-bigquery not installed. BigQuery functionality disabled.")

logger = logging.getLogger(__name__)


class EnhancedBigQueryWriter:
    """
    Enhanced BigQuery Writer with approval workflow and comprehensive strategy tracking
    """
    
    def __init__(self, project_id: str, dataset_id: str = "ai_trading_backtest", 
                 table_id: str = "strategy_results_enhanced", 
                 write_mode: str = "append", max_retries: int = 3):
        """
        Initialize Enhanced BigQuery writer
        
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID (enhanced schema)
            write_mode: 'append' or 'replace'
            max_retries: Maximum retry attempts for failed writes
        """
        if not has_bigquery:
            raise ImportError("google-cloud-bigquery is required for BigQuery functionality")
            
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
        
        logger.info(f"Enhanced BigQuery Writer initialized: {project_id}.{dataset_id}.{table_id}")
    
    def _get_enhanced_table_schema(self) -> List[Any]:
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
            dataset.location = "US"
            dataset.description = "AI Trading Machine enhanced strategy results with approval workflow"
            dataset = self.client.create_dataset(dataset, timeout=30)
            logger.info(f"Created dataset {self.dataset_id}")
    
    def _ensure_table_exists(self) -> None:
        """Ensure the BigQuery table exists with enhanced schema"""
        try:
            self.client.get_table(self.table_ref)
            logger.info(f"Table {self.table_id} already exists")
        except NotFound:
            schema = self._get_enhanced_table_schema()
            table = bigquery.Table(self.table_ref, schema=schema)
            
            # Add partitioning and clustering
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="execution_timestamp"
            )
            table.clustering_fields = ["strategy_name", "scenario_name", "approved"]
            table.description = "Enhanced strategy results with approval workflow"
            
            table = self.client.create_table(table, timeout=30)
            logger.info(f"Created table {self.table_id} with enhanced schema")
    
    def insert_strategy_result(self, result_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a single strategy result with approval workflow
        
        Args:
            result_dict: Dictionary containing strategy backtest results
            
        Returns:
            Dictionary with insertion status and details
        """
        try:
            row = self._prepare_enhanced_row_data(result_dict)
            errors = self.client.insert_rows_json(self.client.get_table(self.table_ref), [row])
            
            if not errors:
                logger.info(f"Successfully inserted strategy result: {row['strategy_name']} - {row['scenario_name']}")
                return {
                    "success": True,
                    "run_id": row['run_id'],
                    "approved": row.get('approved', 'PENDING'),
                    "composite_score": row.get('composite_score', 0),
                    "live_trading_eligible": row.get('live_trading_eligible', False)
                }
            else:
                logger.error(f"BigQuery insertion errors: {errors}")
                return {
                    "success": False,
                    "errors": errors
                }
                
        except Exception as e:
            logger.error(f"Failed to insert strategy result: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_enhanced_row_data(self, result_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare row data for BigQuery insertion with enhanced schema and approval workflow
        
        Args:
            result_dict: Dictionary containing backtest results
            
        Returns:
            Formatted row for BigQuery insertion
        """
        # Generate run_id if not provided
        run_id = result_dict.get('run_id', str(uuid.uuid4()))
        
        # Set execution timestamp
        execution_timestamp = datetime.now(timezone.utc)
        if 'execution_timestamp' in result_dict:
            if isinstance(result_dict['execution_timestamp'], str):
                execution_timestamp = datetime.fromisoformat(result_dict['execution_timestamp'].replace('Z', '+00:00'))
            elif isinstance(result_dict['execution_timestamp'], datetime):
                execution_timestamp = result_dict['execution_timestamp']
        
        # Calculate composite score and approval metrics
        composite_score = self._calculate_composite_score(result_dict)
        approval_info = self._calculate_approval_metrics(result_dict, composite_score)
        
        # Prepare scenario dates
        scenario_start = self._parse_date(result_dict.get('scenario_start_date'))
        scenario_end = self._parse_date(result_dict.get('scenario_end_date'))
        
        row = {
            # Identification
            "run_id": run_id,
            "execution_timestamp": execution_timestamp.isoformat(),
            
            # Strategy Information
            "strategy_name": result_dict.get('strategy_name', 'unknown'),
            "strategy_version": result_dict.get('strategy_version', '1.0.0'),
            "strategy_category": result_dict.get('strategy_category', self._categorize_strategy(result_dict.get('strategy_name', ''))),
            
            # Scenario Information
            "scenario_name": result_dict.get('scenario_name', 'default'),
            "scenario_type": result_dict.get('scenario_type', 'normal'),
            "scenario_start_date": scenario_start,
            "scenario_end_date": scenario_end,
            "scenario_duration_days": self._calculate_duration_days(scenario_start, scenario_end),
            
            # Parameters
            "parameters": self._safe_json_serialize(result_dict.get('parameters', {})),
            "parameter_hash": self._calculate_parameter_hash(result_dict.get('parameters', {})),
            
            # Core Performance Metrics
            "total_return": self._safe_float(result_dict.get('total_return')),
            "cagr": self._safe_float(result_dict.get('cagr')),
            "sharpe_ratio": self._safe_float(result_dict.get('sharpe_ratio')),
            "calmar_ratio": self._safe_float(result_dict.get('calmar_ratio')),
            "sortino_ratio": self._safe_float(result_dict.get('sortino_ratio')),
            
            # Risk Metrics
            "max_drawdown": self._safe_float(result_dict.get('max_drawdown')),
            "volatility": self._safe_float(result_dict.get('volatility')),
            "downside_volatility": self._safe_float(result_dict.get('downside_volatility')),
            "var_95": self._safe_float(result_dict.get('var_95')),
            "cvar_95": self._safe_float(result_dict.get('cvar_95')),
            
            # Trading Metrics
            "num_trades": self._safe_int(result_dict.get('num_trades')),
            "win_rate": self._safe_float(result_dict.get('win_rate')),
            "avg_trade_return": self._safe_float(result_dict.get('avg_trade_return')),
            "avg_win": self._safe_float(result_dict.get('avg_win')),
            "avg_loss": self._safe_float(result_dict.get('avg_loss')),
            "profit_factor": self._safe_float(result_dict.get('profit_factor')),
            
            # Benchmark Comparison
            "benchmark_return": self._safe_float(result_dict.get('benchmark_return')),
            "excess_return": self._safe_float(result_dict.get('excess_return')),
            "alpha": self._safe_float(result_dict.get('alpha')),
            "beta": self._safe_float(result_dict.get('beta')),
            "information_ratio": self._safe_float(result_dict.get('information_ratio')),
            "tracking_error": self._safe_float(result_dict.get('tracking_error')),
            
            # Operational Metrics
            "execution_time_seconds": self._safe_float(result_dict.get('execution_time_seconds')),
            "data_quality_score": self._safe_float(result_dict.get('data_quality_score', 1.0)),
            "backtest_start_date": self._parse_date(result_dict.get('backtest_start_date')),
            "backtest_end_date": self._parse_date(result_dict.get('backtest_end_date')),
            
            # Success Metrics & Scoring
            "composite_score": composite_score,
            "risk_adjusted_score": approval_info['risk_adjusted_score'],
            "consistency_score": approval_info['consistency_score'],
            "drawdown_score": approval_info['drawdown_score'],
            "return_score": approval_info['return_score'],
            
            # Approval Workflow
            "approved": approval_info['approved'],
            "approval_score": approval_info['approval_score'],
            "approval_reason": approval_info['approval_reason'],
            "approved_by": "automated_system",
            "approval_date": execution_timestamp.isoformat() if approval_info['approved'] != 'PENDING' else None,
            
            # Risk Assessment
            "risk_level": approval_info['risk_level'],
            "max_position_size": approval_info['max_position_size'],
            "recommended_allocation": approval_info['recommended_allocation'],
            
            # Live Trading Status
            "live_trading_eligible": approval_info['live_trading_eligible'],
            "live_trading_start_date": None,
            "live_trading_end_date": None,
            "live_trading_status": "NOT_STARTED",
            
            # Market Conditions
            "market_regime": result_dict.get('market_regime', 'normal'),
            "volatility_regime": self._determine_volatility_regime(result_dict.get('volatility')),
            "liquidity_score": self._safe_float(result_dict.get('liquidity_score', 0.8)),
            
            # Metadata
            "created_at": execution_timestamp.isoformat(),
            "updated_at": execution_timestamp.isoformat(),
            "tags": result_dict.get('tags', []),
            "notes": result_dict.get('notes'),
            
            # Environment
            "environment": "CLOUD",  # Always cloud for production runs
            "compute_resource": result_dict.get('compute_resource', 'cloud-run'),
            "data_source": result_dict.get('data_source', 'historical'),
        }
        
        # Remove None values to avoid BigQuery issues
        row = {k: v for k, v in row.items() if v is not None}
        
        return row
    
    def _calculate_composite_score(self, result_dict: Dict[str, Any]) -> float:
        """Calculate composite strategy score (0-100)"""
        sharpe = self._safe_float(result_dict.get('sharpe_ratio', 0)) or 0
        total_return = self._safe_float(result_dict.get('total_return', 0)) or 0
        max_dd = self._safe_float(result_dict.get('max_drawdown', 1)) or 1
        win_rate = self._safe_float(result_dict.get('win_rate', 0)) or 0
        
        # Weighted scoring
        sharpe_score = min(100, max(0, sharpe * 25))  # Sharpe 4.0 = 100 points
        return_score = min(100, max(0, total_return * 100))  # 100% return = 100 points
        drawdown_score = min(100, max(0, (1 - abs(max_dd)) * 100))  # 0% DD = 100 points
        win_rate_score = win_rate * 100  # 100% win rate = 100 points
        
        # Composite: 40% Sharpe, 30% Return, 20% Drawdown, 10% Win Rate
        composite = (sharpe_score * 0.4 + return_score * 0.3 + 
                    drawdown_score * 0.2 + win_rate_score * 0.1)
        
        return round(composite, 2)
    
    def _calculate_approval_metrics(self, result_dict: Dict[str, Any], composite_score: float) -> Dict[str, Any]:
        """Calculate approval workflow metrics"""
        sharpe = self._safe_float(result_dict.get('sharpe_ratio', 0)) or 0
        total_return = self._safe_float(result_dict.get('total_return', 0)) or 0
        max_dd = abs(self._safe_float(result_dict.get('max_drawdown', 1)) or 1)
        win_rate = self._safe_float(result_dict.get('win_rate', 0)) or 0
        
        # Approval thresholds
        min_sharpe = 1.0
        min_return = 0.10  # 10%
        max_drawdown = 0.15  # 15%
        min_win_rate = 0.50  # 50%
        
        # Check thresholds
        meets_sharpe = sharpe >= min_sharpe
        meets_return = total_return >= min_return
        meets_drawdown = max_dd <= max_drawdown
        meets_win_rate = win_rate >= min_win_rate
        
        # Calculate individual scores
        risk_adjusted_score = min(100, max(0, sharpe * 25))
        consistency_score = win_rate * 100
        drawdown_score = min(100, max(0, (1 - max_dd) * 100))
        return_score = min(100, max(0, total_return * 100))
        
        # Overall approval score
        approval_score = (risk_adjusted_score + consistency_score + drawdown_score + return_score) / 4
        
        # Determine approval status
        all_criteria_met = meets_sharpe and meets_return and meets_drawdown and meets_win_rate
        high_score = composite_score >= 70
        
        if all_criteria_met and high_score:
            approved = "APPROVED"
            approval_reason = "Meets all criteria and high composite score"
            live_trading_eligible = True
        elif all_criteria_met:
            approved = "APPROVED"
            approval_reason = "Meets all criteria"
            live_trading_eligible = True
        elif high_score:
            approved = "UNDER_REVIEW"
            approval_reason = "High score but some criteria not met"
            live_trading_eligible = False
        else:
            approved = "REJECTED"
            approval_reason = "Does not meet minimum criteria"
            live_trading_eligible = False
        
        # Risk level assessment
        if max_dd <= 0.05:
            risk_level = "LOW"
            max_position_size = 0.25
            recommended_allocation = 0.20
        elif max_dd <= 0.10:
            risk_level = "MEDIUM"
            max_position_size = 0.15
            recommended_allocation = 0.15
        elif max_dd <= 0.15:
            risk_level = "HIGH"
            max_position_size = 0.10
            recommended_allocation = 0.10
        else:
            risk_level = "EXTREME"
            max_position_size = 0.05
            recommended_allocation = 0.05
        
        return {
            'approved': approved,
            'approval_score': round(approval_score, 2),
            'approval_reason': approval_reason,
            'risk_adjusted_score': round(risk_adjusted_score, 2),
            'consistency_score': round(consistency_score, 2),
            'drawdown_score': round(drawdown_score, 2),
            'return_score': round(return_score, 2),
            'risk_level': risk_level,
            'max_position_size': max_position_size,
            'recommended_allocation': recommended_allocation,
            'live_trading_eligible': live_trading_eligible
        }
    
    def _categorize_strategy(self, strategy_name: str) -> str:
        """Categorize strategy based on name"""
        strategy_name = strategy_name.lower()
        if 'momentum' in strategy_name:
            return 'momentum'
        elif 'mean_reversion' in strategy_name or 'reversion' in strategy_name:
            return 'mean_reversion'
        elif 'lstm' in strategy_name or 'neural' in strategy_name or 'ml' in strategy_name:
            return 'machine_learning'
        elif 'options' in strategy_name:
            return 'options'
        elif 'pairs' in strategy_name:
            return 'pairs_trading'
        elif 'sector' in strategy_name:
            return 'sector_rotation'
        elif 'sentiment' in strategy_name:
            return 'sentiment'
        elif 'multi' in strategy_name or 'timeframe' in strategy_name:
            return 'multi_timeframe'
        else:
            return 'other'
    
    def _parse_date(self, date_value: Any) -> Optional[str]:
        """Parse date value to string format"""
        if date_value is None:
            return None
        if isinstance(date_value, str):
            try:
                # Try to parse and reformat to ensure correct format
                parsed_date = datetime.strptime(date_value, '%Y-%m-%d')
                return parsed_date.strftime('%Y-%m-%d')
            except:
                return date_value
        if hasattr(date_value, 'strftime'):
            return date_value.strftime('%Y-%m-%d')
        return str(date_value)
    
    def _calculate_duration_days(self, start_date: Optional[str], end_date: Optional[str]) -> Optional[int]:
        """Calculate duration in days between two dates"""
        if not start_date or not end_date:
            return None
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            return (end - start).days
        except:
            return None
    
    def _safe_json_serialize(self, obj: Any) -> str:
        """Safely serialize object to JSON, handling numpy types"""
        def convert_numpy_types(item: Any) -> Any:
            if hasattr(item, 'item'):  # numpy scalar
                return item.item()
            elif hasattr(item, 'tolist'):  # numpy array
                return item.tolist()
            elif isinstance(item, dict):
                return {k: convert_numpy_types(v) for k, v in item.items()}
            elif isinstance(item, list):
                return [convert_numpy_types(v) for v in item]
            else:
                return item
        
        clean_obj = convert_numpy_types(obj)
        return json.dumps(clean_obj)
    
    def _calculate_parameter_hash(self, parameters: Dict[str, Any]) -> str:
        """Calculate MD5 hash of parameters for deduplication"""
        # Convert numpy types to standard Python types for JSON serialization
        def convert_numpy_types(obj: Any) -> Any:
            if hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif has_numpy and hasattr(obj, 'tolist'):  # numpy array
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            else:
                return obj
        
        clean_params = convert_numpy_types(parameters)
        param_str = json.dumps(clean_params, sort_keys=True)
        return hashlib.md5(param_str.encode()).hexdigest()
    
    def _determine_volatility_regime(self, volatility: Optional[float]) -> str:
        """Determine volatility regime based on volatility value"""
        if volatility is None:
            return "unknown"
        volatility = abs(volatility)
        if volatility < 0.10:
            return "low"
        elif volatility < 0.20:
            return "medium"
        else:
            return "high"
    
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
    
    def query_approved_strategies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query approved strategies ready for live trading
        
        Args:
            limit: Number of top strategies to return
            
        Returns:
            List of approved strategy results
        """
        query = f"""
        SELECT *
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        WHERE approved = 'APPROVED' 
          AND live_trading_eligible = TRUE
        ORDER BY composite_score DESC, sharpe_ratio DESC
        LIMIT {limit}
        """
        
        try:
            results = self.client.query(query)
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to query approved strategies: {e}")
            return []
    
    def get_strategy_performance_summary(self, strategy_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get strategy performance summary"""
        where_clause = f"WHERE strategy_name = '{strategy_name}'" if strategy_name else ""
        
        query = f"""
        SELECT 
            strategy_name,
            strategy_category,
            COUNT(*) as total_backtests,
            COUNT(CASE WHEN approved = 'APPROVED' THEN 1 END) as approved_count,
            AVG(composite_score) as avg_composite_score,
            AVG(sharpe_ratio) as avg_sharpe_ratio,
            AVG(total_return) as avg_total_return,
            AVG(max_drawdown) as avg_max_drawdown,
            MAX(composite_score) as best_composite_score,
            MAX(execution_timestamp) as last_backtest
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        {where_clause}
        GROUP BY strategy_name, strategy_category
        ORDER BY avg_composite_score DESC
        """
        
        try:
            results = self.client.query(query)
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return []
    
    def cleanup_old_results(self, days_old: int = 90) -> Dict[str, Any]:
        """Clean up old rejected results"""
        query = f"""
        DELETE FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        WHERE approved = 'REJECTED' 
          AND execution_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days_old} DAY)
        """
        
        try:
            job = self.client.query(query)
            job.result()  # Wait for completion
            logger.info(f"Cleaned up rejected results older than {days_old} days")
            return {"success": True, "message": f"Cleaned up old rejected results"}
        except Exception as e:
            logger.error(f"Failed to cleanup old results: {e}")
            return {"success": False, "error": str(e)}
