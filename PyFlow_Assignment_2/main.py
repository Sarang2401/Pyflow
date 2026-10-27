"""
Main entry point for PyFlow ETL pipeline.
Run the complete taxi data ETL pipeline.
"""

import sys
import logging
from pathlib import Path

from pyflow.pipeline import ETLPipeline
from pyflow.exceptions import PyFlowException
from pyflow.utils import setup_logging

logger = logging.getLogger(__name__)


def main(config_path: str = "config/config.json") -> int:
    """
    Run the ETL pipeline.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        print("=" * 80)
        print("PyFlow - Python Data Engineering Assignment 2")
        print("NYC Taxi Trip Data ETL Pipeline")
        print("=" * 80)
        print()
        
        # Check if config file exists
        if not Path(config_path).exists():
            print(f"Error: Configuration file not found: {config_path}")
            print("Please ensure config file exists before running pipeline.")
            return 1
        
        print(f"Configuration: {config_path}")
        print("Starting pipeline...")
        print()
        
        # Initialize and run pipeline
        pipeline = ETLPipeline(config_path=config_path)
        stats = pipeline.run()
        
        # Print summary
        print()
        print("=" * 80)
        print("PIPELINE SUMMARY")
        print("=" * 80)
        print(f"Status: {stats['status']}")
        print(f"Initial rows: {stats['initial_rows']:,}")
        print(f"Final rows: {stats['final_rows']:,}")
        print(f"Rows removed: {stats['initial_rows'] - stats['final_rows']:,}")
        print(f"Memory: {stats['initial_memory_mb']:.2f} MB -> {stats['final_memory_mb']:.2f} MB")
        
        if 'analysis' in stats:
            analysis = stats['analysis']
            print()
            print("ANALYSIS RESULTS")
            print("-" * 80)
            print(f"Total trips: {analysis['total_trips']:,}")
            print(f"Total revenue: ${analysis['total_revenue']:,.2f}")
            print(f"Average fare: ${analysis['avg_fare']:.2f}")
            print(f"Average distance: {analysis['avg_distance']:.2f} miles")
            print(f"Average passengers: {analysis['avg_passengers']:.2f}")
            
            print()
            print("Top 5 Pickup Locations:")
            for loc_id, count in list(analysis['top_pickup_locations'].items())[:5]:
                print(f"  Location {loc_id}: {count:,} trips")
        
        print()
        print("Output files:")
        print("  - data/output/trips_processed.csv")
        print("  - data/output/trips_processed.parquet")
        print("  - data/output/trip_summary.json")
        print("  - data/output/hourly_stats.csv")
        print("  - data/output/location_stats.csv")
        print("  - data/output/pyflow.db (SQLite database)")
        print()
        print("Logs: logs/pyflow.log")
        print()
        print("=" * 80)
        print("Pipeline completed successfully!")
        print("=" * 80)
        
        return 0
        
    except PyFlowException as e:
        logger.error(f"Pipeline error: {e}")
        print()
        print("=" * 80)
        print(f"ERROR: {e}")
        print("=" * 80)
        print("Check logs/pyflow.log for details")
        return 1
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print()
        print("=" * 80)
        print(f"UNEXPECTED ERROR: {e}")
        print("=" * 80)
        print("Check logs/pyflow.log for details")
        return 1


if __name__ == "__main__":
    # Parse command line arguments
    config_path = "config/config.json"
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("Usage: python main.py [config_path]")
            print()
            print("Arguments:")
            print("  config_path    Path to configuration file (default: config/config.json)")
            print()
            print("Examples:")
            print("  python main.py")
            print("  python main.py config/config.yaml")
            sys.exit(0)
        else:
            config_path = sys.argv[1]
    
    sys.exit(main(config_path))
