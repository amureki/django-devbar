from django_devbar import tracker
from django_devbar.tracker import SQLTruncator, truncate_sql


class TestTracker:
    def test_reset_clears_stats(self):
        tracker._query_count.set(5)
        tracker._query_duration.set(100.0)

        tracker.reset()

        stats = tracker.get_stats()
        assert stats["count"] == 0
        assert stats["duration"] == 0.0

    def test_single_query_counted(self):
        tracker.reset()

        def mock_execute(*args):
            return "result"

        result = tracker.tracking_wrapper(mock_execute, "SELECT 1", [], False, {})

        assert result == "result"
        assert tracker.get_stats()["count"] == 1

    def test_duration_tracked(self):
        tracker.reset()

        def slow_execute(*args):
            import time

            time.sleep(0.01)
            return "result"

        tracker.tracking_wrapper(slow_execute, "SELECT 1", [], False, {})

        assert tracker.get_stats()["duration"] >= 10  # at least 10ms

    def test_multiple_queries_summed(self):
        tracker.reset()

        def mock_execute(*args):
            return "result"

        for _ in range(3):
            tracker.tracking_wrapper(mock_execute, "SELECT 1", [], False, {})

        assert tracker.get_stats()["count"] == 3

    def test_no_duplicates_for_unique_queries(self):
        tracker.reset()

        def mock_execute(*args):
            return "result"

        tracker.tracking_wrapper(mock_execute, "SELECT 1", [], False, {})
        tracker.tracking_wrapper(mock_execute, "SELECT 2", [], False, {})

        assert len(tracker.get_stats()["duplicate_queries"]) == 0

    def test_no_duplicates_for_same_sql_different_params(self):
        tracker.reset()

        def mock_execute(*args):
            return "result"

        tracker.tracking_wrapper(
            mock_execute, "SELECT * FROM t WHERE id=%s", [1], False, {}
        )
        tracker.tracking_wrapper(
            mock_execute, "SELECT * FROM t WHERE id=%s", [2], False, {}
        )

        assert len(tracker.get_stats()["duplicate_queries"]) == 0

    def test_duplicates_detected_same_sql_same_params(self):
        tracker.reset()

        def mock_execute(*args):
            return "result"

        tracker.tracking_wrapper(
            mock_execute, "SELECT * FROM t WHERE id=%s", [1], False, {}
        )
        tracker.tracking_wrapper(
            mock_execute, "SELECT * FROM t WHERE id=%s", [1], False, {}
        )

        assert len(tracker.get_stats()["duplicate_queries"]) == 1

    def test_similar_queries_detected_same_sql_different_params(self):
        tracker.reset()

        def mock_execute(*args):
            return "result"

        tracker.tracking_wrapper(
            mock_execute, "SELECT * FROM t WHERE id=%s", [1], False, {}
        )
        tracker.tracking_wrapper(
            mock_execute, "SELECT * FROM t WHERE id=%s", [2], False, {}
        )

        stats = tracker.get_stats()
        assert len(stats["similar_queries"]) == 2
        assert stats["queries"][0]["is_similar"] is True
        assert stats["queries"][1]["is_similar"] is True

    def test_no_similar_for_unique_queries(self):
        tracker.reset()

        def mock_execute(*args):
            return "result"

        tracker.tracking_wrapper(mock_execute, "SELECT 1", [], False, {})
        tracker.tracking_wrapper(mock_execute, "SELECT 2", [], False, {})

        stats = tracker.get_stats()
        assert len(stats["similar_queries"]) == 0
        assert stats["queries"][0]["is_similar"] is False
        assert stats["queries"][1]["is_similar"] is False

    def test_duplicate_only_not_similar(self):
        """Same SQL+params twice is duplicate but not similar (only one param set)."""
        tracker.reset()

        def mock_execute(*args):
            return "result"

        tracker.tracking_wrapper(
            mock_execute, "SELECT * FROM t WHERE id=%s", [1], False, {}
        )
        tracker.tracking_wrapper(
            mock_execute, "SELECT * FROM t WHERE id=%s", [1], False, {}
        )

        stats = tracker.get_stats()
        assert len(stats["duplicate_queries"]) == 1
        assert len(stats["similar_queries"]) == 0

    def test_mixed_similar_and_duplicate(self):
        """SQL with [1], [1], [2] - queries can be both similar and duplicate."""
        tracker.reset()

        def mock_execute(*args):
            return "result"

        tracker.tracking_wrapper(
            mock_execute, "SELECT * FROM t WHERE id=%s", [1], False, {}
        )
        tracker.tracking_wrapper(
            mock_execute, "SELECT * FROM t WHERE id=%s", [1], False, {}
        )
        tracker.tracking_wrapper(
            mock_execute, "SELECT * FROM t WHERE id=%s", [2], False, {}
        )

        stats = tracker.get_stats()
        assert len(stats["duplicate_queries"]) == 1
        # All 3 are similar (same SQL, multiple param sets)
        assert len(stats["similar_queries"]) == 3
        # First [1] is similar but not duplicate (first occurrence)
        assert stats["queries"][0]["is_similar"] is True
        assert stats["queries"][0]["is_duplicate"] is False
        # Second [1] is both similar AND duplicate
        assert stats["queries"][1]["is_similar"] is True
        assert stats["queries"][1]["is_duplicate"] is True
        # The [2] query is similar but not duplicate
        assert stats["queries"][2]["is_similar"] is True
        assert stats["queries"][2]["is_duplicate"] is False


