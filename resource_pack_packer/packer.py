import json
import os
import shutil
import zipfile
from glob import glob
from multiprocessing import Pool
from os import path
from threading import Thread
from time import time

from resource_pack_packer import curseforge
from resource_pack_packer.configs import PackInfo, generate_pack_info, parse_name_scheme_keywords
from resource_pack_packer.curseforge import UploadFileRequest
from resource_pack_packer.patch import patch_pack
from resource_pack_packer.settings import MAIN_SETTINGS, parse_dir_keywords


def _auto_pack_check(version, index):
    try:
        return int(version.split(".")[index])
    except IndexError:
        return 0


def auto_pack(version):
    version = str(version)
    if _auto_pack_check(version, 1) >= 17:
        return _auto_pack_check(version, 1) - 10
    elif _auto_pack_check(version, 1) == 16:
        return 6
    elif _auto_pack_check(version, 1) >= 15:
        return 5
    elif _auto_pack_check(version, 1) >= 13:
        return 4
    elif _auto_pack_check(version, 1) >= 11:
        return 3
    elif _auto_pack_check(version, 1) >= 9:
        return 2
    elif _auto_pack_check(version, 1) >= 7:
        return 1
    elif _auto_pack_check(version, 1) >= 6:
        if _auto_pack_check(version, 2) == 1:
            return 1
    return 0


def clear_temp(temp_dir):
    """Clears the temp folder"""
    if path.exists(temp_dir):
        print("Clearing Temp...")
        shutil.rmtree(temp_dir)


def filter_selection(packs, selected):
    """Finds the correct pack from a dir"""
    # Checks for match
    for pack in packs:
        if selected is path.basename(pack):
            return pack
    # Checks for close match
    for pack in packs:
        if selected in pack:
            return pack
    # Checks for close match
    for pack in packs:
        if selected.lower() in pack.lower():
            return pack
    print(f"Could not find: {selected}")
    return None


def zip_dir(src, dest):
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(src):
            for file in files:
                zip_file.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), src))


RUN_TYPE_CONFIG = "config"
RUN_TYPE_DEV = "dev"
RUN_TYPE_MANUAL = "manual"
RUN_TYPE_PUBLISH = "publish"


