from typing import Iterable, TypeVar

T = TypeVar("T")


def find_duplicates(data: Iterable[T]) -> Iterable[T]:
    """Return duplicates in the given data.

    Worst-case run-time:   O(n*log(n))
    Worst-case memory use: O(n)
    """
    seen = set()
    for datum in data:  # run-time: O(n)
        if datum in seen:
            yield datum
        seen.add(datum)  # run-time: O(log(n))
