from contextvars import ContextVar
from time import perf_counter

_query_count: ContextVar[int] = ContextVar("query_count", default=0)
_query_duration: ContextVar[float] = ContextVar("query_duration", default=0.0)
_seen_queries: ContextVar[dict] = ContextVar("seen_queries", default={})
_duplicate_log: ContextVar[list] = ContextVar("duplicate_log", default=[])


def reset():
    _query_count.set(0)
    _query_duration.set(0.0)
    _seen_queries.set({})
    _duplicate_log.set([])


def get_stats():
    return {
        "count": _query_count.get(),
        "duration": _query_duration.get(),
        "has_duplicates": bool(_duplicate_log.get()),
        "duplicate_queries": _duplicate_log.get(),
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

    if sql in seen:
        if params_hash in seen[sql]:
            param_str = str(params)
            if len(param_str) > 200:
                param_str = param_str[:200] + "..."

            duplicates = _duplicate_log.get()
            duplicates.append(
                {"sql": sql, "params": param_str, "duration": round(duration, 2)}
            )
        else:
            seen[sql].add(params_hash)
    else:
        seen[sql] = {params_hash}


def tracking_wrapper(execute, sql, params, many, context):
    start = perf_counter()
    try:
        return execute(sql, params, many, context)
    finally:
        _record(sql, params, (perf_counter() - start) * 1000)
