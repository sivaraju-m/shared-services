from google.cloud import bigquery
import json
from typing import Any, Dict, List, Optional


def ensure_bq_dataset_and_table(dataset_id: str = "trading_data", 
                               table_id: str = "backtest_results",
                               schema: Optional[List[bigquery.SchemaField]] = None):
    client = bigquery.Client()
    full_dataset_id = f"{client.project}.{dataset_id}"
    full_table_id = f"{full_dataset_id}.{table_id}"

    try:
        client.get_dataset(full_dataset_id)
    except Exception:
        client.create_dataset(bigquery.Dataset(full_dataset_id), timeout=30)

    try:
        client.get_table(full_table_id)
    except Exception:
        if not schema:
            schema = [
                bigquery.SchemaField("ticker", "STRING"),
                bigquery.SchemaField("strategy", "STRING"),
                bigquery.SchemaField("start_date", "DATE"),
                bigquery.SchemaField("end_date", "DATE"),
                bigquery.SchemaField("cagr", "FLOAT"),
                bigquery.SchemaField("sharpe_ratio", "FLOAT"),
                bigquery.SchemaField("drawdown", "FLOAT"),
                bigquery.SchemaField("win_rate", "FLOAT"),
                bigquery.SchemaField("trades", "INTEGER"),
                bigquery.SchemaField("timestamp", "TIMESTAMP"),
            ]
        table = bigquery.Table(full_table_id, schema=schema)
        client.create_table(table, timeout=30)


def log_backtest_result(**kwargs):
    ensure_bq_dataset_and_table()
    client = bigquery.Client()
    table_id = f"{client.project}.trading_data.backtest_results"
    errors = client.insert_rows_json(table_id, [kwargs])
    return errors


def log_to_bigquery(data: Dict[str, Any], 
                   table_id: str = "budget_alerts", 
                   dataset_id: str = "audit_trail", 
                   project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Log data to BigQuery for analysis and auditing.
    
    Args:
        data: Dictionary or list of dictionaries containing the data to log.
        table_id: The BigQuery table ID.
        dataset_id: The BigQuery dataset ID (default: audit_trail).
        project_id: The GCP project ID. If None, uses the default project from credentials.
        
    Returns:
        List of errors, if any. Empty list means success.
    """
    client = bigquery.Client(project=project_id)
    
    # Convert to list if it's a single dict
    rows_to_insert = [data] if isinstance(data, dict) else data
    
    # Format table ID with project and dataset
    full_table_id = f"{client.project}.{dataset_id}.{table_id}"
    
    try:
        errors = client.insert_rows_json(full_table_id, rows_to_insert)
        if errors:
            print(f"Errors encountered while inserting to BigQuery: {errors}")
        return errors
    except Exception as e:
        print(f"Failed to log to BigQuery: {e}")
        return [{"error": str(e)}]


def log_budget_alert(budget_data: Dict[str, Any], actions_taken: List[str]) -> List[Dict[str, Any]]:
    """
    Log budget alert data to BigQuery.
    
    Args:
        budget_data: Dictionary containing budget alert data.
        actions_taken: List of actions taken in response to the budget alert.
        
    Returns:
        List of errors, if any. Empty list means success.
    """
    row = {
        "timestamp": budget_data.get("timestamp"),
        "budget_name": budget_data.get("budgetDisplayName"),
        "cost_amount": budget_data.get("costAmount"),
        "budget_amount": budget_data.get("budgetAmount"),
        "alert_threshold": budget_data.get("alertThresholdExceeded"),
        "actions_taken": json.dumps(actions_taken),
        "severity": (
            "critical"
            if budget_data.get("alertThresholdExceeded", 0) >= 100
            else "warning"
        ),
    }
    
    schema = [
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
        bigquery.SchemaField("budget_name", "STRING"),
        bigquery.SchemaField("cost_amount", "FLOAT"),
        bigquery.SchemaField("budget_amount", "FLOAT"),
        bigquery.SchemaField("alert_threshold", "FLOAT"),
        bigquery.SchemaField("actions_taken", "STRING"),
        bigquery.SchemaField("severity", "STRING"),
    ]
    
    ensure_bq_dataset_and_table("audit_trail", "budget_alerts", schema)
    return log_to_bigquery(row, "budget_alerts", "audit_trail")
