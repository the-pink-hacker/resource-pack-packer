import logging
from typing import Tuple, Optional


def choose_from_list(items: list, title: Optional[str] = None) -> Tuple[any, int]:
    """
    Asks the use to pick between the provided list
    :param items: The list for the user to select between
    :param title: The title that will be shown to the user
    :return: A object from the 'items' list
    """
    if title is not None:
        options = f"{title}\n"
    else:
        options = ""
    for i, item in enumerate(items, start=1):
        options += f"[{i}] - {str(item)}\n"
    selected = input(options)

    if selected == "":
        return items[0], 0
    elif selected.isdigit():
        return items[int(selected) - 1], int(selected) - 1
    elif isinstance(selected, str):
        for i, item in enumerate(items):
            if item == selected:
                return item, i


def add_to_logger_name(logger_name: str, title: str):
    return logging.getLogger(f"{logger_name}\x1b[0m/\x1b[34m{title}\x1b[0m")
