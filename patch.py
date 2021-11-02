import json
import os
import shutil
from glob import glob
from os import path

from settings import parse_dir_keywords, MAIN_SETTINGS

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
    with open(path.join(MAIN_SETTINGS.patch_dir, f"{patch}.json")) as file:
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


MIXIN_MODE_APPEND = "append"
MIXIN_MODE_SET = "set"
MIXIN_MODE_MERGE = "merge"


def _get_json_file(mixin, pack):
    file_dir = path.join(pack, mixin["file"])

    if path.isfile(file_dir) and path.exists(file_dir):
        with open(file_dir, "r") as file:
            return json.load(file)


def _set_json_file(mixin, pack, data):
    file_dir = path.join(pack, mixin["file"])

    if path.isfile(file_dir) and path.exists(file_dir):
        with open(file_dir, "w") as file:
            json.dump(data, file, ensure_ascii=False)


def _set_json_node(root, location, data, index=0):
    child_root = root[location[index]]

    if len(location) > index + 1:
        child_root[location[index + 1]] = _set_json_node(child_root, location, data, index=index + 1)
        return child_root
    else:
        return data


# Allows json files to be edited
def _patch_mixin_json(pack, patch):
    mixins = patch.patch["mixins"]

    for mixin in mixins:
        mode = mixin["mode"]

        file = _get_json_file(mixin, pack)
        modified_file = file

        if mode == MIXIN_MODE_APPEND:
            pass
        elif mode == MIXIN_MODE_SET:
            modified_file = _set_json_node(file, mixin["location"], mixin["data"])
        elif mode == MIXIN_MODE_APPEND:
            pass
        else:
            return

        _set_json_file(mixin, pack, modified_file)


def patch_pack(pack, patch):
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
