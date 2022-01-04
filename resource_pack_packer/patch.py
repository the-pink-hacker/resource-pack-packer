import json
import logging
import os
import re
import shutil
from glob import glob
from os import path

from typing import List, Union

from resource_pack_packer.settings import MAIN_SETTINGS, parse_dir_keywords


def check_option(root, option):
    if option in root:
        return True
    else:
        return False


def get_patches(patch_names):
    patches = []

    for patch in patch_names:
        patches.append(Patch(get_patch_data(patch), patch))

    return patches


def get_patch_data(patch):
    with open(parse_dir_keywords(
            path.join(MAIN_SETTINGS.working_directory, MAIN_SETTINGS.patch_dir, f"{patch}.json"))) as file:
        return json.load(file)


class Patch:
    def __init__(self, data, name):
        self.patch = data["patch"]
        self.type = data["type"]
        self.name = name


# Replaces and adds files accordingly
def _patch_replace(pack, patch, logger: logging.Logger):
    patch_dir = parse_dir_keywords(patch.patch["directory"])
    patch_files = glob(path.join(patch_dir, "**"), recursive=True)

    for file in patch_files:
        # The location that the file should go to
        pack_file = file.replace(patch_dir, pack)

        # Removes all files in pack that are in the patch.py
        if path.isfile(pack_file) and path.exists(pack_file):
            os.remove(pack_file)

        # Applies patch.py
        if path.isfile(file) and path.exists(file):
            try:
                shutil.copy(file, pack_file)
            except IOError:
                os.makedirs(path.dirname(pack_file))
                shutil.copy(file, pack_file)


def _remove_block(file):
    if path.exists(file):
        os.remove(file)


# Removes all specified files
def _patch_remove(pack, patch, logger: logging.Logger):
    files = []
    if "files" in patch.patch:
        files = patch.patch["files"]

    blocks = []
    if "blocks" in patch.patch:
        blocks = patch.patch["blocks"]

    for i, block in enumerate(blocks, start=1):
        block_name_plural = block["block"]

        # Example: stone_bricks -> stone_brick
        if check_option(block, "plural") and block["plural"]:
            block_name = block_name_plural[:-1]
        else:
            block_name = block_name_plural

        for block_file in patch.patch["block_files"]:
            parsed_block_file = block_file.replace("[block_name]", block_name)
            parsed_block_file = parsed_block_file.replace("[block_name_plural]", block_name_plural)

            _remove_block(path.join(pack, path.normpath(parsed_block_file)))

        logger.info(f"Removed block [{i}/{len(blocks)}]: {block_name_plural}")

    for i, file in enumerate(files, start=1):
        file_abs = path.join(pack, file)

        if path.exists(path.dirname(file_abs)):
            # Removes file
            if path.isfile(file_abs):
                os.remove(file_abs)
                logging.info(f"Removed file [{i}/{len(files)}]: {file_abs}")
            # Removes folder
            else:
                shutil.rmtree(file_abs)
                logging.info(f"Removed folder [{i}/{len(files)}]: {file_abs}")
        else:
            logging.error(f"File couldn't be found: {file_abs}")


# Contains multiple patches
def _patch_multi(pack, patch, logger_name: str):
    patches = patch.patch

    for patch_data in patches:
        patch_pack(pack, Patch(patch_data, patch.name), logger_name)


def _get_json_file(file_dir: str) -> dict:
    if path.isfile(file_dir) and path.exists(file_dir):
        with open(file_dir, "r") as file:
            return json.load(file)


def _set_json_file(file_dir: str, data: dict):
    if path.isfile(file_dir) and path.exists(file_dir):
        with open(file_dir, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent="\t")


def _set_json(root: Union[list, dict], location: list, data, merge: bool, add: bool) -> dict:
    if len(location) > 1:
        if location[0] == "*":
            if isinstance(root, dict):
                for key in root.keys():
                    root[key] = _set_json(root[key], location[1:], data, merge, add)
            elif isinstance(root, list):
                for i in range(len(root)):
                    root[i] = _set_json(root[i], location[1:], data, merge, add)
        else:
            if location[0] in root:
                root[location[0]] = _set_json(root[location[0]], location[1:], data, merge, add)
            elif bool:
                # If the location does not exist, then it won't attempt a merge (faster).
                new_json = data

                location.reverse()

                for key in location:
                    new_json = {key: new_json}

                root |= new_json
    else:
        if location[0] == "*":
            if isinstance(root, dict):
                for key in root.keys():
                    root[key] = data
            elif isinstance(root, list):
                for i in range(len(root)):
                    root[i] = data
        else:
            if merge and isinstance(data, dict) and isinstance(root[location[0]], dict):
                root[location[0]] |= data
            else:
                root[location[0]] = data
    return root


def _replace_json(root: Union[list, dict], location: list, select: str, replacement: str) -> dict:
    if len(location) > 1:
        if location[0] == "*":
            if isinstance(root, dict):
                for key in root.keys():
                    root[key] = _replace_json(root[key], location[1:], select, replacement)
            elif isinstance(root, list):
                for i in range(len(root)):
                    root[i] = _replace_json(root[i], location[1:], select, replacement)
        else:
            # Checks if the key exits
            if location[0] in root:
                root[location[0]] = _replace_json(root[location[0]], location[1:], select, replacement)
    else:
        if location[0] == "*":
            if isinstance(root, dict):
                for key, value in root.items():
                    root[key] = re.sub(select, replacement, value)
            elif isinstance(root, list):
                for value, i in iter(root):
                    root[i] = re.sub(select, replacement, value)
        elif isinstance(root, dict):
            root[location[0]] = re.sub(select, replacement, root[location[0]])
    return root


