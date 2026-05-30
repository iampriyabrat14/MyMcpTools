import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

_READONLY_PREFIXES = ("SELECT", "WITH", "EXEC", "EXECUTE", "SHOW", "DESCRIBE", "EXPLAIN")
_DANGEROUS_KEYWORDS = ("DROP", "TRUNCATE", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "GRANT", "REVOKE")


def _get_connection() -> pyodbc.Connection:
    server = os.getenv("SQL_SERVER_HOST", "localhost")
    database = os.getenv("SQL_SERVER_DB", "master")
    username = os.getenv("SQL_SERVER_USER", "")
    password = os.getenv("SQL_SERVER_PASSWORD", "")
    driver = os.getenv("SQL_SERVER_DRIVER", "ODBC Driver 17 for SQL Server")

    if username and password:
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
        )
    else:
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            "Trusted_Connection=yes;"
        )

    return pyodbc.connect(conn_str, timeout=30)


def _is_safe_query(sql: str) -> bool:
    normalized = sql.strip().upper()
    return normalized.startswith(_READONLY_PREFIXES)


def execute_query(sql: str, params: list | None = None) -> dict:
    """Run a SELECT/WITH/EXEC query and return rows as a list of dicts."""
    if not _is_safe_query(sql):
        raise ValueError(
            "Only read-only queries (SELECT, WITH, EXEC, EXECUTE, SHOW, DESCRIBE, EXPLAIN) "
            "are allowed via execute_query. Use execute_write for data modifications."
        )

    conn = _get_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        results = [dict(zip(columns, row)) for row in rows]

        return {
            "status": "success",
            "row_count": len(results),
            "columns": columns,
            "rows": results,
        }
    finally:
        conn.close()


def execute_write(sql: str, params: list | None = None, confirm: bool = False) -> dict:
    """Run INSERT / UPDATE / DELETE and return affected row count. Requires confirm=True."""
    if not confirm:
        raise ValueError(
            "Write operations require confirm=True to prevent accidental data changes."
        )

    normalized = sql.strip().upper()
    if normalized.startswith(_READONLY_PREFIXES):
        raise ValueError("Use execute_query for read-only queries.")

    conn = _get_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        affected = cursor.rowcount
        conn.commit()
        return {"status": "success", "rows_affected": affected}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_tables(schema: str = "dbo") -> dict:
    """List all tables in the given schema."""
    sql = """
        SELECT TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = ?
        ORDER BY TABLE_NAME
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, [schema])
        rows = cursor.fetchall()
        tables = [{"table_name": r[0], "table_type": r[1]} for r in rows]
        return {"status": "success", "schema": schema, "tables": tables}
    finally:
        conn.close()


def describe_table(table_name: str, schema: str = "dbo") -> dict:
    """Return column definitions for a table."""
    sql = """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH,
               IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, [schema, table_name])
        rows = cursor.fetchall()
        if not rows:
            return {"status": "not_found", "table": f"{schema}.{table_name}"}
        columns = [
            {
                "column": r[0],
                "type": r[1],
                "max_length": r[2],
                "nullable": r[3],
                "default": r[4],
            }
            for r in rows
        ]
        return {"status": "success", "table": f"{schema}.{table_name}", "columns": columns}
    finally:
        conn.close()


def get_table_sample(table_name: str, schema: str = "dbo", top: int = 10) -> dict:
    """Fetch a sample of rows from a table (read-only TOP N)."""
    if top > 100:
        top = 100
    safe_schema = schema.replace("]", "").replace("[", "")
    safe_table = table_name.replace("]", "").replace("[", "")
    sql = f"SELECT TOP {int(top)} * FROM [{safe_schema}].[{safe_table}]"
    return execute_query(sql)


def list_schemas() -> dict:
    """List all non-system schemas in the database."""
    sql = """
        SELECT SCHEMA_NAME
        FROM INFORMATION_SCHEMA.SCHEMATA
        WHERE SCHEMA_NAME NOT IN ('sys','INFORMATION_SCHEMA','guest','db_owner',
                                   'db_accessadmin','db_securityadmin','db_ddladmin',
                                   'db_backupoperator','db_datareader','db_datawriter',
                                   'db_denydatareader','db_denydatawriter')
        ORDER BY SCHEMA_NAME
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        return {"status": "success", "schemas": [r[0] for r in rows]}
    finally:
        conn.close()


def get_row_count(table_name: str, schema: str = "dbo") -> dict:
    """Return the exact row count for a table."""
    safe_schema = schema.replace("]", "").replace("[", "")
    safe_table = table_name.replace("]", "").replace("[", "")
    sql = f"SELECT COUNT(*) FROM [{safe_schema}].[{safe_table}]"
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        count = cursor.fetchone()[0]
        return {"status": "success", "table": f"{schema}.{table_name}", "row_count": count}
    finally:
        conn.close()
