import json
import logging
import os
from glob import glob
from os import path
from typing import Union, List

from resource_pack_packer.patch import PatchFile
from resource_pack_packer.settings import MAIN_SETTINGS
from resource_pack_packer.settings import parse_keyword


def parse_name_scheme_keywords(scheme, name, version, mc_version):
    scheme = parse_keyword(scheme, "name", name)
    scheme = parse_keyword(scheme, "version", version)
    scheme = parse_keyword(scheme, "mcversion", mc_version)
    return scheme


def _get_config_file(pack: str, logger: logging.Logger) -> str:
    files = glob(path.join(MAIN_SETTINGS.working_directory, "configs", "*"))

    file_dir = None

    for file in files:
        if pack.lower() == path.splitext(path.basename(file))[0].replace("_", " ").lower():
            file_dir = path.abspath(file)

    if file_dir is not None:
        return file_dir
    else:
        logger.error(f"Could not find config: {pack}")
        raise FileNotFoundError(f"Could not find config: {pack}")


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
    def __init__(self, pack_name: str, data: dict):
        logger = logging.getLogger(pack_name)

        self.directory = data["directory"]
        self.name_scheme = data["name_scheme"]

        if "description" in data:
            self.description = data["description"]
        else:
            self.description = ""
            logger.warning("Description is missing in pack info")

        if check_option(data, "dev") and check_option(data["dev"], "dependencies"):
            self.dependencies = data["dev"]["dependencies"]
        else:
            self.dependencies = []

        self.configs = []

        if "configs" in data:
            if len(data["configs"]) > 0:
                for config in data["configs"]:
                    self.configs.append(Config(data["configs"][config], config, logger))
            else:
                logger.error("No configs are detected")
        else:
            logger.error("Couldn't parse configs")

        if "run_options" in data:
            self.run_options = RunOptions.parse(data["run_options"])
        else:
            self.run_options = RunOptions.parse(MAIN_SETTINGS.run_options)

        if check_option(data, "curseforge"):
            self.curseforge_id = data["curseforge"]["id"]

            if check_option(data["curseforge"], "changelog_type"):
                self.curseforge_id = data["curseforge"]["changelog_type"]

    def get_run_option(self, name: str) -> Union["RunOptions", None]:
        for run_option in self.run_options:
            if run_option.name == name:
                return run_option
        # Default run options
        for run_option in MAIN_SETTINGS.run_options:
            if run_option.name == name:
                return run_option
        return None

    @staticmethod
    def parse(pack_name: str) -> Union["PackInfo", None]:
        logger = logging.getLogger(pack_name)
        file_directory = path.join(MAIN_SETTINGS.working_directory, "configs", f"{pack_name}.json")
        if os.path.exists(file_directory):
            with open(file_directory, "r") as file:
                data = json.load(file)
            return PackInfo(pack_name, data)
        else:
            logger.error(f"Couldn't find pack: {pack_name}")
            return None


class Config:
    def __init__(self, config: dict, name: str, logger: logging.Logger):
        self.name = name
        self.mc_version = config["mc_versions"][0]
        self.mc_versions = config["mc_versions"]
        self.delete_textures = config["textures"]["delete"]
        self.ignore_textures = config["textures"]["ignore"]

        self.delete_empty_folders = False

        if check_option(config, "delete_empty_folders"):
            self.delete_empty_folders = config["delete_empty_folders"]

        if "pack_format" not in config:
            self.pack_format = self.get_auto_pack_format()
        else:
            self.pack_format = config["pack_format"]

        self.minify_json = False

        if check_option(config, "minify_json"):
            self.minify_json = config["minify_json"]

        self.patches = []

        if check_option(config, "patches"):
            for patch in config["patches"]:
                self.patches.append(PatchFile.parse_file(
                    os.path.join(MAIN_SETTINGS.working_directory, MAIN_SETTINGS.patch_dir, f"{patch}.json"), patch,
                    logger))

    def get_auto_pack_format(self) -> int:
        version = int(self.mc_version.split(".")[1])
        if version >= 18:
            pack_format = 8
        elif version >= 17:
            pack_format = 7
        elif version >= 16:
            pack_format = 6
        elif version >= 15:
            pack_format = 5
        elif version >= 13:
            pack_format = 4
        elif version >= 11:
            pack_format = 3
        elif version >= 9:
            pack_format = 2
        elif version >= 6:
            pack_format = 1
        else:
            pack_format = 1
            logging.warning(f"Couldn't find correct pack format for: '{self.mc_version}'. Defaulting to: {pack_format}")
        return pack_format


class RunOptions:
    def __init__(self, name: str, configs: Union[List[str], str], minify_json: bool, delete_empty_folders: bool,
                 zip_pack: bool, out_dir: str, version: Union[str, None], rerun: bool):
        self.name = name
        self.configs = configs
        self.minify_json = minify_json
        self.delete_empty_folders = delete_empty_folders
        self.zip_pack = zip_pack
        self.out_dir = out_dir
        self.version = version
        self.rerun = rerun

    def get_configs(self, configs: List[Config], logger: logging.Logger) -> Union[
                    List[Config], None]:
        selected_configs = []

        # All configs
        if self.configs == "*":
            selected_configs = configs
        # Select config
        elif self.configs == "?":
            config_list = ""
            for config in configs:
                config_list += f"- {config.name}\n"
            name = input(f"Select Config:\n{config_list}\n")
            for config in configs:
                if config.name == name:
                    selected_configs.append(config)
        # List of configs
        elif isinstance(self.configs, list) and len(self.configs) > 0:
            for name in self.configs:
                for config in configs:
                    if config.name == name:
                        selected_configs.append(config)
        else:
            logger.warning(f"couldn't find config(s): {self.configs}")
            return None
        return selected_configs

    @staticmethod
    def parse(data: dict) -> List["RunOptions"]:
        run_options = []
        for key, value in data.items():
            if "out_dir" in value:
                out_dir = value["out_dir"]
            else:
                out_dir = MAIN_SETTINGS.out_dir

            if "version" in value:
                version = value["version"]
            else:
                version = None

            if "rerun" in value:
                rerun = value["rerun"]
            else:
                rerun = False

            run_options.append(RunOptions(
                key,
                value["configs"],
                value["minify_json"],
                value["delete_empty_folders"],
                value["zip_pack"],
                out_dir,
                version,
                rerun
            ))
        return run_options