def minify_json(directory):
    with open(directory, "r", encoding="utf8") as json_file:
        data = json.load(json_file)

    with open(directory, "w", encoding="utf8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=None)


class Packer:
    def __init__(self, run_type, pack=None, parent=None):
        self.RUN_TYPE = run_type
        self.PACK_FOLDER_DIR = MAIN_SETTINGS.pack_folder
        self.TEMP_DIR = MAIN_SETTINGS.temp_dir
        self.OUT_DIR = MAIN_SETTINGS.out_dir
        self.PATCH_DIR = MAIN_SETTINGS.patch_dir

        self.PACK_OVERRIDE = pack is not None

        if self.PACK_OVERRIDE:
            self.pack = pack
            self.parent = parent
        else:
            self.pack = None

        self.publish = self.RUN_TYPE == RUN_TYPE_PUBLISH

        self.dev = self.RUN_TYPE == RUN_TYPE_DEV

    def start(self):
        if self.RUN_TYPE.lower() == RUN_TYPE_CONFIG:
            self._pack_configs()
        elif self.RUN_TYPE.lower() == RUN_TYPE_DEV:
            self._pack_dev()
        elif self.RUN_TYPE.lower() == RUN_TYPE_MANUAL:
            self._pack_manual()
        elif self.RUN_TYPE.lower() == RUN_TYPE_PUBLISH:
            self._pack_configs()

    def _pack_configs(self):
        """Automatically packs a resource pack with the config file"""
        if self.publish:
            if input("Publish to www.curseforge.com? Y/N\n").lower() != "y":
                publish = False
                print("Request canceled.")
            else:
                input("Hit 'ENTER' to continue and publish to curseforge...")

        self.pack = input("Pack Name: ")

        self.pack_info = PackInfo(self.pack)

        self.pack_dir = parse_dir_keywords(self.pack_info.directory)

        print(f"Located Pack: {self.pack_dir}")

        self.version = input("Resource Pack Version: ")

        if self.publish:
            self.release_type = input("Release Type ('alpha', 'beta', 'release'): ")

        clear_temp(self.TEMP_DIR)

        start_time = time()

        if self.publish:
            curseforge.init()

        with Pool(os.cpu_count()) as p:
            p.map(self._pack, self.pack_info.configs)

        print(f"Time: {time() - start_time} Seconds")

    def _pack_dev(self, rerun=False):
        """Outputs a single config into your resource pack folder for development purposes"""
        if not rerun:
            if not self.PACK_OVERRIDE:
                self.pack = input("Pack Name: ")

        self.pack_info = PackInfo(self.pack)

        self.pack_dir = parse_dir_keywords(self.pack_info.directory)

        print(f"Located Pack: {self.pack_dir}")

        if not rerun:
            if not self.PACK_OVERRIDE:
                self.config = input("Config: ")
            else:
                self.config = self.parent.config

        # Checks for dependencies and builds them
        if len(self.pack_info.dependencies) > 0:
            print(f"Packing {self.pack}'s dependencies...")

            for pack in self.pack_info.dependencies:
                print(f"Packing {pack}")
                packer = Packer(RUN_TYPE_DEV, pack.replace("_", " "), self)
                packer.start()

        start_time = time()

        self.version = "DEV"

        for config in self.pack_info.configs:
            if config.name == self.config:
                self._pack(config)

        print(f"{self.pack_dir} - Time: {time() - start_time} Seconds")

        if not self.PACK_OVERRIDE:
            input("Hit enter to rerun")
            self._pack_dev(True)

    def _pack_manual(self):
        """Manually input the option to pack a resource pack"""
        self.pack = input("Pack Name: ")

        self.pack_dir = filter_selection(glob(path.join(self.PACK_FOLDER_DIR, "*")), self.pack)

        print(f"Located Pack: {self.pack_dir}")

        self.version = input("Resource Pack Version: ")
        mc_version = input("Minecraft Version: ")
        delete_textures = input("Delete Textures? y/n: ").lower() == "y"

        ignore_folders = []

        if delete_textures:
            ignore_folders = input("\tIgnore Folders (use comma and space to separate): ").split(", ")

        regenerate_meta = input("Regenerate Meta? (pack format) y/n: ").lower() == "y"

        patches = []

        if input("Apply patches? y/n: ").lower() == "y":
            patches = input("\tPatches (use comma and space to separate): ").split(", ")

        clear_temp(self.TEMP_DIR)

        start_time = time()

        self.pack_info = generate_pack_info(self.pack, path.basename(self.pack_dir), mc_version, delete_textures,
                                            ignore_folders, regenerate_meta, patches)

        self._pack(self.pack_info.configs[0])

        print(f"Time: {time() - start_time} Seconds")

    def _pack(self, config):
        pack_name = parse_name_scheme_keywords(self.pack_info.name_scheme, path.basename(self.pack_dir), self.version,
                                               config.mc_version)
        print(f"Config: {pack_name}")

        temp_pack_dir = path.join(self.TEMP_DIR, pack_name)

        if self.dev:
            temp_pack_dir = path.join(self.PACK_FOLDER_DIR, pack_name)
            clear_temp(temp_pack_dir)

        print("Copying...")

        # Copy Files
        self._copy_pack(self.pack_dir, temp_pack_dir)

        # Delete Textures
        if config.delete_textures:
            print("Deleting textures...")
            self.delete(temp_pack_dir, "textures", config.ignore_textures)

        # Regenerate Meta
        if config.regenerate_meta:
            print("Regenerating meta...")
            if config.minify_json and not self.dev:
                self.regenerate_meta(temp_pack_dir, config.mc_version, indent=None)
            else:
                self.regenerate_meta(temp_pack_dir, config.mc_version)

        # Minify Json
        if config.minify_json and not self.dev:
            print("Minifying json files...")
            self.minify_json_files(temp_pack_dir)

        # Patch
        if len(config.patches) > 0:
            print("Applying patches...")

            for patch in config.patches:
                patch_pack(temp_pack_dir, patch)

        # Delete Empty Folders
        if config.delete_empty_folders:
            directories = glob(path.join(temp_pack_dir, "**"), recursive=True)

            for directory in directories:
                if path.isdir(directory) and path.exists(directory):
                    if len(glob(path.join(directory, "**"), recursive=True)) == 1:
                        os.remove(directory)

        # Zip
        if not self.dev:
            if self.publish:
                output = temp_pack_dir + ".zip"
            else:
                output = path.normpath(path.join(self.OUT_DIR, path.basename(temp_pack_dir) + ".zip"))

            self._zip_pack(temp_pack_dir, output)
            print(f"Completed pack: {output}")

            # Publish to CurseForge
            if self.publish:
                UploadFileRequest(self.pack_info, config, output, temp_pack_dir, pack_name, self.release_type).upload()

    def _copy_pack(self, src, dest):
        files = glob(path.join(src, "**"), recursive=True)

        copy_threads = []

        for file in files:
            if path.isfile(file):
                thread = Thread(target=self._copy_file, args=[src, dest, file])
                copy_threads.append(thread)
                thread.start()

        for thread in copy_threads:
            thread.join()

    def _copy_file(self, src, dest, file):
        file_dest = file.replace(src, dest)

        try:
            shutil.copy(file, file_dest)
        except IOError:
            try:
                os.makedirs(path.dirname(file_dest))
            except FileExistsError:
                pass
            shutil.copy(file, file_dest)

    def delete(self, directory, folder, ignore):
        namespaces = glob(path.join(directory, "assets", "*"))

        for namespace in namespaces:
            if path.exists(path.join(namespace, folder)):
                folders = glob(path.join(namespace, folder, "*"))

                for fold in folders:
                    delete_files = True
                    for ig in ignore:
                        if path.basename(fold) == ig.lower():
                            delete_files = False

                    if delete_files:
                        shutil.rmtree(fold)
                print(f"Deleted {path.basename(namespace)}'s Textures")

    def regenerate_meta(self, directory, version, indent=2):
        pack_format = auto_pack(version)
        print(f"Pack Format: {pack_format}")

        with open(path.join(directory, "pack.mcmeta"), "r") as file:
            data = json.load(file)

        with open(path.join(directory, "pack.mcmeta"), "w", newline="\n") as file:
            if data["pack"]["pack_format"] != pack_format:
                data["pack"]["pack_format"] = pack_format

            json.dump(data, file, ensure_ascii=False, indent=indent)

    def minify_json_files(self, temp_pack_dir):
        files = glob(path.join(temp_pack_dir, "**"), recursive=True)

        for file in files:
            if file.endswith(".json"):
                minify_json(file)

    def _zip_pack(self, pack, output):
        if path.exists(output):
            os.remove(output)

        zip_dir(pack, output)