class TestSQLTruncator:
    def test_short_queries_unchanged(self):
        truncator = SQLTruncator(150)
        short_sql = "SELECT * FROM users"
        assert truncator.truncate(short_sql) == short_sql

    def test_exact_length_queries_unchanged(self):
        sql = "SELECT id, name, email FROM users WHERE active = 1"
        truncator = SQLTruncator(len(sql))
        assert truncator.truncate(sql) == sql

    def test_simple_select_truncation(self):
        long_sql = "SELECT " + ", ".join([f"col{i}" for i in range(20)]) + " FROM users"
        result = truncate_sql(long_sql, 50)
        assert "SELECT col0, ... FROM users" == result
        assert len(result) <= 50

    def test_select_with_distinct(self):
        long_sql = (
            "SELECT DISTINCT "
            + ", ".join([f"col{i}" for i in range(10)])
            + " FROM users"
        )
        result = truncate_sql(long_sql, 50)
        assert result.startswith("SELECT DISTINCT")
        assert "FROM users" in result
        assert len(result) <= 50

    def test_select_with_joins(self):
        sql = "SELECT id, name FROM users JOIN profiles ON users.id = profiles.user_id JOIN roles ON users.role_id = roles.id"
        result = truncate_sql(sql, 80)
        assert "SELECT" in result and "FROM users" in result
        assert "JOIN" in result
        assert len(result) <= 80

    def test_complex_column_expressions(self):
        sql = "SELECT COUNT(DISTINCT CASE WHEN status = 'active' THEN id END), AVG(score) as avg_score FROM users"
        result = truncate_sql(sql, 100)
        assert "SELECT" in result and "FROM users" in result
        assert len(result) <= 100

    def test_quoted_columns(self):
        sql = 'SELECT "user name", `email address`, COUNT(*) FROM "user table"'
        result = truncate_sql(sql, 80)
        assert "SELECT" in result and "FROM" in result
        assert len(result) <= 80

    def test_nested_function_calls(self):
        sql = "SELECT COALESCE(MAX(CASE WHEN created_at > '2023-01-01' THEN id END), 0) as latest_id FROM users"
        result = truncate_sql(sql, 100)
        assert "SELECT" in result and "FROM users" in result
        assert len(result) <= 100

    def test_subquery_in_select(self):
        sql = "SELECT id, (SELECT COUNT(*) FROM orders WHERE user_id = users.id) as order_count FROM users"
        result = truncate_sql(sql, 100)
        assert "SELECT" in result and "FROM users" in result
        assert len(result) <= 100

    def test_non_select_queries(self):
        insert_sql = "INSERT INTO users (name, email) VALUES ('John', 'john@example.com'), ('Jane', 'jane@example.com')"
        result = truncate_sql(insert_sql, 50)
        assert result.endswith("...")
        assert len(result) <= 55  # Allow some tolerance for fallback

    def test_update_queries(self):
        update_sql = "UPDATE users SET name = 'John Doe', email = 'john@example.com', updated_at = NOW() WHERE id = 1"
        result = truncate_sql(update_sql, 80)
        assert result.endswith("...")
        assert len(result) <= 85  # Allow some tolerance for fallback

    def test_clause_boundary_truncation(self):
        sql = "SELECT id, name FROM users WHERE active = 1 AND created_at > '2023-01-01' ORDER BY name LIMIT 10"
        result = truncate_sql(sql, 60)
        # Should truncate at SELECT boundary since it fits
        assert "SELECT" in result and "FROM users" in result
        assert len(result) <= 60

    def test_empty_select_list(self):
        sql = "SELECT FROM users"  # Invalid SQL but should handle gracefully
        result = truncate_sql(sql, 50)
        assert "SELECT" in result and "FROM users" in result

    def test_very_long_single_column(self):
        long_column = "COALESCE(MAX(CASE WHEN status = 'active' AND created_at > '2023-01-01' AND score > 50 THEN id END), 0) as latest_id"
        sql = f"SELECT {long_column} FROM users"
        result = truncate_sql(sql, 100)
        # Should fallback to simple truncation for very long columns
        assert "SELECT" in result
        assert len(result) <= 105  # Allow some tolerance for fallback truncation

    def test_multiple_joins_fitting(self):
        sql = "SELECT id FROM users JOIN profiles ON users.id = profiles.user_id JOIN roles ON users.role_id = roles.id"
        result = truncate_sql(sql, 120)
        assert "JOIN profiles" in result
        assert "JOIN roles" in result
        assert len(result) <= 120

    def test_joins_not_fitting(self):
        sql = "SELECT id FROM users JOIN very_long_table_name_on_purpose ON users.id = very_long_table_name_on_purpose.user_id"
        result = truncate_sql(sql, 80)
        assert "SELECT" in result and "FROM users" in result
        assert len(result) <= 80

    def test_escape_sequences_in_quotes(self):
        sql = "SELECT name FROM users WHERE bio LIKE 'John\\'s story %' AND status = 'active'"
        result = truncate_sql(sql, 80)
        assert "SELECT" in result and "FROM users" in result
        assert len(result) <= 80


