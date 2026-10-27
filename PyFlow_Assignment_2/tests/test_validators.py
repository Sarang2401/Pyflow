"""
Tests for data validators.
Question 38: Test validators module.
"""

import pytest
import pandas as pd

from pyflow.validators import (
    TripRecord,
    deduplicate_records,
    SchemaValidator,
    DataQualityValidator,
    validate_taxi_data,
)
from pyflow.exceptions import SchemaValidationError, DataQualityError


def test_trip_record_equality():
    """Test TripRecord equality."""
    record1 = TripRecord(
        vendor_id=1,
        pickup_datetime='2024-01-01 08:00:00',
        dropoff_datetime='2024-01-01 08:30:00',
        pickup_location=100,
        dropoff_location=200,
        passenger_count=2.0,
        trip_distance=5.0,
        fare_amount=15.0
    )
    
    record2 = TripRecord(
        vendor_id=1,
        pickup_datetime='2024-01-01 08:00:00',
        dropoff_datetime='2024-01-01 08:30:00',
        pickup_location=100,
        dropoff_location=200,
        passenger_count=2.0,
        trip_distance=5.0,
        fare_amount=15.0
    )
    
    assert record1 == record2
    assert hash(record1) == hash(record2)


def test_trip_record_inequality():
    """Test TripRecord inequality."""
    record1 = TripRecord(
        vendor_id=1,
        pickup_datetime='2024-01-01 08:00:00',
        dropoff_datetime='2024-01-01 08:30:00',
        pickup_location=100,
        dropoff_location=200,
        passenger_count=2.0,
        trip_distance=5.0,
        fare_amount=15.0
    )
    
    record2 = TripRecord(
        vendor_id=1,
        pickup_datetime='2024-01-01 09:00:00',  # Different time
        dropoff_datetime='2024-01-01 09:30:00',
        pickup_location=100,
        dropoff_location=200,
        passenger_count=2.0,
        trip_distance=5.0,
        fare_amount=15.0
    )
    
    assert record1 != record2
    assert hash(record1) != hash(record2)


def test_deduplicate_records():
    """Test record deduplication."""
    record1 = TripRecord(1, '2024-01-01 08:00:00', '2024-01-01 08:30:00', 100, 200, 2.0, 5.0, 15.0)
    record2 = TripRecord(1, '2024-01-01 08:00:00', '2024-01-01 08:30:00', 100, 200, 2.0, 5.0, 15.0)
    record3 = TripRecord(1, '2024-01-01 09:00:00', '2024-01-01 09:30:00', 100, 200, 2.0, 5.0, 15.0)
    
    records = [record1, record2, record3]
    unique = deduplicate_records(records)
    
    assert len(unique) == 2  # record1 and record2 are duplicates


def test_schema_validator_valid():
    """Test schema validation with valid data."""
    df = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': [1.5, 2.5, 3.5],
        'col3': ['a', 'b', 'c']
    })
    
    schema = {
        'col1': int,
        'col2': float,
        'col3': str
    }
    
    validator = SchemaValidator(schema)
    validator.validate(df)  # Should not raise


def test_schema_validator_missing_column():
    """Test schema validation with missing column."""
    df = pd.DataFrame({
        'col1': [1, 2, 3]
    })
    
    schema = {
        'col1': int,
        'col2': float  # Missing in df
    }
    
    validator = SchemaValidator(schema)
    
    with pytest.raises(SchemaValidationError):
        validator.validate(df)


def test_data_quality_validator():
    """Test data quality validation."""
    df = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': [10, 20, 30]
    })
    
    validator = DataQualityValidator(
        required_columns=['col1', 'col2'],
        non_null_columns=['col1'],
        value_ranges={'col2': (0, 100)}
    )
    
    result = validator.validate(df)
    
    assert result['valid'] is True
    assert result['stats']['total_rows'] == 3


def test_data_quality_validator_with_nulls():
    """Test data quality validation with null values."""
    df = pd.DataFrame({
        'col1': [1, None, 3],
        'col2': [10, 20, 30]
    })
    
    validator = DataQualityValidator(
        required_columns=['col1', 'col2'],
        non_null_columns=['col1']
    )
    
    result = validator.validate(df)
    
    assert len(result['warnings']) > 0


def test_validate_taxi_data():
    """Test taxi data validation."""
    df = pd.DataFrame({
        'fare_amount': [10.0, -5.0, 20.0],  # -5.0 is invalid
        'trip_distance': [2.0, 3.0, 4.0],
        'passenger_count': [2.0, 0.0, 3.0],  # 0.0 is invalid
        'tpep_pickup_datetime': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']),
        'tpep_dropoff_datetime': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03'])
    })
    
    result = validate_taxi_data(df)
    
    assert len(result) < len(df)  # Some rows should be removed
