"""
Database connection and operations.
Question 6: Context manager for database connections.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Any, List, Tuple
from types import TracebackType

from pyflow.exceptions import LoadingError

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Question 6: Context manager for SQLite database connections.
    Automatically handles connection opening, commit, and cleanup.
    """
    
    def __init__(self, db_path: str = "data/output/pyflow.db"):
        """
        Initialize database connection context manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
    
    def __enter__(self) -> 'DatabaseConnection':
        """
        Enter context: open database connection.
        
        Returns:
            Self for use in with statement
        """
        try:
            # Ensure directory exists
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Open connection
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            
            logger.info(f"Database connection opened: {self.db_path}")
            return self
            
        except Exception as e:
            raise LoadingError(f"Failed to connect to database {self.db_path}: {e}")
    
    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> bool:
        """
        Exit context: commit changes and close connection.
        
        Args:
            exc_type: Exception type if error occurred
            exc_val: Exception value if error occurred
            exc_tb: Exception traceback if error occurred
            
        Returns:
            False to propagate exceptions
        """
        try:
            if exc_type is None and self.connection:
                # No exception: commit
                self.connection.commit()
                logger.info("Database changes committed")
            elif self.connection:
                # Exception occurred: rollback
                self.connection.rollback()
                logger.warning("Database transaction rolled back due to error")
        finally:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
                logger.info("Database connection closed")
        
        return False  # Propagate exceptions
    
    def execute(self, query: str, params: Optional[Tuple] = None) -> sqlite3.Cursor:
        """
        Execute a SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            Cursor with results
            
        Raises:
            LoadingError: If query execution fails
        """
        if not self.cursor:
            raise LoadingError("Database connection not initialized")
        
        try:
            if params:
                return self.cursor.execute(query, params)
            else:
                return self.cursor.execute(query)
        except Exception as e:
            raise LoadingError(f"Query execution failed: {e}")
    
    def executemany(self, query: str, params_list: List[Tuple]) -> None:
        """
        Execute a SQL query with multiple parameter sets.
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Raises:
            LoadingError: If query execution fails
        """
        if not self.cursor:
            raise LoadingError("Database connection not initialized")
        
        try:
            self.cursor.executemany(query, params_list)
        except Exception as e:
            raise LoadingError(f"Batch query execution failed: {e}")
    
    def fetchall(self) -> List[Tuple[Any, ...]]:
        """
        Fetch all results from the last query.
        
        Returns:
            List of result tuples
        """
        if not self.cursor:
            raise LoadingError("Database connection not initialized")
        return self.cursor.fetchall()
    
    def fetchone(self) -> Optional[Tuple[Any, ...]]:
        """
        Fetch one result from the last query.
        
        Returns:
            Result tuple or None
        """
        if not self.cursor:
            raise LoadingError("Database connection not initialized")
        return self.cursor.fetchone()
    
    def create_table(
        self,
        table_name: str,
        schema: str,
        drop_if_exists: bool = False
    ) -> None:
        """
        Create a table with the given schema.
        
        Args:
            table_name: Name of the table
            schema: SQL schema definition
            drop_if_exists: Whether to drop existing table
            
        Raises:
            LoadingError: If table creation fails
        """
        try:
            if drop_if_exists:
                self.execute(f"DROP TABLE IF EXISTS {table_name}")
                logger.info(f"Dropped existing table: {table_name}")
            
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
            self.execute(create_sql)
            logger.info(f"Table created: {table_name}")
            
        except Exception as e:
            raise LoadingError(f"Failed to create table {table_name}: {e}")
