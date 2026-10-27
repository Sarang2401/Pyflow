"""
Tests for data transformers.
Question 38: Test transformers module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from pyflow.transformers import (
    handle_missing_values,
    remove_outliers,
    remove_duplicates,
    convert_datetime,
    filter_data,
    aggregate_data,
    analyze_pickup_locations,
    analyze_hourly_fares,
    optimize_dtypes,
)
from pyflow.exceptions import TransformationError


def test_handle_missing_values_drop():
    """Test missing value handling with drop strategy."""
    df = pd.DataFrame({
        'a': [1, 2, None, 4],
        'b': [5, None, 7, 8]
    })
    
    result = handle_missing_values(df, strategy='drop')
    
    assert len(result) == 2  # Only rows without nulls


def test_handle_missing_values_fill():
    """Test missing value handling with fill strategy."""
    df = pd.DataFrame({
        'a': [1, 2, None, 4],
        'b': [5, None, 7, 8]
    })
    
    result = handle_missing_values(df, strategy='fill', fill_value=0)
    
    assert result['a'].isnull().sum() == 0
    assert result['b'].isnull().sum() == 0
    assert result['a'].tolist() == [1, 2, 0, 4]


def test_handle_missing_values_mean():
    """Test missing value handling with mean strategy."""
    df = pd.DataFrame({
        'a': [1.0, 2.0, None, 4.0],
    })
    
    result = handle_missing_values(df, strategy='mean')
    
    assert result['a'].isnull().sum() == 0
    # Mean of [1, 2, 4] is 2.33...
    assert 2.0 < result['a'].iloc[2] < 2.5


def test_remove_outliers_iqr():
    """Test outlier removal using IQR method."""
    df = pd.DataFrame({
        'value': [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]  # 100 is outlier
    })
    
    result = remove_outliers(df, columns=['value'], method='iqr', threshold=1.5)
    
    assert len(result) < len(df)
    assert result['value'].max() < 100


def test_remove_duplicates():
    """Test duplicate removal."""
    df = pd.DataFrame({
        'a': [1, 1, 2, 3],
        'b': [4, 4, 5, 6]
    })
    
    result = remove_duplicates(df)
    
    assert len(result) == 3


def test_convert_datetime():
    """Test datetime conversion."""
    df = pd.DataFrame({
        'date': ['2024-01-01', '2024-01-02', '2024-01-03']
    })
    
    result = convert_datetime(df, columns=['date'])
    
    assert pd.api.types.is_datetime64_any_dtype(result['date'])


def test_convert_datetime_invalid():
    """Test datetime conversion with invalid dates."""
    df = pd.DataFrame({
        'date': ['2024-01-01', 'invalid', '2024-01-03']
    })
    
    result = convert_datetime(df, columns=['date'], errors='coerce')
    
    assert pd.isna(result['date'].iloc[1])


def test_filter_data():
    """Test data filtering."""
    df = pd.DataFrame({
        'value': [1, 2, 3, 4, 5],
        'category': ['A', 'B', 'A', 'B', 'A']
    })
    
    result = filter_data(df, {'value': {'>=': 3}})
    
    assert len(result) == 3
    assert result['value'].min() >= 3


def test_aggregate_data():
    """Test data aggregation."""
    df = pd.DataFrame({
        'category': ['A', 'A', 'B', 'B'],
        'value': [1, 2, 3, 4]
    })
    
    result = aggregate_data(
        df,
        group_by='category',
        aggregations={'value': ['mean', 'sum']}
    )
    
    assert len(result) == 2
    assert 'category' in result.columns


def test_analyze_pickup_locations():
    """Test pickup location frequency analysis."""
    df = pd.DataFrame({
        'PULocationID': [1, 2, 1, 3, 1, 2]
    })
    
    result = analyze_pickup_locations(df)
    
    assert result[1] == 3
    assert result[2] == 2
    assert result[3] == 1


def test_analyze_hourly_fares():
    """Test hourly fare analysis."""
    df = pd.DataFrame({
        'tpep_pickup_datetime': pd.to_datetime([
            '2024-01-01 08:00:00',
            '2024-01-01 08:30:00',
            '2024-01-01 09:00:00',
        ]),
        'fare_amount': [10.0, 20.0, 15.0]
    })
    
    result = analyze_hourly_fares(df, 'tpep_pickup_datetime', 'fare_amount')
    
    assert 8 in result
    assert 9 in result
    assert result[8] == 15.0  # Average of 10 and 20


def test_optimize_dtypes():
    """Test dtype optimization."""
    df = pd.DataFrame({
        'int_col': [1, 2, 3],
        'float_col': [1.0, 2.0, 3.0],
        'str_col': ['a', 'b', 'a']
    })
    
    # Convert to inefficient types
    df['int_col'] = df['int_col'].astype('int64')
    df['float_col'] = df['float_col'].astype('float64')
    
    initial_memory = df.memory_usage(deep=True).sum()
    
    result = optimize_dtypes(df)
    
    final_memory = result.memory_usage(deep=True).sum()
    
    # Should use less memory or same
    assert final_memory <= initial_memory
