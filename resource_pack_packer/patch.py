import json
import os
import re
import shutil
from glob import glob
from os import path

from typing import List, Union

import billiard.pool

from resource_pack_packer.settings import MAIN_SETTINGS, parse_dir_keywords


def check_option(root, option):
    if option in root:
        return True
    else:
        return False


def get_patches(patch_names):
    patches = []

    for patch in patch_names:
        patches.append(Patch(get_patch_data(patch)))

    return patches


def get_patch_data(patch):
    with open(parse_dir_keywords(
            path.join(MAIN_SETTINGS.working_directory, MAIN_SETTINGS.patch_dir, f"{patch}.json"))) as file:
        return json.load(file)


class Patch:
    def __init__(self, data):
        self.patch = data["patch"]
        self.type = data["type"]


# Replaces and adds files accordingly
def _patch_replace(pack, patch):
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
def _patch_remove(pack, patch):
    files = []
    if "files" in patch.patch:
        files = patch.patch["files"]

    blocks = []
    if "blocks" in patch.patch:
        blocks = patch.patch["blocks"]

    for block in blocks:
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

        print(f"Removed Block: {block_name_plural}")

    for file in files:
        file_abs = path.join(pack, file)

        # Removes file
        if path.isfile(file_abs) and path.exists(path.dirname(file_abs)):
            os.remove(file_abs)
            print(f"removed: {file_abs}")

        # Removes folder
        if path.exists(file_abs):
            shutil.rmtree(file_abs)


# Contains multiple patches
def _patch_multi(pack, patch):
    patches = patch.patch

    for patch in patches:
        patch_pack(pack, Patch(patch))


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
        else:
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

    def run(self) -> Union[List[str], None]:
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
        return None

    @staticmethod
    def parse(data: dict, pack):
        return MixinFileSelector(data["type"], data["arguments"], pack)


MIXIN_SELECTOR_TYPE_PATH = "path"


class MixinSelector:
    def __init__(self, selector_type: str, arguments: dict):
        self.selector_type = selector_type
        self.arguments = arguments

    def run(self, json_data) -> Union[list, None]:
        if self.selector_type == MIXIN_SELECTOR_TYPE_PATH:
            location = str(self.arguments["location"]).split("/")
            return location

    @staticmethod
    def parse(data: dict):
        return MixinSelector(data["type"], data["arguments"])


MIXIN_MODIFIER_TYPE_SET = "set"
MIXIN_MODIFIER_TYPE_REPLACE = "replace"


class MixinModifier:
    def __init__(self, modifier_type: str, arguments: dict):
        self.modifier_type = modifier_type
        self.arguments = arguments

    def run(self, file_directory: str, file: dict, json_directory: list):
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

    def run(self):
        files = self.file_selector.run()
        for file in files:
            self._run_file(file)

    def _run_file(self, file):
        file_data = _get_json_file(os.path.join(self.pack, file))

        json_directory = self.selector.run(file_data)

        for modifier in self.modifiers:
            modifier.run(os.path.join(self.pack, file), file_data, json_directory)

    @staticmethod
    def parse(data: dict, pack: str):
        return Mixin(MixinFileSelector.parse(data["file_selector"], pack),
                     MixinSelector.parse(data["selector"]),
                     MixinModifier.parse(data["modifiers"]), pack)


# Allows json files to be edited
def _patch_mixin_json(pack: str, patch: Patch):
    mixins = patch.patch["mixins"]

    for data in mixins:
        mixin = Mixin.parse(data, pack)
        mixin.run()


PATCH_TYPE_REPLACE = "replace"
PATCH_TYPE_REMOVE = "remove"
PATCH_TYPE_MULTI = "multi"
PATCH_TYPE_MIXIN_JSON = "mixin_json"


def patch_pack(pack: str, patch: Patch):
    if patch.type == PATCH_TYPE_REPLACE:
        _patch_replace(pack, patch)
    elif patch.type == PATCH_TYPE_REMOVE:
        _patch_remove(pack, patch)
    elif patch.type == PATCH_TYPE_MULTI:
        _patch_multi(pack, patch)
    elif patch.type == PATCH_TYPE_MIXIN_JSON:
        _patch_mixin_json(pack, patch)
    else:
        print(f"Incorrect patch type: {patch.type}")
