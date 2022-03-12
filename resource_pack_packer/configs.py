import json
import logging
import os
from glob import glob
from os import path
from typing import Union, List, Optional, Tuple

import resource_pack_packer.dependencies
from resource_pack_packer.console import choose_from_list
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

        if "selectors" in data and "block_files" in data["selectors"]:
            self.block_files: List[str] = data["selectors"]["block_files"]
        else:
            self.block_files = None

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

    @staticmethod
    def parse(pack_name: str) -> Optional["PackInfo"]:
        logger = logging.getLogger(pack_name)
        file_directory = path.join(MAIN_SETTINGS.working_directory, "configs", pack_name)
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

        self.mc_versions = config["mc_versions"]
        self.mc_versions.sort()
        self.mc_versions.reverse()

        self.mc_version = config["mc_versions"][0]

        if "textures" in config:
            self.delete_textures = config["textures"]["delete"]

            if "ignore" in config["textures"]:
                self.ignore_textures = config["textures"]["ignore"]
            else:
                self.ignore_textures = []
        else:
            self.delete_textures = False
            self.ignore_textures = []

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

        if "dependencies" in config and "curseforge" in config["dependencies"]:
            self.curseforge_dependencies = []
            for mod in config["dependencies"]["curseforge"]:
                self.curseforge_dependencies.append(resource_pack_packer.dependencies.Mod.parse(mod))
        else:
            self.curseforge_dependencies = []

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

    def __str__(self) -> str:
        return self.name


class RunOptions:
    def __init__(self, name: str, configs: Union[List[str], str], minify_json: bool, delete_empty_folders: bool,
                 zip_pack: bool, out_dir: str, version: Optional[str], rerun: bool, validate: bool):
        self.name = name
        self.configs = configs
        self.minify_json = minify_json
        self.delete_empty_folders = delete_empty_folders
        self.zip_pack = zip_pack
        self.out_dir = out_dir
        self.version = version
        self.rerun = rerun
        self.validate = validate

    def get_configs(self, configs: List[Config], logger: logging.Logger, config_override: Union[List[int], str, None] = None) -> Tuple[List[Config], List[int]]:
        selected_configs = []
        selected_config_indexes = []

        if config_override is None:
            # All configs
            if self.configs == "*":
                selected_configs = configs
                selected_config_indexes = "*"
            # Select config
            elif self.configs == "?":
                selected, i = choose_from_list(configs, "Select config:")
                selected_configs.append(selected)
                selected_config_indexes.append(i)
            # List of configs
            elif isinstance(self.configs, list) and len(self.configs) > 0:
                for i, config in enumerate(configs):
                    for name in self.configs:
                        if config.name == name:
                            selected_configs.append(config)
                            selected_config_indexes.append(i)
            else:
                logger.warning(f"couldn't find config(s): {self.configs}")
        else:
            if isinstance(config_override, list):
                for item in config_override:
                    selected_configs.append(configs[item])
            elif config_override == "*":
                selected_configs = configs
            selected_config_indexes = config_override
        return selected_configs, selected_config_indexes

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

            if "validate" in value:
                validate = value["validate"]
            else:
                validate = False

            run_options.append(RunOptions(
                key,
                value["configs"],
                value["minify_json"],
                value["delete_empty_folders"],
                value["zip_pack"],
                out_dir,
                version,
                rerun,
                validate
            ))
        return run_options

    def __str__(self) -> str:
        return self.name
