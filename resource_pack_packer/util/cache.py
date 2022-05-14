import json
import os
from typing import Union


def update_cache(value: Union[str, list[str], set[str]], src: str):
    cache_data = {
        "cache": []
    }
    # Cache file exists
    if os.path.exists(src):
        with open(src, "r") as file:
            cache_data = json.load(file)
    elif not os.path.exists(os.path.dirname(src)):
        os.makedirs(os.path.dirname(src))

    # Add to cache with duplicates
    if isinstance(value, str):
        cache_set = set(cache_data["cache"])
        cache_set.add(value)
        cache_data["cache"] = list(set(cache_data["cache"]) | cache_set)
    elif isinstance(value, (list, set)):
        cache_data["cache"] = list(set(cache_data["cache"]) | set(value))

    with open(src, "w", encoding="utf-8") as file:
        json.dump(cache_data, file, ensure_ascii=False, indent=2)


def check_cache(value: str, src: str) -> bool:
    if os.path.exists(src):
        with open(src, "r") as file:
            cache_data = json.load(file)
            if value in cache_data["cache"]:
                return True
    return False


def get_cache(src: str) -> set:
    if os.path.exists(src):
        with open(src, "r") as file:
            return set(json.load(file)["cache"])
    return set()
