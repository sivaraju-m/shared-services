# src/ai_trading_machine/utils/data_cleaner.py

import pandas as pd


def clean_and_impute_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and fill missing OHLCV data using simple interpolation.
    """
    df = df.copy()
    df = df.sort_values(by="date")

    df.ffill(inplace=True)
    df.bfill(inplace=True)

    # Drop rows still with missing values
    df.dropna(inplace=True)

    return df


def clean_ohlcv_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Alias for clean_and_impute_data for compatibility with backtest_runner.
    """
    return clean_and_impute_data(df)


def clean_data(df: pd.DataFrame, columns_to_clean: list = None, method: str = 'ffill') -> pd.DataFrame:
    """
    General purpose data cleaning function.

    Args:
        df: Input DataFrame to clean
        columns_to_clean: List of columns to clean (None for all columns)
        method: Cleaning method ('ffill', 'bfill', 'interpolate', 'drop')

    Returns:
        Cleaned DataFrame
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # Select columns to clean
    if columns_to_clean is None:
        columns_to_clean = df.columns

    # Apply cleaning method
    if method == 'ffill':
        df[columns_to_clean] = df[columns_to_clean].ffill()
    elif method == 'bfill':
        df[columns_to_clean] = df[columns_to_clean].bfill()
    elif method == 'interpolate':
        df[columns_to_clean] = df[columns_to_clean].interpolate()
    elif method == 'drop':
        df = df.dropna(subset=columns_to_clean)

    return df
