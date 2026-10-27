"""
Main ETL pipeline orchestration.
Question 35: Orchestration workflow for extraction, validation, transformation, and loading.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from pyflow.exceptions import PyFlowException
from pyflow.utils import load_config, timing_decorator, setup_logging
from pyflow.extractors import get_extractor
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
from pyflow.loaders import get_loader, SQLiteLoader
from pyflow.validators import (
    SchemaValidator,
    DataQualityValidator,
    validate_taxi_data,
)

logger = logging.getLogger(__name__)


class ETLPipeline:
    """
    Question 35: Main ETL pipeline orchestrator.
    Coordinates extraction, validation, transformation, and loading.
    """
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Initialize ETL pipeline.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.df: Optional[pd.DataFrame] = None
        self.stats: Dict[str, Any] = {}
        
        # Setup logging
        log_config = self.config.get('logging', {})
        setup_logging(
            log_file=log_config.get('file', 'logs/pyflow.log'),
            level=getattr(logging, log_config.get('level', 'INFO')),
            max_bytes=log_config.get('max_bytes', 10485760),
            backup_count=log_config.get('backup_count', 5)
        )
        
        logger.info(f"Initialized pipeline: {self.config['pipeline']['name']}")
    
    @timing_decorator
    def extract(self) -> pd.DataFrame:
        """
        Extract data from source.
        
        Returns:
            Extracted DataFrame
        """
        logger.info("=" * 80)
        logger.info("EXTRACTION PHASE")
        logger.info("=" * 80)
        
        extract_config = self.config['extraction']
        source_file = extract_config['source_file']
        
        # Get appropriate extractor
        extractor = get_extractor(
            source_file,
            file_type=extract_config.get('file_type'),
            columns=extract_config.get('columns'),
            chunk_size=extract_config.get('chunk_size'),
            sample_size=extract_config.get('sample_size')
        )
        
        # Extract data
        self.df = extractor.extract()
        
        # Store initial stats
        self.stats['initial_rows'] = len(self.df)
        self.stats['initial_columns'] = len(self.df.columns)
        self.stats['initial_memory_mb'] = self.df.memory_usage(deep=True).sum() / 1024**2
        
        logger.info(f"Extracted {self.stats['initial_rows']} rows, "
                   f"{self.stats['initial_columns']} columns, "
                   f"{self.stats['initial_memory_mb']:.2f} MB")
        
        return self.df
    
    @timing_decorator
    def validate(self) -> None:
        """Validate data quality and schema."""
        logger.info("=" * 80)
        logger.info("VALIDATION PHASE")
        logger.info("=" * 80)
        
        if self.df is None:
            raise PyFlowException("No data to validate. Run extract() first.")
        
        validation_config = self.config.get('validation', {})
        
        # Data quality validation
        validator = DataQualityValidator(
            required_columns=validation_config.get('required_columns', []),
            non_null_columns=validation_config.get('non_null_columns', []),
            value_ranges=validation_config.get('value_ranges', {})
        )
        
        validation_results = validator.validate(self.df)
        self.stats['validation'] = validation_results
        
        # Business rule validation for taxi data
        self.df = validate_taxi_data(self.df)
        
        self.stats['rows_after_validation'] = len(self.df)
        logger.info(f"Validation complete: {len(self.df)} valid rows")
    
    @timing_decorator
    def transform(self) -> None:
        """Transform data according to configuration."""
        logger.info("=" * 80)
        logger.info("TRANSFORMATION PHASE")
        logger.info("=" * 80)
        
        if self.df is None:
            raise PyFlowException("No data to transform. Run extract() first.")
        
        transform_config = self.config['transformation']
        
        # Convert datetime columns
        datetime_cols = transform_config.get('datetime_columns', [])
        if datetime_cols:
            self.df = convert_datetime(self.df, datetime_cols)
        
        # Handle missing values
        missing_config = transform_config.get('missing_values', {})
        if missing_config:
            self.df = handle_missing_values(
                self.df,
                strategy=missing_config.get('strategy', 'drop'),
                fill_value=missing_config.get('fill_value'),
                columns=missing_config.get('columns')
            )
        
        # Remove duplicates
        dup_config = transform_config.get('duplicates', {})
        if dup_config.get('enabled', False):
            self.df = remove_duplicates(self.df, keep=dup_config.get('keep', 'first'))
        
        # Remove outliers
        outlier_config = transform_config.get('outliers', {})
        if outlier_config.get('enabled', False):
            self.df = remove_outliers(
                self.df,
                columns=outlier_config.get('columns', []),
                method=outlier_config.get('method', 'iqr'),
                threshold=outlier_config.get('threshold', 1.5)
            )
        
        # Apply filters
        filters = transform_config.get('filters', {})
        if filters:
            self.df = filter_data(self.df, filters)
        
        # Optimize data types
        self.df = optimize_dtypes(self.df)
        
        # Add derived columns
        if 'tpep_pickup_datetime' in self.df.columns:
            self.df['hour'] = self.df['tpep_pickup_datetime'].dt.hour
            self.df['day_of_week'] = self.df['tpep_pickup_datetime'].dt.dayofweek
            self.df['date'] = self.df['tpep_pickup_datetime'].dt.date
        
        self.stats['rows_after_transform'] = len(self.df)
        self.stats['final_memory_mb'] = self.df.memory_usage(deep=True).sum() / 1024**2
        
        logger.info(f"Transformation complete: {len(self.df)} rows, "
                   f"{self.stats['final_memory_mb']:.2f} MB")
    
    @timing_decorator
    def analyze(self) -> Dict[str, Any]:
        """Perform analysis and generate insights."""
        logger.info("=" * 80)
        logger.info("ANALYSIS PHASE")
        logger.info("=" * 80)
        
        if self.df is None:
            raise PyFlowException("No data to analyze. Run pipeline first.")
        
        analysis = {}
        
        # Basic statistics
        analysis['total_trips'] = len(self.df)
        analysis['total_revenue'] = self.df['fare_amount'].sum()
        analysis['avg_fare'] = self.df['fare_amount'].mean()
        analysis['avg_distance'] = self.df['trip_distance'].mean()
        analysis['avg_passengers'] = self.df['passenger_count'].mean()
        
        # Pickup location analysis (Question 8: Counter)
        analysis['pickup_locations'] = analyze_pickup_locations(self.df)
        analysis['top_pickup_locations'] = dict(sorted(
            analysis['pickup_locations'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])
        
        # Hourly fare analysis (Question 9: defaultdict)
        analysis['hourly_fares'] = analyze_hourly_fares(
            self.df,
            'tpep_pickup_datetime',
            'fare_amount'
        )
        
        self.stats['analysis'] = analysis
        
        logger.info(f"Analysis complete: {analysis['total_trips']} trips, "
                   f"${analysis['total_revenue']:.2f} total revenue")
        
        return analysis
    
    @timing_decorator
    def load(self) -> None:
        """Load data to configured destinations."""
        logger.info("=" * 80)
        logger.info("LOADING PHASE")
        logger.info("=" * 80)
        
        if self.df is None:
            raise PyFlowException("No data to load. Run pipeline first.")
        
        load_config = self.config['loading']
        outputs = load_config.get('outputs', {})
        
        # Load to files
        for name, path in outputs.items():
            if path:
                try:
                    loader = get_loader(path)
                    loader.load(self.df)
                except Exception as e:
                    logger.error(f"Failed to load {name}: {e}")
        
        # Load aggregations
        agg_config = self.config.get('aggregation', {})
        
        if 'hourly_stats' in agg_config:
            hourly_config = agg_config['hourly_stats']
            hourly_df = aggregate_data(
                self.df,
                hourly_config['group_by'],
                hourly_config['metrics']
            )
            
            hourly_path = outputs.get('hourly_stats')
            if hourly_path:
                hourly_df.to_csv(hourly_path, index=False)
                logger.info(f"Saved hourly stats to {hourly_path}")
        
        if 'location_stats' in agg_config:
            location_config = agg_config['location_stats']
            location_df = aggregate_data(
                self.df,
                location_config['group_by'],
                location_config['metrics']
            )
            
            location_path = outputs.get('location_stats')
            if location_path:
                location_df.to_csv(location_path, index=False)
                logger.info(f"Saved location stats to {location_path}")
        
        # Load to database
        db_config = load_config.get('database', {})
        if db_config.get('enabled', False):
            db_loader = SQLiteLoader(
                db_path=db_config.get('path', 'data/output/pyflow.db'),
                table_name=db_config.get('table_name', 'taxi_trips'),
                if_exists=db_config.get('if_exists', 'replace')
            )
            
            # Load sample of data to database (limit for demo)
            sample_df = self.df.head(10000) if len(self.df) > 10000 else self.df
            db_loader.load(sample_df)
        
        logger.info("Loading complete")
    
    @timing_decorator
    def run(self) -> Dict[str, Any]:
        """
        Run complete ETL pipeline.
        
        Returns:
            Dictionary with pipeline statistics
        """
        try:
            logger.info("=" * 80)
            logger.info(f"Starting pipeline: {self.config['pipeline']['name']}")
            logger.info("=" * 80)
            
            # Execute pipeline phases
            self.extract()
            self.validate()
            self.transform()
            analysis = self.analyze()
            self.load()
            
            # Compile final statistics
            self.stats['status'] = 'SUCCESS'
            self.stats['final_rows'] = len(self.df)
            
            logger.info("=" * 80)
            logger.info("PIPELINE COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Status: {self.stats['status']}")
            logger.info(f"Initial rows: {self.stats['initial_rows']}")
            logger.info(f"Final rows: {self.stats['final_rows']}")
            logger.info(f"Memory reduction: {self.stats['initial_memory_mb']:.2f} MB -> "
                       f"{self.stats['final_memory_mb']:.2f} MB")
            
            return self.stats
            
        except Exception as e:
            self.stats['status'] = 'FAILED'
            self.stats['error'] = str(e)
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise
