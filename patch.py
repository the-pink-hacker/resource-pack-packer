import json
from os import path

from settings import parse_dir_keywords

PATCH_TYPE_REPLACE = "replace"


def get_patches(config, resource_pack_dir):
    patches = []

    for patch in config["patches"]:
        patches.append(Patch(patch, resource_pack_dir))

    return patches


class Patch:
    def __init__(self, patch, resource_pack_dir):
        with open(path.join("patches", f"{patch}.json")) as file:
            data = json.load(file)
            self.directory = parse_dir_keywords(data["directory"], resource_pack_dir)
            self.type = data["type"]


class Patcher:
    def __init__(self):
        pass