class TestTruncateSqlFunction:
    def test_function_delegation(self):
        sql = "SELECT id, name FROM users WHERE active = 1"
        result = truncate_sql(sql, 50)
        assert "SELECT" in result
        assert len(result) <= 50

    def test_custom_max_length(self):
        sql = "SELECT id, name, email, created_at FROM users"
        result = truncate_sql(sql, 30)
        assert len(result) <= 30
        # Result should be truncated since SQL is longer than 30 chars


def test_default_max_length():
    long_sql = (
        "SELECT "
        + ", ".join([f"col{i}" for i in range(20)])
        + " FROM some_very_long_table_name"
    )
    result = truncate_sql(long_sql)
    assert len(result) <= 150


class TestSQLTruncatorEdgeCases:
    def test_malformed_sql(self):
        malformed = "SELECT FROM WHERE JOIN"
        result = truncate_sql(malformed, 50)
        assert len(result) <= 50

    def test_sql_with_comments(self):
        sql = "SELECT id, name /* comment here */ FROM users WHERE active = 1"
        result = truncate_sql(sql, 60)
        assert "SELECT" in result and "FROM users" in result
        assert len(result) <= 60

    def test_sql_with_line_breaks(self):
        sql = """SELECT id, name
                 FROM users
                 WHERE active = 1"""
        result = truncate_sql(sql, 50)
        assert "SELECT" in result and "FROM users" in result
        assert len(result) <= 50

    def test_unicode_characters(self):
        sql = "SELECT 姓名, email FROM 用户 WHERE 状态 = '活跃'"
        result = truncate_sql(sql, 50)
        assert "SELECT" in result and "FROM" in result
        assert len(result) <= 50
