import json
import logging
import os
import zipfile

import requests
import shutil

from glob import glob
from typing import Optional

from resource_pack_packer.configs import PackInfo, RunOptions, Config
from resource_pack_packer.console import choose_from_list, add_to_logger_name
from resource_pack_packer.settings import MAIN_SETTINGS
from resource_pack_packer.util.cache import update_cache, check_cache

logger = logging.getLogger("Setup")

URL_CURSEFORGE = "https://api.curseforge.com"
URL_MINECRAFT_VERSION_INDEX = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"


def extract_jar(src: str, mc_version: str):
    out_dir = os.path.join(MAIN_SETTINGS.get_property("locations", "working_directory"), "dev", mc_version)
    with zipfile.ZipFile(src) as jar:
        for file in jar.namelist():
            if file.startswith("assets"):
                jar.extract(file, out_dir)


def download_file(url: str, dest: str):
    if not os.path.exists(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))

    with requests.get(url, stream=True) as r:
        with open(dest, "wb") as f:
            shutil.copyfileobj(r.raw, f)


class Mod:
    def __init__(self, name: str, project: int, file: int):
        self.name = name
        self.project = project
        self.file = file
        self.directory = ""
        self.file_name = ""

    def download(self, mod_cache: str) -> bool:
        download_dir = os.path.join(MAIN_SETTINGS.get_property("locations", "working_directory"), "dev", "src")
        self.file_name = f"{self.name}.{self.project}.{self.file}.jar"
        self.directory = os.path.join(download_dir, self.file_name)

        # Check if mod is already downloaded
        if check_cache(f"{self.name}.{self.project}.{self.file}", mod_cache):
            return False

        # Download file
        # Get download link
        r = requests.get(f"{URL_CURSEFORGE}/v1/mods/{self.project}/files/{self.file}/download-url", headers={
            "accept": "application/json",
            "x-api-key": MAIN_SETTINGS.get_property("tokens", "curseforge")
        })

        download_url = r.json()["data"]
        download_file(download_url, self.directory)

        return True

    def install(self, mc_version: str):
        extract_jar(self.directory, mc_version)

    @staticmethod
    def parse(data: dict) -> "Mod":
        return Mod(data["name"], data["project"], data["file"])


def install_version_from_index(index_dir: str) -> str:
    with open(index_dir, "r") as index_file:
        data = json.load(index_file)
    version_url = data["downloads"]["client"]["url"]
    out_dir = os.path.join(index_dir.replace(".json", ".jar"))
    download_file(version_url, out_dir)
    return out_dir


def setup(pack_override: Optional[str] = None, config_override: Optional[list[Config] | str] = None):
    # Pack info
    config_files = glob(os.path.join(MAIN_SETTINGS.get_property("locations", "working_directory"), "configs", "*"))
    config_file_names = list(map(lambda f: os.path.basename(f), config_files))

    if pack_override is None:
        selected_pack_name = choose_from_list(config_file_names, "Select pack:")[0]
    else:
        selected_pack_name = pack_override
    pack_info = PackInfo.parse(selected_pack_name)

    if config_override is None:
        config_selection = choose_from_list(["all", "select"], "Configs:")[0]
    else:
        config_selection = config_override

    if config_selection == "all":
        parsed_config_selection = "*"
    elif config_selection == "select":
        parsed_config_selection = "?"
    else:
        parsed_config_selection = config_selection

    # Run option is only used to select config
    run_option = RunOptions("setup", parsed_config_selection, False, False, False, "", "", False, False)
    configs = run_option.get_configs(pack_info.configs, logger)[0]

    for config in configs:
        installer_logger = add_to_logger_name(logger.name, str(config))

        # Minecraft version
        mc_jar = None
        # Check for installed versions
        for version in config.mc_versions:
            mc_jar_unchecked = os.path.join(
                MAIN_SETTINGS.get_property("locations", "minecraft"), "versions", version, f"{version}.jar")
            # Version installed
            if os.path.exists(mc_jar_unchecked) and os.path.isfile(mc_jar_unchecked):
                mc_jar = mc_jar_unchecked
                break

        # Install if version not installed
        if mc_jar is None:
            # Check if index for versions are preset
            for version in config.mc_versions:
                version_index = os.path.join(MAIN_SETTINGS.get_property("locations", "minecraft"), "versions", version, f"{version}.json")
                if os.path.exists(version_index):
                    mc_jar = install_version_from_index(version_index)
                    installer_logger.info(f"Installed Minecraft: {version}")
                    break

            # If no versions can be found
            if mc_jar is None:
                version_manifest = requests.get(URL_MINECRAFT_VERSION_INDEX, headers={"accept": "application/json"}).json()
                version_index = None
                for version in version_manifest["versions"]:
                    if version["id"] == config.mc_version:
                        version_index = version["url"]
                        break
                if version_index is not None:
                    index_dir = os.path.join(MAIN_SETTINGS.get_property("locations", "minecraft"), "versions", config.mc_version, f"{config.mc_version}.json")
                    download_file(version_index, index_dir)
                    mc_jar = install_version_from_index(index_dir)
                    installer_logger.info(f"Installed Minecraft: {config.mc_version}")
                else:
                    installer_logger.error(f"Version could not be found: {config.mc_version}")

        mc_version = os.path.basename(mc_jar).replace(".jar", "")

        mod_cache = os.path.join(MAIN_SETTINGS.get_property("locations", "working_directory"), "dev", "src", "cache.json")

        # Download
        for i, mod in enumerate(config.curseforge_dependencies, start=1):
            downloaded = mod.download(mod_cache)
            if downloaded:
                update_cache(f"{mod.name}.{mod.project}.{mod.file}", mod_cache)
                installer_logger.info(f"Downloaded mod [{i}/{len(config.curseforge_dependencies)}]: {mod.name}")
            else:
                installer_logger.info(f"Already downloaded mod [{i}/{len(config.curseforge_dependencies)}]: {mod.name}")

        # Preinstall
        if not os.path.exists(os.path.join(MAIN_SETTINGS.get_property("locations", "minecraft"), "mods")):
            os.makedirs(os.path.join(MAIN_SETTINGS.get_property("locations", "minecraft"), "mods"))

        # Clear dependencies
        if os.path.exists(os.path.join(MAIN_SETTINGS.get_property("locations", "working_directory"), "dev", mc_version, "assets")):
            shutil.rmtree(os.path.join(MAIN_SETTINGS.get_property("locations", "working_directory"), "dev", mc_version, "assets"))

        # Minecraft install
        extract_jar(mc_jar, mc_version)
        installer_logger.info(f"Installed Minecraft: {mc_version}")

        # Install
        for i, mod in enumerate(config.curseforge_dependencies, start=1):
            name = f"{mod.name}.{mod.project}.{mod.file}"
            mod.install(mc_version)
            installer_logger.info(f"Installed mod [{i}/{len(config.curseforge_dependencies)}]: {name}")

        logger.info("Completed setup")
