import os
import shutil
from threading import Thread
from time import time

from configs import *
from patch import *
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

        version = input("Resource Pack Version: ")

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

        print(f"Time: {time() - start_time} Seconds")

    def _pack_dev(self, rerun=False):
        """Outputs a single config into your resource pack folder for development purposes"""
        if not rerun:
            self.pack = input("Pack Name: ")

        self.config_file = Configs(self.pack).data

        self.configs = self.config_file["configs"]

        self.pack_dir = parse_dir_keywords(self.config_file["directory"], self.PACK_FOLDER_DIR)

        print(f"Located Pack: {self.pack_dir}")

        if not rerun:
            self.config = input("Config: ")

        start_time = time()

        self._pack(self.config, "DEV", True)

        print(f"Time: {time() - start_time} Seconds")

        input("Hit enter to rerun")

        self._pack_dev(True)

    def _pack_manual(self):
        """Manually input the option to pack a resource pack"""
        self.pack = input("Pack Name: ")

        self.pack_dir = filter_selection(glob(path.join(self.PACK_FOLDER_DIR, "*")), self.pack)

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

        self.config_file = generate_config(path.basename(self.pack_dir), mc_version, delete_textures, ignore_folders, regenerate_meta, patches)

        self.configs = self.config_file["configs"]

        self._pack(mc_version, version)

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
        self._copy_pack(self.pack_dir, temp_pack_dir)

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

            patches = get_patches(self.configs[config], self.PACK_FOLDER_DIR)

            patcher = Patcher()

            for patch in patches:
                print(f"Applying: {patch.directory}")
                self.patch_pack(temp_pack_dir, patch.directory)

        # Zip
        if not dev:
            self._zip_pack(temp_pack_dir)

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
