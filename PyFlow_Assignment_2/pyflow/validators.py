"""
Data validation module.
Question 40: Schema and data quality validation.
Question 12: TripRecord class with equality and hashing.
"""

import logging
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from collections import namedtuple

import pandas as pd

from pyflow.exceptions import ValidationError, SchemaValidationError, DataQualityError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TripRecord:
    """
    Question 12: Trip record class with defined equality and hashing.
    Immutable dataclass for trip records with proper equality and hash implementation.
    """
    vendor_id: int
    pickup_datetime: str
    dropoff_datetime: str
    pickup_location: int
    dropoff_location: int
    passenger_count: float
    trip_distance: float
    fare_amount: float
    
    def __eq__(self, other: object) -> bool:
        """
        Define equality based on key fields.
        Two trips are equal if they have same pickup/dropoff time and locations.
        """
        if not isinstance(other, TripRecord):
            return NotImplemented
        
        return (
            self.pickup_datetime == other.pickup_datetime and
            self.dropoff_datetime == other.dropoff_datetime and
            self.pickup_location == other.pickup_location and
            self.dropoff_location == other.dropoff_location
        )
    
    def __hash__(self) -> int:
        """
        Define hash based on key fields used in equality.
        """
        return hash((
            self.pickup_datetime,
            self.dropoff_datetime,
            self.pickup_location,
            self.dropoff_location
        ))


def deduplicate_records(records: List[TripRecord]) -> List[TripRecord]:
    """
    Question 12: Deduplicate trip records using set.
    
    Args:
        records: List of trip records
        
    Returns:
        List of unique records
    """
    logger.info(f"Deduplicating {len(records)} trip records")
    
    unique_records = list(set(records))
    
    duplicates_removed = len(records) - len(unique_records)
    logger.info(f"Removed {duplicates_removed} duplicate records")
    
    return unique_records


class SchemaValidator:
    """
    Question 40a: Schema validation.
    Validates DataFrame schema against expected structure.
    """
    
    def __init__(self, expected_schema: Dict[str, type]):
        """
        Initialize schema validator.
        
        Args:
            expected_schema: Dictionary mapping column names to expected types
        """
        self.expected_schema = expected_schema
    
    def validate(self, df: pd.DataFrame) -> None:
        """
        Validate DataFrame schema.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            SchemaValidationError: If schema doesn't match
        """
        logger.info("Validating DataFrame schema")
        
        errors = []
        
        # Check for missing columns
        expected_cols = set(self.expected_schema.keys())
        actual_cols = set(df.columns)
        missing_cols = expected_cols - actual_cols
        
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        # Check data types
        for col, expected_type in self.expected_schema.items():
            if col in df.columns:
                actual_type = df[col].dtype
                
                # Type compatibility check
                if expected_type == int and not pd.api.types.is_integer_dtype(actual_type):
                    errors.append(f"Column '{col}': expected integer, got {actual_type}")
                elif expected_type == float and not pd.api.types.is_numeric_dtype(actual_type):
                    errors.append(f"Column '{col}': expected float, got {actual_type}")
                elif expected_type == str and actual_type not in ['object', 'string']:
                    errors.append(f"Column '{col}': expected string, got {actual_type}")
        
        if errors:
            raise SchemaValidationError(f"Schema validation failed:\n" + "\n".join(errors))
        
        logger.info("Schema validation passed")


