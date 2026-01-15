from collections.abc import Callable
from functools import wraps


def run_once[**P, T](func: Callable[P, T]) -> Callable[P, T | None]:
    """Wrap func so that it only runs on the first call.

    All subsequent calls are no-op. Effectively, this makes the function idempotent.
    """
    has_run = False

    @wraps(func)
    def _inner(*args: P.args, **kwargs: P.kwargs) -> T | None:
        nonlocal has_run
        if has_run:
            return None
        try:
            return func(*args, **kwargs)
        finally:
            has_run = True

    return _inner
