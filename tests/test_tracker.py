from django_devbar import tracker


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

        assert tracker.get_stats()["has_duplicates"] is False

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

        assert tracker.get_stats()["has_duplicates"] is False

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

        assert tracker.get_stats()["has_duplicates"] is True
