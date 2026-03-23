"""PostgreSQL-backed dbms.query / dbms.update implementation."""

from postgresdb.impl import PostgresDbBackend, build_handlers

__all__ = ["PostgresDbBackend", "build_handlers"]
