import re
from contextvars import ContextVar
from time import perf_counter

SQL_KEYWORDS_RE = re.compile(
    r"\b(SELECT|FROM|WHERE|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN|ON|AND|OR|ORDER BY|GROUP BY|HAVING|LIMIT|OFFSET|INSERT INTO|VALUES|UPDATE|SET|DELETE|CREATE TABLE|ALTER TABLE|DROP TABLE|DISTINCT|COUNT|SUM|AVG|MAX|MIN|UNION|EXISTS|IN|IS NULL|IS NOT NULL|LIKE|BETWEEN|CASE|WHEN|THEN|ELSE|END|ASC|DESC|AS|WITH|RECURSIVE)\b",
    re.IGNORECASE,
)

SQL_CLAUSES_RE = re.compile(
    r"\b(FROM|WHERE|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN|GROUP BY|ORDER BY|HAVING|LIMIT|OFFSET|ON|AND|OR|UNION|WITH|CASE|WHEN|THEN|ELSE)\b",
    re.IGNORECASE,
)

_query_count: ContextVar[int] = ContextVar("query_count", default=0)
_query_duration: ContextVar[float] = ContextVar("query_duration", default=0.0)
_seen_queries: ContextVar[dict] = ContextVar("seen_queries", default={})
_duplicate_log: ContextVar[list] = ContextVar("duplicate_log", default=[])
_query_log: ContextVar[list] = ContextVar("query_log", default=[])


def reset():
    _query_count.set(0)
    _query_duration.set(0.0)
    _seen_queries.set({})
    _duplicate_log.set([])
    _query_log.set([])


def get_stats():
    duplicate_queries = _duplicate_log.get()
    duplicate_sqls = {d["sql"] for d in duplicate_queries}

    queries = _query_log.get()
    for q in queries:
        q["is_duplicate"] = q["sql"] in duplicate_sqls

    return {
        "count": _query_count.get(),
        "duration": _query_duration.get(),
        "duplicate_queries": duplicate_queries,
        "queries": queries,
    }


def _hash_params(params):
    try:
        return hash(tuple(params)) if params else 0
    except TypeError:
        return hash(str(params))


def _record(sql, params, duration):
    _query_count.set(_query_count.get() + 1)
    _query_duration.set(_query_duration.get() + duration)

    seen = _seen_queries.get()
    params_hash = _hash_params(params)

    query_log = _query_log.get()
    query_log.append(
        {
            "sql": sql,
            "duration": round(duration, 2),
        }
    )
    _query_log.set(query_log)

    if sql in seen:
        if params_hash in seen[sql]:
            duplicates = _duplicate_log.get()
            duplicates.append({"sql": sql, "duration": round(duration, 2)})
        else:
            seen[sql].add(params_hash)
    else:
        seen[sql] = {params_hash}


def format_sql(sql):
    """Highlight SQL keywords with HTML spans for visual formatting.

    Escapes HTML first for security, then wraps SQL keywords in span tags.
    Used for rendering duplicates in the injected devbar HTML.

    Args:
        sql: SQL query string

    Returns:
        Safe HTML string with keywords wrapped in spans
    """
    from django.utils.html import escape
    from django.utils.safestring import mark_safe

    escaped_sql = escape(sql)

    def replace_keyword(match):
        return f'<span class="sql-keyword">{match.group(0)}</span>'

    highlighted = SQL_KEYWORDS_RE.sub(replace_keyword, escaped_sql)
    return mark_safe(highlighted)


