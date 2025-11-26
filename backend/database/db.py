import asyncpg
from contextlib import asynccontextmanager
from typing import Optional
import config

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                config.DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            print("✓ Database connection pool created")

            # Initialize schema if needed
            await self.initialize_schema()
        except Exception as e:
            print(f"✗ Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            print("✓ Database connection pool closed")

    async def initialize_schema(self):
        """Initialize database schema"""
        try:
            async with self.pool.acquire() as conn:
                # Check if pgvector extension exists
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )
                if not result:
                    print("⚠ pgvector extension not found. Please install it manually.")
                    print("  Run: CREATE EXTENSION vector;")
                else:
                    print("✓ pgvector extension is available")
        except Exception as e:
            print(f"⚠ Error checking database schema: {e}")

    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool"""
        async with self.pool.acquire() as conn:
            yield conn

    async def execute(self, query: str, *args):
        """Execute a query"""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Fetch all rows from a query"""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Fetch one row from a query"""
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Fetch a single value from a query"""
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *args)


# Global database instance
db = Database()