def _check_json_node(root: dict, location: list) -> bool:
    # For the case that we have an empty element
    if root is None:
        return False

    # Check existence of the first key
    if location[0] in root:

        # if this is the last key in the list, then no need to look further
        if len(location) == 1:
            return True
        else:
            next_value = location[1:len(location)]
            return _check_json_node(root[location[0]], next_value)
    else:
        return False


MIXIN_FILE_SELECTOR_TYPE_FILE = "file"
MIXIN_FILE_SELECTOR_TYPE_PATH = "path"


class MixinFileSelector:
    def __init__(self, selector_type: str, arguments: dict, pack):
        self.selector_type = selector_type
        self.arguments = arguments
        self.pack = pack

    def run(self, logger: logging.Logger) -> Union[List[str], None]:
        if self.selector_type == MIXIN_FILE_SELECTOR_TYPE_FILE:
            return self.arguments["files"]
        elif self.selector_type == MIXIN_FILE_SELECTOR_TYPE_PATH:
            file_path = self.arguments["path"]

            recursive = False
            if "recursive" in self.arguments:
                recursive = self.arguments["recursive"]

            files = glob(os.path.join(self.pack, file_path, "*"), recursive=recursive)

            if "regex" in self.arguments:
                regex = re.compile(self.arguments["regex"])

                sorted_files = []
                for file in files:
                    if regex.match(os.path.relpath(file, os.path.join(self.pack, file_path))) is not None:
                        sorted_files.append(os.path.relpath(file, self.pack))
                return sorted_files
            else:
                return files
        else:
            logger.error(f"Incorrect file selector type: {self.selector_type}")
            return

    @staticmethod
    def parse(data: dict, pack):
        return MixinFileSelector(data["type"], data["arguments"], pack)


MIXIN_SELECTOR_TYPE_PATH = "path"


class MixinSelector:
    def __init__(self, selector_type: str, arguments: dict):
        self.selector_type = selector_type
        self.arguments = arguments

    def run(self, json_data, logger: logging.Logger) -> Union[list, None]:
        if self.selector_type == MIXIN_SELECTOR_TYPE_PATH:
            location = str(self.arguments["location"]).split("/")
            return location
        else:
            logger.error(f"Incorrect selector type: {self.selector_type}")

    @staticmethod
    def parse(data: dict):
        return MixinSelector(data["type"], data["arguments"])


MIXIN_MODIFIER_TYPE_SET = "set"
MIXIN_MODIFIER_TYPE_REPLACE = "replace"


class MixinModifier:
    def __init__(self, modifier_type: str, arguments: dict):
        self.modifier_type = modifier_type
        self.arguments = arguments

    def run(self, file_directory: str, file: dict, json_directory: list, logger: logging.Logger):
        modified_file = file

        if self.modifier_type == MIXIN_MODIFIER_TYPE_SET:
            merge = False
            if "merge" in self.arguments:
                merge = self.arguments["merge"]

            add = True
            if "add" in self.arguments:
                merge = self.arguments["add"]

            modified_file = _set_json(file, json_directory, self.arguments["data"], merge, add)
        elif self.modifier_type == MIXIN_MODIFIER_TYPE_REPLACE:
            modified_file = _replace_json(file, json_directory, self.arguments["select"], self.arguments["replacement"])
        else:
            logger.error(f"Incorrect modifier type: {self.modifier_type}")

        _set_json_file(file_directory, modified_file)

    @staticmethod
    def parse(data: list):
        modifiers = []
        for modifier in data:
            modifiers.append(MixinModifier(modifier["type"], modifier["arguments"]))
        return modifiers


class Mixin:
    def __init__(self, file_selector: MixinFileSelector, selector: MixinSelector, modifiers: List[MixinModifier], pack: str):
        self.file_selector = file_selector
        self.selector = selector
        self.modifiers = modifiers
        self.pack = pack

    def run(self, logger):
        files = self.file_selector.run(logger)
        for file in files:
            file_path = os.path.join(self.pack, file)
            file_data = _get_json_file(file_path)

            # Checks if file exists
            if file_data is None:
                logger.error(f"File couldn't be found: {file_path}")
                return

            json_directory = self.selector.run(file_data, logger)

            for modifier in self.modifiers:
                modifier.run(file_path, file_data, json_directory, logger)

    @staticmethod
    def parse(data: dict, pack: str):
        return Mixin(MixinFileSelector.parse(data["file_selector"], pack),
                     MixinSelector.parse(data["selector"]),
                     MixinModifier.parse(data["modifiers"]), pack)


# Allows json files to be edited
def _patch_mixin_json(pack: str, patch: Patch, logger: logging.Logger):
    mixins = patch.patch["mixins"]

    for i, data in enumerate(mixins, start=1):
        mixin = Mixin.parse(data, pack)
        logger.info(f"Completed mixin [{i}/{len(mixins)}]")
        mixin.run(logger)


PATCH_TYPE_REPLACE = "replace"
PATCH_TYPE_REMOVE = "remove"
PATCH_TYPE_MULTI = "multi"
PATCH_TYPE_MIXIN_JSON = "mixin_json"


def patch_pack(pack: str, patch: Patch, logger_name: str):
    logger = logging.getLogger(f"{logger_name}\x1b[0m/\x1b[34mPatching\x1b[0m")
    if patch.type == PATCH_TYPE_REPLACE:
        _patch_replace(pack, patch, logger)
    elif patch.type == PATCH_TYPE_REMOVE:
        _patch_remove(pack, patch, logger)
    elif patch.type == PATCH_TYPE_MULTI:
        _patch_multi(pack, patch, logger_name)
    elif patch.type == PATCH_TYPE_MIXIN_JSON:
        _patch_mixin_json(pack, patch, logger)
    else:
        logger.error(f"Incorrect patch type: {patch.type}")
