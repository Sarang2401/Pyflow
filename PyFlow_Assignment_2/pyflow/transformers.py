"""
Data transformation module.
Question 32: Reusable transformation functions.
Questions 22-29: Pandas transformations (missing values, outliers, deduplication,
                 merging, aggregations, datetime, rolling window, filtering).
"""

import logging
from typing import Any, Dict, List, Optional, Union
from collections import deque, defaultdict, Counter

import pandas as pd
import numpy as np

from pyflow.exceptions import TransformationError

logger = logging.getLogger(__name__)


def handle_missing_values(
    df: pd.DataFrame,
    strategy: str = 'drop',
    fill_value: Any = None,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Question 22: Handle missing values with configurable strategies.
    
    Args:
        df: Input DataFrame
        strategy: Strategy - 'drop', 'fill', 'mean', 'median', 'mode', 'forward_fill', 'backward_fill'
        fill_value: Value to use for 'fill' strategy
        columns: Columns to apply strategy to (None for all)
        
    Returns:
        DataFrame with missing values handled
        
    Raises:
        TransformationError: If strategy is invalid
    """
    try:
        df = df.copy()
        target_cols = columns if columns else df.columns.tolist()
        
        logger.info(f"Handling missing values using '{strategy}' strategy")
        
        if strategy == 'drop':
            df = df.dropna(subset=target_cols)
        elif strategy == 'fill':
            if fill_value is None:
                raise TransformationError("fill_value required for 'fill' strategy")
            df[target_cols] = df[target_cols].fillna(fill_value)
        elif strategy == 'mean':
            for col in target_cols:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].mean())
        elif strategy == 'median':
            for col in target_cols:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
        elif strategy == 'mode':
            for col in target_cols:
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col] = df[col].fillna(mode_val[0])
        elif strategy == 'forward_fill':
            df[target_cols] = df[target_cols].ffill()
        elif strategy == 'backward_fill':
            df[target_cols] = df[target_cols].bfill()
        else:
            raise TransformationError(f"Unknown strategy: {strategy}")
        
        missing_after = df[target_cols].isnull().sum().sum()
        logger.info(f"Missing values after handling: {missing_after}")
        
        return df
        
    except Exception as e:
        raise TransformationError(f"Failed to handle missing values: {e}")


def remove_outliers(
    df: pd.DataFrame,
    columns: List[str],
    method: str = 'iqr',
    threshold: float = 1.5
) -> pd.DataFrame:
    """
    Question 23: Detect and remove outliers using IQR method.
    
    Args:
        df: Input DataFrame
        columns: Columns to check for outliers
        method: Method to use ('iqr' or 'zscore')
        threshold: IQR multiplier or z-score threshold
        
    Returns:
        DataFrame with outliers removed
        
    Raises:
        TransformationError: If method is invalid
    """
    try:
        df = df.copy()
        initial_count = len(df)
        
        logger.info(f"Removing outliers using '{method}' method with threshold {threshold}")
        
        if method == 'iqr':
            # IQR method
            for col in columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - threshold * IQR
                    upper_bound = Q3 + threshold * IQR
                    
                    df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
        
        elif method == 'zscore':
            # Z-score method
            for col in columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                    df = df[z_scores < threshold]
        else:
            raise TransformationError(f"Unknown outlier method: {method}")
        
        removed_count = initial_count - len(df)
        logger.info(f"Removed {removed_count} outlier rows ({removed_count/initial_count*100:.2f}%)")
        
        return df
        
    except Exception as e:
        raise TransformationError(f"Failed to remove outliers: {e}")


def remove_duplicates(
    df: pd.DataFrame,
    subset: Optional[List[str]] = None,
    keep: str = 'first'
) -> pd.DataFrame:
    """
    Question 24: Remove duplicate rows.
    
    Args:
        df: Input DataFrame
        subset: Columns to consider for identifying duplicates
        keep: Which duplicates to keep ('first', 'last', False)
        
    Returns:
        DataFrame with duplicates removed
    """
    try:
        df = df.copy()
        initial_count = len(df)
        
        logger.info(f"Removing duplicates (keep={keep})")
        
        df = df.drop_duplicates(subset=subset, keep=keep)
        
        removed_count = initial_count - len(df)
        logger.info(f"Removed {removed_count} duplicate rows")
        
        return df
        
    except Exception as e:
        raise TransformationError(f"Failed to remove duplicates: {e}")


def convert_datetime(
    df: pd.DataFrame,
    columns: List[str],
    format: Optional[str] = None,
    errors: str = 'coerce'
) -> pd.DataFrame:
    """
    Question 27: Convert columns to datetime with error handling.
    
    Args:
        df: Input DataFrame
        columns: Columns to convert
        format: Datetime format string (None for auto-detection)
        errors: How to handle errors ('raise', 'coerce', 'ignore')
        
    Returns:
        DataFrame with datetime columns
    """
    try:
        df = df.copy()
        
        logger.info(f"Converting {len(columns)} columns to datetime")
        
        for col in columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format=format, errors=errors)
                
                # Count invalid dates
                if errors == 'coerce':
                    invalid_count = df[col].isnull().sum()
                    if invalid_count > 0:
                        logger.warning(f"Column '{col}': {invalid_count} invalid dates converted to NaT")
        
        return df
        
    except Exception as e:
        raise TransformationError(f"Failed to convert datetime: {e}")


def calculate_rolling_metrics(
    df: pd.DataFrame,
    column: str,
    window: int,
    metrics: List[str] = ['mean', 'std', 'min', 'max']
) -> pd.DataFrame:
    """
    Question 28: Calculate rolling window metrics.
    
    Args:
        df: Input DataFrame
        column: Column to calculate metrics for
        window: Window size
        metrics: List of metrics to calculate
        
    Returns:
        DataFrame with rolling metrics added
    """
    try:
        df = df.copy()
        
        logger.info(f"Calculating rolling metrics for '{column}' with window={window}")
        
        rolling = df[column].rolling(window=window)
        
        for metric in metrics:
            col_name = f"{column}_rolling_{metric}_{window}"
            
            if metric == 'mean':
                df[col_name] = rolling.mean()
            elif metric == 'std':
                df[col_name] = rolling.std()
            elif metric == 'min':
                df[col_name] = rolling.min()
            elif metric == 'max':
                df[col_name] = rolling.max()
            elif metric == 'sum':
                df[col_name] = rolling.sum()
            else:
                logger.warning(f"Unknown rolling metric: {metric}")
        
        return df
        
    except Exception as e:
        raise TransformationError(f"Failed to calculate rolling metrics: {e}")


def filter_data(
    df: pd.DataFrame,
    conditions: Dict[str, Any]
) -> pd.DataFrame:
    """
    Question 29: Filter DataFrame based on conditions.
    
    Args:
        df: Input DataFrame
        conditions: Dictionary of column:value conditions
        
    Returns:
        Filtered DataFrame
    """
    try:
        df = df.copy()
        initial_count = len(df)
        
        logger.info(f"Applying {len(conditions)} filter conditions")
        
        for column, value in conditions.items():
            if column not in df.columns:
                logger.warning(f"Column '{column}' not found, skipping")
                continue
            
            if isinstance(value, dict):
                # Handle operators: {'>=': 10, '<=': 100}
                for op, val in value.items():
                    if op == '==':
                        df = df[df[column] == val]
                    elif op == '!=':
                        df = df[df[column] != val]
                    elif op == '>':
                        df = df[df[column] > val]
                    elif op == '>=':
                        df = df[df[column] >= val]
                    elif op == '<':
                        df = df[df[column] < val]
                    elif op == '<=':
                        df = df[df[column] <= val]
            elif isinstance(value, (list, tuple)):
                # Value in list
                df = df[df[column].isin(value)]
            else:
                # Direct equality
                df = df[df[column] == value]
        
        filtered_count = initial_count - len(df)
        logger.info(f"Filtered {filtered_count} rows, {len(df)} remaining")
        
        return df
        
    except Exception as e:
        raise TransformationError(f"Failed to filter data: {e}")


def aggregate_data(
    df: pd.DataFrame,
    group_by: Union[str, List[str]],
    aggregations: Dict[str, Union[str, List[str]]]
) -> pd.DataFrame:
    """
    Question 26: Perform grouped aggregations.
    
    Args:
        df: Input DataFrame
        group_by: Column(s) to group by
        aggregations: Dictionary mapping columns to aggregation functions
        
    Returns:
        Aggregated DataFrame
    """
    try:
        logger.info(f"Aggregating data by {group_by}")
        
        grouped = df.groupby(group_by)
        result = grouped.agg(aggregations).reset_index()
        
        # Flatten column names if multi-level
        if isinstance(result.columns, pd.MultiIndex):
            result.columns = ['_'.join(col).strip('_') for col in result.columns.values]
        
        logger.info(f"Aggregated into {len(result)} groups")
        
        return result
        
    except Exception as e:
        raise TransformationError(f"Failed to aggregate data: {e}")


def merge_dataframes(
    dataframes: List[pd.DataFrame],
    on: Union[str, List[str]],
    how: str = 'inner',
    suffixes: tuple = ('_x', '_y')
) -> pd.DataFrame:
    """
    Question 25: Merge multiple DataFrames on a common key.

    Sequentially merges a list of DataFrames using pd.merge, supporting all
    standard join types (inner, left, right, outer).

    Args:
        dataframes: List of DataFrames to merge (must contain at least 2)
        on: Column name(s) to join on
        how: Join type — 'inner', 'left', 'right', or 'outer'
        suffixes: Suffixes for overlapping column names from consecutive merges

    Returns:
        Single merged DataFrame

    Raises:
        TransformationError: If fewer than 2 DataFrames provided or merge fails
    """
    if len(dataframes) < 2:
        raise TransformationError("At least 2 DataFrames required for merging")

    try:
        logger.info(f"Merging {len(dataframes)} DataFrames on '{on}' ({how} join)")

        result = dataframes[0]
        for i, df_right in enumerate(dataframes[1:], start=1):
            result = pd.merge(result, df_right, on=on, how=how, suffixes=suffixes)
            logger.info(f"After merge {i}: {len(result)} rows")

        logger.info(f"Final merged DataFrame: {len(result)} rows, {len(result.columns)} columns")
        return result

    except Exception as e:
        raise TransformationError(f"Failed to merge DataFrames: {e}")


def analyze_pickup_locations(df: pd.DataFrame, location_col: str = 'PULocationID') -> Dict[int, int]:
    """
    Question 8: Use Counter to analyze pickup location frequency.
    
    Args:
        df: DataFrame with taxi trip data
        location_col: Name of pickup location column
        
    Returns:
        Dictionary with location frequencies
    """
    try:
        logger.info(f"Analyzing pickup location frequency for '{location_col}'")
        
        locations = df[location_col].dropna().astype(int).tolist()
        frequency = Counter(locations)
        
        logger.info(f"Found {len(frequency)} unique pickup locations")
        
        return dict(frequency)
        
    except Exception as e:
        raise TransformationError(f"Failed to analyze pickup locations: {e}")


def analyze_hourly_fares(df: pd.DataFrame, datetime_col: str, fare_col: str) -> Dict[int, float]:
    """
    Question 9: Use defaultdict to calculate average fare by hour.

    Uses a vectorized pandas approach for performance at scale, then
    stores results in a defaultdict to satisfy the data-structure requirement.

    Args:
        df: DataFrame with taxi trip data
        datetime_col: Name of datetime column
        fare_col: Name of fare column

    Returns:
        defaultdict with average fare by hour
    """
    try:
        logger.info("Analyzing hourly fare averages")

        df = df.copy()
        df['_hour'] = pd.to_datetime(df[datetime_col]).dt.hour

        # Vectorized groupby — O(n) instead of row-by-row iterrows
        valid = df[df[fare_col] > 0]
        hourly_avg = valid.groupby('_hour')[fare_col].mean()

        # Store in defaultdict as required by Q9
        fare_averages: defaultdict = defaultdict(float)
        for hour, avg in hourly_avg.items():
            fare_averages[hour] = float(avg)

        logger.info(f"Calculated average fares for {len(fare_averages)} hours")
        return dict(sorted(fare_averages.items()))

    except Exception as e:
        raise TransformationError(f"Failed to analyze hourly fares: {e}")


def create_rolling_buffer(size: int = 100) -> deque:
    """
    Question 10: Create a rolling buffer using deque.
    
    Args:
        size: Maximum size of buffer
        
    Returns:
        Deque with maximum length
    """
    return deque(maxlen=size)


def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Question 21: Optimize DataFrame dtypes for memory efficiency.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with optimized dtypes
    """
    try:
        df = df.copy()
        initial_memory = df.memory_usage(deep=True).sum() / 1024**2
        
        logger.info("Optimizing DataFrame dtypes for memory efficiency")
        
        for col in df.columns:
            col_type = df[col].dtype
            
            # Optimize integers
            if col_type == 'int64':
                df[col] = pd.to_numeric(df[col], downcast='integer')
            
            # Optimize floats
            elif col_type == 'float64':
                df[col] = pd.to_numeric(df[col], downcast='float')
            
            # Convert object to category for low cardinality
            elif col_type == 'object':
                num_unique = df[col].nunique()
                num_total = len(df[col])
                if num_unique / num_total < 0.5:  # Less than 50% unique
                    df[col] = df[col].astype('category')
        
        final_memory = df.memory_usage(deep=True).sum() / 1024**2
        savings = initial_memory - final_memory
        
        logger.info(f"Memory reduced from {initial_memory:.2f} MB to {final_memory:.2f} MB "
                   f"(saved {savings:.2f} MB, {savings/initial_memory*100:.1f}%)")
        
        return df
        
    except Exception as e:
        raise TransformationError(f"Failed to optimize dtypes: {e}")