class SQLTruncator:
    """Handles intelligent SQL query truncation while preserving the structure."""

    def __init__(self, max_length=150):
        self.max_length = max_length

    def truncate(self, sql):
        """Intelligently truncate long SQL queries while preserving the structure.

        Args:
            sql: SQL query string

        Returns:
            Truncated SQL string with "..." at the end if shortened
        """
        if len(sql) <= self.max_length:
            return sql

        sql_upper = sql.upper()

        if sql_upper.startswith("SELECT"):
            result = self._truncate_select(sql, sql_upper)
            if result:
                return result

        return self._fallback_truncate(sql)

    def _truncate_select(self, sql, sql_upper):
        """Truncate SELECT queries while preserving columns and joins."""
        distinct_match = re.search(r"\bDISTINCT\b", sql_upper[:20])
        has_distinct = distinct_match is not None
        from_match = re.search(r"\bFROM\b", sql_upper)

        if not from_match:
            return None

        from_pos = from_match.start()

        if has_distinct:
            distinct_end = distinct_match.end()
            select_part = sql[distinct_end:from_pos].strip()
        else:
            select_part = sql[6:from_pos].strip()

        first_column = self._extract_first_column(select_part)
        select_clause = "SELECT DISTINCT" if has_distinct else "SELECT"

        from_part = sql[from_pos:]
        table_match = re.search(r'FROM\s+(["\[]?)(\w+)', from_part, re.IGNORECASE)

        if not table_match:
            return None

        table_name = table_match.group(2)
        result = f"{select_clause} {first_column} FROM {table_name}"

        # Add joins if they fit
        join_result = self._add_joins_if_fit(result, from_part)
        if join_result:
            return join_result

        return result if len(result) <= self.max_length else None

    def _extract_first_column(self, select_part):
        """Extract the first column from SELECT clause, handling quotes and parentheses."""
        if not select_part.strip():
            return "..."
        columns = self._parse_columns(select_part)
        return columns[0] + ", ..." if columns else "..."

    def _parse_columns(self, select_part):
        """Parse columns from SELECT clause, handling complex expressions."""
        columns = []
        in_quotes = False
        quote_char = None
        in_parens = False
        paren_depth = 0
        current_col = ""

        for i, char in enumerate(select_part):
            if char in ('"', "'") and (i == 0 or select_part[i - 1] != "\\"):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                current_col += char
            elif in_quotes:
                current_col += char
            elif char == "(":
                in_parens = True
                paren_depth += 1
                current_col += char
            elif char == ")":
                paren_depth -= 1
                if paren_depth == 0:
                    in_parens = False
                current_col += char
            elif char == "," and not in_parens and not in_quotes:
                if current_col.strip():
                    columns.append(current_col.strip())
                    break
                current_col = ""
            elif char in " \t\n" and not in_parens and not in_quotes:
                if current_col.strip():
                    columns.append(current_col.strip())
                current_col = ""
            else:
                current_col += char

        if not columns and current_col.strip():
            columns.append(current_col.strip())

        return columns

    def _add_joins_if_fit(self, base_result, from_part):
        """Add JOIN clauses to result if they fit within max_length."""
        join_matches = re.finditer(
            r'\b(LEFT\s+|RIGHT\s+|INNER\s+|OUTER\s+)?JOIN\s+(["\[]?)(\w+)',
            from_part,
            re.IGNORECASE,
        )

        result = base_result

        for join_match in join_matches:
            join_type = (join_match.group(1) or "").strip()
            join_table = join_match.group(3)
            new_result = (
                f"{result} {join_type} JOIN {join_table}"
                if join_type
                else f"{result} JOIN {join_table}"
            )
            if len(new_result) <= self.max_length:
                result = new_result
            else:
                break

        return result if len(result) <= self.max_length else None

    def _fallback_truncate(self, sql):
        """Fallback truncation at clause boundaries or simple length limit."""
        # First try simple length truncation
        if len(sql) <= self.max_length:
            return sql

        # Try clause boundary truncation
        clause_positions = [
            (match.start(), match.group())
            for match in SQL_CLAUSES_RE.finditer(sql[: self.max_length + 50])
        ]

        if clause_positions:
            best_pos = self._find_best_truncate_position(clause_positions)
            if best_pos > 0:
                return sql[:best_pos].rstrip() + "..."

        # Final fallback: simple truncation
        return sql[: self.max_length].rstrip() + "..."

    def _find_best_truncate_position(self, clause_positions):
        """Find the best position to truncate based on clause boundaries."""
        best_pos = 0
        for pos, _ in clause_positions:
            if self.max_length > pos > best_pos:
                best_pos = pos

        if best_pos > self.max_length - 30:
            best_pos = 0

        return best_pos


def truncate_sql(sql, max_length=150):
    truncator = SQLTruncator(max_length)
    return truncator.truncate(sql)


def tracking_wrapper(execute, sql, params, many, context):
    start = perf_counter()
    try:
        return execute(sql, params, many, context)
    finally:
        _record(sql, params, (perf_counter() - start) * 1000)
