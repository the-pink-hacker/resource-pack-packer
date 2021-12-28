import json
import os
import shutil
from glob import glob
from os import path

from typing import List, Union

from resource_pack_packer.settings import MAIN_SETTINGS, parse_dir_keywords

PATCH_TYPE_REPLACE = "replace"
PATCH_TYPE_REMOVE = "remove"
PATCH_TYPE_MULTI = "multi"
PATCH_TYPE_MIXIN_JSON = "mixin_json"


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
    files = patch.patch["files"]
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


def _set_json_node(root: dict, location: list, data) -> dict:
    if len(location) > 1:
        if location[0] in root:
            root[location[0]] = _set_json_node(root[location[0]], location[1:], data)
        else:
            # If the location does not exist, then it won't attempt a merge (faster).
            new_json = data

            location.reverse()

            for key in location:
                new_json = {key: new_json}

            root = root | new_json
    else:
        root[location[0]] = data
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


MIXIN_SELECTOR_TYPE_PATH = "path"
MIXIN_SELECTOR_TYPE_LIST = "list"
MIXIN_SELECTOR_TYPE_CONTENT = "content"


class MixinSelector:
    def __init__(self, selector_type: str, arguments: dict):
        self.selector_type = selector_type
        self.arguments = arguments

    def run(self, json_data) -> Union[list, None]:
        if self.selector_type == MIXIN_SELECTOR_TYPE_PATH:
            location = str(self.arguments["location"]).split("/")
            return location
        elif self.selector_type == MIXIN_SELECTOR_TYPE_LIST:
            pass
        elif self.selector_type == MIXIN_SELECTOR_TYPE_CONTENT:
            pass
        return None

    @staticmethod
    def parse(data: dict):
        return MixinSelector(data["type"], data["arguments"])


MIXIN_MODIFIER_TYPE_SET = "set"
MIXIN_MODIFIER_TYPE_MERGE = "merge"
MIXIN_MODIFIER_TYPE_APPEND = "append"
MIXIN_MODIFIER_TYPE_REPLACE = "replace"


class MixinModifier:
    def __init__(self, modifier_type: str, arguments: dict):
        self.modifier_type = modifier_type
        self.arguments = arguments

    def run(self, file_directory: str, file: dict, json_directory: list):
        modified_file = file

        if self.modifier_type == MIXIN_MODIFIER_TYPE_SET:
            modified_file = _set_json_node(file, json_directory, self.arguments["data"])
        elif self.modifier_type == MIXIN_MODIFIER_TYPE_MERGE:
            pass
        elif self.modifier_type == MIXIN_MODIFIER_TYPE_APPEND:
            pass
        elif self.modifier_type == MIXIN_MODIFIER_TYPE_REPLACE:
            pass

        _set_json_file(file_directory, modified_file)

    @staticmethod
    def parse(data: list):
        modifiers = []
        for modifier in data:
            modifiers.append(MixinModifier(modifier["type"], modifier["arguments"]))
        return modifiers


class Mixin:
    def __init__(self, files: List[str], selector: MixinSelector, modifiers: List[MixinModifier], pack: str):
        self.files = files
        self.selector = selector
        self.modifiers = modifiers

        for file in self.files:
            file_data = _get_json_file(os.path.join(pack, file))

            json_directory = self.selector.run(file_data)

            for modifier in self.modifiers:
                modifier.run(os.path.join(pack, file), file_data, json_directory)

    @staticmethod
    def parse(data: dict, pack: str):
        return Mixin(data["files"], MixinSelector.parse(data["selector"]), MixinModifier.parse(data["modifiers"]), pack)


# Allows json files to be edited
def _patch_mixin_json(pack: str, patch: Patch):
    mixins = patch.patch["mixins"]

    for data in mixins:
        mixin = Mixin.parse(data, pack)


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
