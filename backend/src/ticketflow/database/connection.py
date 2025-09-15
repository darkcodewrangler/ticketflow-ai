"""
PyTiDB Connection Manager for TicketFlow AI
Handles database connections and table initialization
"""

from pytidb import TiDBClient,Table
from typing import Optional, Dict, Any
import logging
from ticketflow.config import config
from ticketflow.database.models import APIKey, Settings, Ticket, KnowledgeBaseArticle, AgentWorkflow, PerformanceMetrics, ProcessingTask, LearningMetrics

logger = logging.getLogger(__name__)

class PyTiDBManager:
    """
    Manages PyTiDB connections and table operations
    Much simpler than SQLAlchemy - no session management needed!
    """
    
    def __init__(self):
        self.client: Optional[TiDBClient] = None
        self.tables: Dict[str, Any] = {}
        self._connected = False
    def connect(self) -> bool:
        """
        Connect to TiDB using PyTiDB client
        Returns True if successful, False otherwise
        """
        try:
            self.client = TiDBClient.connect(
                host=config.TIDB_HOST,
                port=config.TIDB_PORT,
                username=config.TIDB_USER,
                password=config.TIDB_PASSWORD,
                database=config.TIDB_DATABASE,
                ensure_db=True,  # Creates database if it doesn't exist
                
            )
            # Test connection
            self.client.execute("SELECT 1")
            logger.info("PyTiDB connection successful!")
            self.client.configure_embedding_provider(provider='jina_ai', api_key=config.JINA_API_KEY)
            self._connected = True
        
            return True
            
        except Exception as e:
            logger.error(f"PyTiDB connection failed: {e}")
            self._connected = False
            return False
    def drop_db(self) -> bool:
        """
        Drop the entire database - use with caution!
        """
        if not self._connected or not self.client:
            raise Exception("Not connected to database. Call connect() first.")
        
        try:
            if self.client.has_database(f"{config.TIDB_DATABASE}"):
               self.client.drop_database(f"{config.TIDB_DATABASE}")
            logger.info(f"Database '{config.TIDB_DATABASE}' dropped successfully!")
         
            return True
        except Exception as e:
            logger.error(f"Failed to drop database: {e}")
            return False
    def create_db(self) -> bool:
        """
        Create the database if it doesn't exist
        """
        if not self._connected or not self.client:
            raise Exception("Not connected to database. Call connect() first.")
        
        try:
            if not self.client.has_database(f"{config.TIDB_DATABASE}"):
               self.client.create_database(f"{config.TIDB_DATABASE}")
               self.client.use_database (f"{config.TIDB_DATABASE}")
            logger.info(f"Database '{config.TIDB_DATABASE}' created successfully!")
            return True
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False
    def initialize_tables(self, drop_existing: bool = False) -> bool:
        """
        Initialize all tables with PyTiDB models
        
        Args:
            drop_existing: If True, drops existing tables (useful for development)
        """
        if not self._connected or not self.client:
            raise Exception("Not connected to database. Call connect() first.")
        
        try:
            # Determine table creation mode
            if_exists_mode = "overwrite" if drop_existing else "skip"
            
            # Create tables - PyTiDB handles schema creation automatically!
            print("Creating Tickets table with auto-embeddings...")
            self.tables['tickets'] = self.client.create_table(
                schema=Ticket, 
                if_exists=if_exists_mode
            )
            
            print("Creating Knowledge Base table with auto-embeddings...")
            self.tables['kb_articles'] = self.client.create_table(
                schema=KnowledgeBaseArticle,
                if_exists=if_exists_mode
            )
            
            print("Creating Agent Workflows table...")
            self.tables['agent_workflows'] = self.client.create_table(
                schema=AgentWorkflow,
                if_exists=if_exists_mode
            )
            
            print("Creating Performance Metrics table...")
            self.tables['performance_metrics'] = self.client.create_table(
                schema=PerformanceMetrics,
                if_exists=if_exists_mode
            )
            
            print("Creating Processing Tasks table...")
            self.tables['processing_tasks'] = self.client.create_table(
                schema=ProcessingTask,
                if_exists=if_exists_mode
            )
            print("Creating Settings table...")
            self.tables['settings'] = self.client.create_table(
                schema=Settings,
                if_exists=if_exists_mode
            )
            print("Creating API Keys table...")
            self.tables['api_keys'] = self.client.create_table(
                schema=APIKey,
                if_exists=if_exists_mode
            )
            
            print("Creating Learning Metrics table...")
            self.tables['learning_metrics'] = self.client.create_table(
                schema=LearningMetrics,
                if_exists=if_exists_mode
            )
            
            logger.info("All tables initialized successfully!")
            
            # Log the amazing features we just got for free
            print("\n🤖 PyTiDB AI Features Enabled:")
            print("Automatic embedding generation for text fields")
            print("Built-in vector similarity search")
            print("Hybrid search (vector + full-text)")
            print("Automatic result reranking")
            print("Optimized vector indexing")
            
            return True
            
        except Exception as e:
            logger.error(f"Table initialization failed: {e}")
            return False

    def get_table(self, table_name: str) -> Table:
        """Get a table instance for operations"""
        if self.client.has_table(table_name) or not table_name in self.tables:
           self.tables[table_name] = self.client.open_table(table_name)
        # elif table_name not in self.tables:
        #     raise ValueError(f"Table '{table_name}' not initialized")
        else:
            raise ValueError(f"Table '{table_name}' not found")
        return self.tables[table_name]
        
    
    @property
    def tickets(self):
        """Quick access to tickets table"""
        return self.get_table('tickets')
    
    @property
    def kb_articles(self):
        """Quick access to knowledge base table"""
        return self.get_table('kb_articles')
    
    @property
    def agent_workflows(self):
        """Quick access to workflows table"""
        return self.get_table('agent_workflows')
    
    @property
    def performance_metrics(self):
        """Quick access to metrics table"""
        return self.get_table('performance_metrics')
    
    @property
    def processing_tasks(self):
        """Quick access to processing tasks table"""
        return self.get_table('processing_tasks')
    
    @property
    def settings(self):
        """Quick access to settings table"""
        return self.get_table('settings')
    
    @property
    def api_keys(self):
        """Quick access to api keys table"""
        return self.get_table('api_keys')
    
    @property
    def learning_metrics(self):
        """Quick access to learning metrics table"""
        return self.get_table('learning_metrics')
    
    def close(self):
        """Close database connection"""
        if self.client:
            # PyTiDB handles cleanup automatically
            self._connected = False
            logger.info("Database connection closed")

# Global PyTiDB manager instance
db_manager = PyTiDBManager()