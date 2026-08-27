from mcp.server.mcpserver import MCPServer
import pymysql
import re
import os
from dotenv import load_dotenv

load_dotenv()

mcp = MCPServer("mysql-analytics")

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor
    )

DEFAULT_ROW_LIMIT = 7000       # for real analytics work
MAX_EXECUTION_MS = 5000        # server-side query timeout

def enforce_row_limit(sql: str, limit: int = DEFAULT_ROW_LIMIT) -> str:
    if re.search(r"\blimit\s+\d+", sql, re.IGNORECASE):
        return sql
    return f"{sql.rstrip().rstrip(';')} LIMIT {limit}"


@mcp.tool()
def run_query(sql: str) -> dict:
    """
    Run a read-only SQL query against the trend tracking database.
    Only SELECT works since this connects as a SELECT-only DB user.

    Behavior:
      - Auto-adds a LIMIT if you don't include one
      - Caps server-side execution time so a bad query can't hang forever

    Guidance:
      - Call get_schema once at the start of a session to learn the available
        tables, and describe_table for any specific table before querying it
        for the first time. Reuse that knowledge for the rest of the session
        rather than discovering structure through failed or exploratory queries.
      - For analytical questions (trends, correlations, distributions), aggregate
        or filter in SQL to keep result sets small (GROUP BY, window functions,
        date bucketing) rather than pulling raw rows.
      - Do statistical analysis, correlation, forecasting, or visualization in
        code execution after retrieving the data — not by requesting new tools.
    """
    try:
        bounded_sql = enforce_row_limit(sql)

        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        try:
            cursor.execute(f"SET SESSION MAX_EXECUTION_TIME={MAX_EXECUTION_MS}")
        except Exception:
            pass

        cursor.execute(bounded_sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]  # read before close

        cursor.close()
        conn.close()

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": len(rows) == DEFAULT_ROW_LIMIT,
            "max_rows": DEFAULT_ROW_LIMIT,
        }
    except Exception as e:
        return {
            "error": str(e),
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
            "max_rows": DEFAULT_ROW_LIMIT,
        }


@mcp.tool()
def get_schema() -> dict:
    """
    Return the schema (tables, columns, types) for the trend tracking database.

    Call this first when starting a new session or when you're unfamiliar
    with the available tables — before writing analytical queries with
    run_query. Cache this in your reasoning for the rest of the session
    instead of re-calling it every turn.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            ORDER BY TABLE_NAME, ORDINAL_POSITION
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        schema: dict[str, list[dict]] = {}
        for row in rows:
            table = row["TABLE_NAME"]
            schema.setdefault(table, []).append(
                {
                    "column": row["COLUMN_NAME"],
                    "type": row["DATA_TYPE"],
                    "nullable": row["IS_NULLABLE"],
                    "key": row["COLUMN_KEY"],
                }
            )
        return schema
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def list_tables() -> list[str]:
    """List all tables in the connected database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [list(row.values())[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return tables
    except Exception as e:
        return [f"ERROR: {e}"]


@mcp.tool()
def describe_table(table: str) -> list[dict]:
    """
    Describe a single table: column names, types, nullability, keys, defaults.
    Use this before writing a query against a table you haven't seen yet.
    """
    try:
        if not re.match(r"^[A-Za-z0-9_]+$", table):
            return [{"error": "Invalid table name."}]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """,
            (table,),
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def sample_rows(table: str, n: int = 5) -> list[dict]:
    """
    Return a small sample of real rows from a table, to see actual data
    shape/values (e.g. whether a 'status' column is an enum, int code, etc).
    """
    try:
        if not re.match(r"^[A-Za-z0-9_]+$", table):
            return [{"error": "Invalid table name."}]
        n = max(1, min(int(n), 50))  # hard cap regardless of what's asked

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM `{table}` LIMIT %s", (n,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        return [{"error": str(e)}]


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8080)