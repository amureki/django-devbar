from contextvars import ContextVar
from time import perf_counter

_query_count: ContextVar[int] = ContextVar("query_count", default=0)
_query_duration: ContextVar[float] = ContextVar("query_duration", default=0.0)
_seen_queries: ContextVar[dict] = ContextVar(
    "seen_queries"
)  # sql -> set of params hashes
_has_duplicates: ContextVar[bool] = ContextVar("has_duplicates", default=False)


def reset():
    _query_count.set(0)
    _query_duration.set(0.0)
    _seen_queries.set({})
    _has_duplicates.set(False)


def get_stats():
    return {
        "count": _query_count.get(),
        "duration": _query_duration.get(),
        "has_duplicates": _has_duplicates.get(),
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
    if sql in seen:
        params_hash = _hash_params(params)
        if params_hash in seen[sql]:
            _has_duplicates.set(True)
        else:
            seen[sql].add(params_hash)
    else:
        seen[sql] = {_hash_params(params)}


def tracking_wrapper(execute, sql, params, many, context):
    start = perf_counter()
    try:
        return execute(sql, params, many, context)
    finally:
        _record(sql, params, (perf_counter() - start) * 1000)
