import json
from glob import glob
from os import path
from typing import List

from resource_pack_packer.settings import MAIN_SETTINGS
from resource_pack_packer.curseforge import CHANGELOG_TYPE_MARKDOWN
from resource_pack_packer.patch import get_patches, Patch
from resource_pack_packer.settings import parse_keyword


def parse_name_scheme_keywords(scheme, name, version, mc_version):
    scheme = parse_keyword(scheme, "name", name)
    scheme = parse_keyword(scheme, "version", version)
    scheme = parse_keyword(scheme, "mcversion", mc_version)
    return scheme


def _get_config_file(pack):
    files = glob(path.join(MAIN_SETTINGS.working_directory, "configs", "*"))

    for file in files:
        if pack.lower() == path.splitext(path.basename(file))[0].replace("_", " ").lower():
            return path.abspath(file)


def generate_pack_info(pack, pack_name, mc_version, delete_textures, ignore_folders, regenerate_meta, patches):
    data = {
        "directory": f"#packdir/{pack_name}",
        "name_scheme": "\u00A76\u00A7l#name v#version - #mcversion",
        "configs": {
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
    }

    return PackInfo(pack, data)


def check_option(root, option):
    if option in root:
        return True
    else:
        return False


class PackInfo:
    def __init__(self, pack_name, data=None):
        if data is None:
            with open(_get_config_file(pack_name)) as file:
                data = json.load(file)

        self.directory = data["directory"]
        self.name_scheme = data["name_scheme"]
        self.dependencies = []

        if check_option(data, "dev") and check_option(data["dev"], "dependencies"):
            self.dependencies = data["dev"]["dependencies"]

        self.configs = []

        for config in data["configs"]:
            self.configs.append(Config(data["configs"][config], config))

        self.curseforge_id = None
        self.curseforge_changelog_type = CHANGELOG_TYPE_MARKDOWN

        if check_option(data, "curseforge"):
            self.curseforge_id = data["curseforge"]["id"]

            if check_option(data["curseforge"], "changelog_type"):
                self.curseforge_id = data["curseforge"]["changelog_type"]


class Config:
    def __init__(self, config, name):
        self.name = name
        self.mc_version = config["mc_versions"][0]
        self.mc_versions = config["mc_versions"]
        self.delete_textures = config["textures"]["delete"]
        self.ignore_textures = config["textures"]["ignore"]

        self.delete_empty_folders = False

        if check_option(config, "delete_empty_folders"):
            self.delete_empty_folders = config["delete_empty_folders"]

        self.regenerate_meta = config["regenerate_meta"]

        self.minify_json = False

        if check_option(config, "minify_json"):
            self.minify_json = config["minify_json"]

        self.patches: List[Patch] = []

        if check_option(config, "patches"):
            self.patches = get_patches(config["patches"])