class DataQualityValidator:
    """
    Question 40b: Data quality validation.
    Validates data quality rules and business constraints.
    """
    
    def __init__(
        self,
        required_columns: Optional[List[str]] = None,
        non_null_columns: Optional[List[str]] = None,
        value_ranges: Optional[Dict[str, tuple]] = None,
        custom_rules: Optional[List] = None
    ):
        """
        Initialize data quality validator.
        
        Args:
            required_columns: Columns that must exist
            non_null_columns: Columns that cannot have null values
            value_ranges: Dictionary mapping columns to (min, max) ranges
            custom_rules: List of custom validation functions
        """
        self.required_columns = required_columns or []
        self.non_null_columns = non_null_columns or []
        self.value_ranges = value_ranges or {}
        self.custom_rules = custom_rules or []
    
    def validate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate data quality.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dictionary with validation results
            
        Raises:
            DataQualityError: If critical validation fails
        """
        logger.info("Validating data quality")
        
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        # Check required columns
        missing_cols = set(self.required_columns) - set(df.columns)
        if missing_cols:
            results['valid'] = False
            results['errors'].append(f"Missing required columns: {missing_cols}")
        
        # Check null constraints
        for col in self.non_null_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    results['warnings'].append(
                        f"Column '{col}' has {null_count} null values "
                        f"({null_count/len(df)*100:.2f}%)"
                    )
        
        # Check value ranges
        for col, (min_val, max_val) in self.value_ranges.items():
            if col in df.columns:
                out_of_range = df[(df[col] < min_val) | (df[col] > max_val)]
                if len(out_of_range) > 0:
                    results['warnings'].append(
                        f"Column '{col}' has {len(out_of_range)} values out of range "
                        f"[{min_val}, {max_val}]"
                    )
        
        # Calculate stats
        results['stats']['total_rows'] = len(df)
        results['stats']['total_columns'] = len(df.columns)
        results['stats']['missing_values'] = df.isnull().sum().sum()
        results['stats']['duplicate_rows'] = df.duplicated().sum()
        
        # Log results
        if results['valid']:
            logger.info("Data quality validation passed")
        else:
            logger.error(f"Data quality validation failed: {results['errors']}")
        
        if results['warnings']:
            for warning in results['warnings']:
                logger.warning(warning)
        
        if not results['valid']:
            raise DataQualityError(
                f"Data quality validation failed:\n" + "\n".join(results['errors'])
            )
        
        return results


def validate_taxi_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Question 40: Validate taxi trip data with business rules.
    
    Args:
        df: DataFrame with taxi trip data
        
    Returns:
        Validated DataFrame (with invalid rows removed)
    """
    logger.info(f"Validating taxi data: {len(df)} rows")
    
    initial_count = len(df)
    df = df.copy()
    
    # Remove rows with invalid fares
    df = df[df['fare_amount'] >= 0]
    
    # Remove rows with invalid distances
    df = df[df['trip_distance'] >= 0]
    
    # Remove rows with invalid passenger counts
    df = df[df['passenger_count'] > 0]
    
    # Remove rows with pickup after dropoff
    df = df[df['tpep_pickup_datetime'] <= df['tpep_dropoff_datetime']]
    
    removed = initial_count - len(df)
    if removed > 0:
        logger.warning(f"Removed {removed} invalid rows ({removed/initial_count*100:.2f}%)")
    
    logger.info(f"Validation complete: {len(df)} valid rows")
    
    return df


def validate_covid_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate COVID-19 county data.
    
    Args:
        df: DataFrame with COVID data
        
    Returns:
        Validated DataFrame
    """
    logger.info(f"Validating COVID data: {len(df)} rows")
    
    initial_count = len(df)
    df = df.copy()
    
    # Remove rows with negative cases or deaths
    df = df[df['cases'] >= 0]
    df = df[df['deaths'] >= 0]
    
    # Remove rows where deaths > cases
    df = df[df['deaths'] <= df['cases']]
    
    removed = initial_count - len(df)
    if removed > 0:
        logger.warning(f"Removed {removed} invalid rows")
    
    logger.info(f"Validation complete: {len(df)} valid rows")
    
    return df


def validate_gdp_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate GDP data.
    
    Args:
        df: DataFrame with GDP data
        
    Returns:
        Validated DataFrame
    """
    logger.info(f"Validating GDP data: {len(df)} rows")
    
    initial_count = len(df)
    df = df.copy()
    
    # Remove rows with invalid values
    df = df[df['Value'] > 0]
    
    # Remove rows with invalid years
    df = df[(df['Year'] >= 1960) & (df['Year'] <= 2030)]
    
    removed = initial_count - len(df)
    if removed > 0:
        logger.warning(f"Removed {removed} invalid rows")
    
    logger.info(f"Validation complete: {len(df)} valid rows")
    
    return df
