from typing import Mapping, TypeVar

from immutables import Map

Key = TypeVar("Key")
Val = TypeVar("Val")


# mypy can't handle the return inside the with statement. Hence the ignore.
def freeze_mapping(mapping: Mapping[Key, Val]) -> Map[Key, Val]:  # type: ignore[return]
    """Convert `Mapping` into `immutables.Map`.

    Unlike `immutables.Map.__init__`, this function works for non-string keys.
    Note that `__init__` will never work because keywords must be strings.
    """
    result: Map[Key, Val] = Map()
    with result.mutate() as result_mutation:
        for key, value in mapping.items():
            result_mutation[key] = value
        return result_mutation.finish()
