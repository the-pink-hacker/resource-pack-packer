import json
from glob import glob
from os import path


def _get_config_file(pack):
    files = glob(path.join("configs", "*"))

    for file in files:
        if pack.lower() == path.splitext(path.basename(file))[0].replace("_", " ").lower():
            return path.abspath(file)


def generate_config(mc_version, delete_textures, ignore_folders, regenerate_meta, patches):
    data = {
        mc_version: {
            "mc_version": mc_version,
            "textures": {
                "delete": delete_textures,
                "ignore": ignore_folders
            },
            "regenerate_meta": regenerate_meta,
            "patches": patches
        }
    }

    return data


def check_option(root, option):
    if option in root:
        return True
    else:
        return False


class Configs:
    def __init__(self, pack):
        with open(_get_config_file(pack)) as file:
            self.data = json.load(file)
