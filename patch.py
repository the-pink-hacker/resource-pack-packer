import json
import os
import shutil
from glob import glob
from os import path

from settings import parse_dir_keywords

PATCH_TYPE_REPLACE = "replace"
PATH_TYPE_REMOVE = "remove"


def get_patches(config):
    patches = []

    for patch in config["patches"]:
        patches.append(Patch(patch))

    return patches


class Patch:
    def __init__(self, patch):
        with open(path.join("patches", f"{patch}.json")) as file:
            data = json.load(file)
            self.patch = data["patch"]
            self.type = data["type"]


# Replaces and adds files accordingly
def _patch_replace(pack, patch, resource_pack_dir):
    patch_dir = parse_dir_keywords(patch.patch["directory"], resource_pack_dir)
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


# Removes all specified files
def _patch_remove(pack, patch):
    files = patch.patch["files"]

    for file in files:
        file_abs = path.join(pack, file)

        # Removes file
        if path.isfile(file_abs) and path.exists(path.dirname(file_abs)):
            os.remove(file_abs)
            print(f"removed: {file_abs}")

        # Removes folder
        if path.exists(file_abs):
            shutil.rmtree(file_abs)


def patch_pack(pack, patch, resource_pack_dir):
    if patch.type == PATCH_TYPE_REPLACE:
        _patch_replace(pack, patch, resource_pack_dir)
    elif patch.type == PATH_TYPE_REMOVE:
        _patch_remove(pack, patch)
