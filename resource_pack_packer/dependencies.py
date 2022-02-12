import logging
import os
import requests
import shutil

from glob import glob
from typing import List

from resource_pack_packer import settings
from resource_pack_packer.configs import PackInfo
from resource_pack_packer.settings import MAIN_SETTINGS


logger = logging.getLogger("Setup")

URL_CURSEFORGE = "https://api.curseforge.com"


class Mod:
    def __init__(self, name: str, project: int, file: int, assets: List[str]):
        self.name = name
        self.project = project
        self.file = file
        self.assets = assets
        self.directory = ""
        self.file_name = ""

    def download(self):
        temp = os.path.join(MAIN_SETTINGS.working_directory, MAIN_SETTINGS.temp_dir)

        # Make dirs
        if not os.path.exists(temp):
            os.makedirs(temp)

        # Download file
        # Get download link
        r = requests.get(f"{URL_CURSEFORGE}/v1/mods/{self.project}/files/{self.file}/download-url", headers={
            "accept": "application/json",
            "x-api-key": MAIN_SETTINGS.curseforge_token
        })

        download_url = r.json()["data"]

        self.file_name = f"{self.name}.{self.project}.{self.file}.jar"
        self.directory = os.path.join(temp, self.file_name)
        with requests.get(download_url, stream=True) as r:
            with open(self.directory, "wb") as f:
                shutil.copyfileobj(r.raw, f)

    def install(self, pack_dir: str):
        # Install mod
        shutil.copy(self.directory, os.path.join(MAIN_SETTINGS.minecraft_dir, "mods", self.file_name))

        # Extract
        temp_dir = os.path.join(MAIN_SETTINGS.working_directory,
                                MAIN_SETTINGS.temp_dir,
                                f"{self.name}.{self.project}.{self.file}")

        shutil.unpack_archive(self.directory, temp_dir, "zip")

        # Install to dev namespace
        for namespace in glob(os.path.join(temp_dir, "assets", "*")):
            namespace_name = os.path.basename(namespace)
            for asset in self.assets:
                asset_dir = os.path.join(temp_dir, "assets", namespace_name, asset)
                if os.path.exists(asset_dir):
                    shutil.move(asset_dir, os.path.join(pack_dir, "assets", f"rpp-{namespace_name}", asset))

    @staticmethod
    def parse(data: dict) -> "Mod":
        if "assets" in data:
            assets = data["assets"]
        else:
            assets = []

        return Mod(data["name"], data["project"], data["file"], assets)


def setup():
    # Pack info
    config_files = glob(os.path.join(MAIN_SETTINGS.working_directory, "configs", "*"))
    config_files_string = ""
    for config in config_files:
        config_files_string += f"- {os.path.basename(config.split('.')[0])}\n"

    pack_info = PackInfo.parse(input(f"Choose pack:\n{config_files_string}\n"))

    if not pack_info.mod_dependencies:
        logger.error("No dependencies found")
        return

    if MAIN_SETTINGS.curseforge_token is None:
        logger.error("Token not provided")
        return

    # Download
    for i, mod in enumerate(pack_info.mod_dependencies, start=1):
        mod.download()
        logger.info(f"Downloaded mod [{i}/{len(pack_info.mod_dependencies)}]: {mod.name}")

    # Preinstall
    if os.path.exists(os.path.join(MAIN_SETTINGS.minecraft_dir, "mods")):
        if any(os.scandir(os.path.join(MAIN_SETTINGS.minecraft_dir, "mods"))):
            mod_input = input("Mods already installed. Remove, keep, or backup? ").lower()
            if mod_input == "remove":
                shutil.rmtree(os.path.join(MAIN_SETTINGS.minecraft_dir, "mods"))
                logger.info("Cleared mods")
            elif mod_input == "keep":
                pass
            else:
                backup_dir = os.path.join(MAIN_SETTINGS.minecraft_dir, "mods-RPPBACKUP")
                shutil.move(os.path.join(MAIN_SETTINGS.minecraft_dir, "mods"), backup_dir)
                logger.info(f"Created backup mods to: {backup_dir}")

    if not os.path.exists(os.path.join(MAIN_SETTINGS.minecraft_dir, "mods")):
        os.makedirs(os.path.join(MAIN_SETTINGS.minecraft_dir, "mods"))

    # Install
    for i, mod in enumerate(pack_info.mod_dependencies, start=1):
        mod.install(settings.parse_dir_keywords(pack_info.directory))
        logger.info(f"Installed mod [{i}/{len(pack_info.mod_dependencies)}]: {mod.name}.{mod.project}.{mod.file}")

    shutil.rmtree(os.path.join(MAIN_SETTINGS.working_directory, MAIN_SETTINGS.temp_dir))
