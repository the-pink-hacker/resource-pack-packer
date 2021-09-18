import os
import shutil
from time import time
from glob import glob
from threading import Thread
from time import sleep

from configs import *
from settings import *


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
    for pack in packs:
        # Checks for match
        if selected in pack:
            return pack
        # Checks for close match
        if selected.lower() in pack.lower():
            return pack
    print(f"Could not find: {selected}")
    return None


class Packer:
    def __init__(self, run_type, pack_folder_dir, temp_dir, out_dir):
        self.RUN_TYPE = run_type
        self.PACK_FOLDER_DIR = pack_folder_dir
        self.TEMP_DIR = temp_dir
        self.OUT_DIR = out_dir

    def start(self):
        if self.RUN_TYPE == "config":
            self._pack_configs()
        elif self.RUN_TYPE == "dev":
            self._pack_dev()
        elif self.RUN_TYPE == "manual":
            self._pack_manual()

    def _pack_configs(self):
        """Automatically packs a resource pack with the config file"""
        self.pack = input("Pack Name: ")

        self.config_file = Configs(self.pack).data

        self.configs = self.config_file["configs"]

        self.pack_dir = parse_dir_keywords(self.config_file["directory"], self.PACK_FOLDER_DIR)

        print(f"Located Pack: {self.pack_dir}")

        version = input("Version: ")

        clear_temp(self.TEMP_DIR)

        start_time = time()

        threads = []

        for config in self.configs:
            thread = Thread(target=self._pack, args=[config, version])
            threads.append(thread)
            thread.start()

        # Waits for all threads to finish
        for thread in threads:
            thread.join()

        self.zip_packs()

        print(f"Time: {time() - start_time} Seconds")

    def _pack_dev(self):
        """Outputs a single config into your resource pack folder for development purposes"""
        self.pack = input("Pack Name: ")

        self.config_file = Configs(self.pack).data

        self.configs = self.config_file["configs"]

        self.pack_dir = parse_dir_keywords(self.config_file["directory"], self.PACK_FOLDER_DIR)

        print(f"Located Pack: {self.pack_dir}")

        start_time = time()

        config = input("Config: ")

        self._pack(config, "DEV", True)

        print(f"Time: {time() - start_time} Seconds")

        self._pack_dev()

    def _pack_manual(self):
        """Manually input the option to pack a resource pack"""
        self.pack = input("Pack Name: ")

        self.pack_dir = filter_selection(self.PACKS, self.pack)

        print(f"Located Pack: {self.pack_dir}")

        version = input("Resource Pack Version: ")
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

        self.configs = generate_config(mc_version, delete_textures, ignore_folders, regenerate_meta, patches)

        self._pack(mc_version, version)

        self.zip_packs()

        print(f"Time: {time() - start_time} Seconds")

    def _pack(self, config, version, dev=False):
        pack_name = parse_name_scheme_keywords(self.config_file["name_scheme"], path.basename(self.pack_dir), version, self.configs[config]["mc_version"])
        print(f"Config: {pack_name}")

        temp_pack_dir = path.join(self.TEMP_DIR, pack_name)

        if dev:
            temp_pack_dir = path.join(self.PACK_FOLDER_DIR, pack_name)
            clear_temp(temp_pack_dir)

        print("Copying...")

        # Copy Files
        shutil.copytree(self.pack_dir, temp_pack_dir)

        # Delete Textures
        if check_option(self.configs[config], "textures"):
            if check_option(self.configs[config]["textures"], "delete") and \
                    self.configs[config]["textures"]["delete"]:
                print("Deleting textures...")
                self.delete(temp_pack_dir, "textures", self.configs[config]["textures"]["ignore"])

        # Regenerate Meta
        if check_option(self.configs[config], "regenerate_meta") and self.configs[config]["regenerate_meta"]:
            print("Regenerating meta...")
            self.regenerate_meta(temp_pack_dir, self.configs[config]["mc_version"])

        # Patch
        if check_option(self.configs[config], "patches") and len(self.configs[config]["patches"]) > 0:
            print("Applying patches...")
            patches = self.configs[config]["patches"]

            for patch in patches:
                print(f"Applying: {patch}")
                patch_dir = filter_selection(glob(path.join(self.PACK_FOLDER_DIR, "*"), recursive=False), patch)
                self.patch_pack(temp_pack_dir, patch_dir)

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

    def regenerate_meta(self, directory, version):
        pack_format = auto_pack(version)
        print(f"Pack Format: {pack_format}")

        with open(path.join(directory, "pack.mcmeta"), "r") as file:
            data = json.load(file)

        with open(path.join(directory, "pack.mcmeta"), "w", newline="\n") as file:
            if data["pack"]["pack_format"] != pack_format:
                data["pack"]["pack_format"] = pack_format

            json.dump(data, file, ensure_ascii=False, indent=2)

    def patch_pack(self, pack, patch):
        patch_files = glob(path.join(patch, "**"), recursive=True)

        for file in patch_files:
            # The location that the file should go to
            pack_file = file.replace(patch, pack)

            # Removes all files in pack that are in the patch
            if path.isfile(pack_file) and path.exists(pack_file):
                os.remove(pack_file)

            # Applies patch
            if path.isfile(file) and path.exists(file):
                try:
                    shutil.copy(file, pack_file)
                except IOError:
                    os.makedirs(path.dirname(pack_file))
                    shutil.copy(file, pack_file)

    def zip_packs(self):
        # Zip files
        print(f"Zipping...")

        packs = glob(path.join(self.TEMP_DIR, "*"))

        #threads = []

        for pack in packs:
            self._zip_pack(pack)
        #    thread = Thread(target=self._zip_pack, args=[pack])
        #    threads.append(thread)
        #    thread.start()

        # Waits for all threads to finish
        #for thread in threads:
        #    thread.join()

    def _zip_pack(self, pack):
        shutil.make_archive(pack, "zip", pack)

        pack_name = path.basename(pack)

        # Move to out dir
        if path.exists(path.normpath(path.join(self.OUT_DIR, pack_name + ".zip"))):
            os.remove(path.normpath(path.join(self.OUT_DIR, pack_name + ".zip")))
            shutil.move(path.normpath(pack + ".zip"), self.OUT_DIR)

            print(f"Completed pack sent to: {self.OUT_DIR}")
        else:
            shutil.move(path.normpath(pack + ".zip"), self.OUT_DIR)
            print(f"Completed pack sent to: {self.OUT_DIR}")
