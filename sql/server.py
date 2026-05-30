from fastmcp import FastMCP
from sql.sql_tools import (
    execute_query,
    execute_write,
    list_tables,
    describe_table,
    get_table_sample,
    list_schemas,
    get_row_count,
)

mcp = FastMCP("SQL Server MCP Server")


@mcp.tool()
def tool_sql_query(sql: str, params: list | None = None) -> dict:
    """
    Run a read-only SQL query against the configured SQL Server database.
    Supports SELECT, WITH (CTEs), EXEC / EXECUTE, SHOW, DESCRIBE, EXPLAIN.
    sql: the T-SQL query string
    params: optional list of positional parameter values (replaces ? placeholders)
    Returns columns, rows, and row_count.
    """
    return execute_query(sql, params)


@mcp.tool()
def tool_sql_write(sql: str, params: list | None = None, confirm: bool = False) -> dict:
    """
    Run a write SQL statement (INSERT, UPDATE, DELETE) on the SQL Server database.
    You MUST pass confirm=True to execute — this is a safety guard.
    sql: the T-SQL statement
    params: optional list of positional parameter values (replaces ? placeholders)
    confirm: must be True to allow the write to proceed
    Returns rows_affected.
    """
    return execute_write(sql, params, confirm)


@mcp.tool()
def tool_sql_list_tables(schema: str = "dbo") -> dict:
    """
    List all tables in the given SQL Server schema.
    schema: database schema name (default: dbo)
    Returns table names and their type (BASE TABLE or VIEW).
    """
    return list_tables(schema)


@mcp.tool()
def tool_sql_describe_table(table_name: str, schema: str = "dbo") -> dict:
    """
    Show column definitions for a SQL Server table.
    table_name: the table to inspect
    schema: database schema (default: dbo)
    Returns column name, data type, max length, nullability, and default value.
    """
    return describe_table(table_name, schema)


@mcp.tool()
def tool_sql_sample_table(table_name: str, schema: str = "dbo", top: int = 10) -> dict:
    """
    Fetch a sample of rows from a SQL Server table (max 100 rows).
    table_name: table to sample
    schema: database schema (default: dbo)
    top: number of rows to return (default: 10, max: 100)
    """
    return get_table_sample(table_name, schema, top)


@mcp.tool()
def tool_sql_list_schemas() -> dict:
    """
    List all non-system schemas available in the connected SQL Server database.
    """
    return list_schemas()


@mcp.tool()
def tool_sql_row_count(table_name: str, schema: str = "dbo") -> dict:
    """
    Get the exact row count for a SQL Server table.
    table_name: table name
    schema: database schema (default: dbo)
    """
    return get_row_count(table_name, schema)


if __name__ == "__main__":
    mcp.run()
