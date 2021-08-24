import os
import shutil
from time import time
from glob import glob
from threading import Thread
from time import sleep

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
    def __init__(self, run_type, temp_dir, packs_dir, out_dir, packs):
        self.RUN_TYPE = run_type
        self.TEMP_DIR = temp_dir
        self.PACKS_DIR = packs_dir
        self.OUT_DIR = out_dir
        self.PACKS = packs

    def start(self):
        if self.RUN_TYPE == "config":
            self._pack_configs()
        elif self.RUN_TYPE == "manual":
            self._pack_manual()

    def _pack_configs(self):
        """Automatically packs a resource pack with the config file"""
        self.pack = input("Pack Name: ")

        self.pack_dir = filter_selection(self.PACKS, self.pack)

        print(f"Located Pack: {self.pack_dir}")

        version = input("Version: ")

        self.configs_settings = Configs.get_config(Configs().data, self.pack)

        clear_temp(self.TEMP_DIR)

        start_time = time()

        self.number_of_packers = 0

        for config in self.configs_settings:
            thread = Thread(target=self._config_pack, args=[config, version])
            thread.start()

        while self.number_of_packers > 0:
            sleep(0.1)

        self.zip_packs()

        print(f"Time: {time() - start_time} Seconds")

        clear_temp(self.TEMP_DIR)

    def _pack_manual(self):
        """Manually input the option to pack a resource pack"""
        pass

    def _config_pack(self, config, version):
        self.number_of_packers += 1
        pack_name = f"{path.basename(self.pack_dir)} v{version} - {config}"
        print(f"Config: {pack_name}")

        temp_pack_dir = path.join(self.TEMP_DIR, pack_name)

        print("Copying...")

        # Copy Files
        shutil.copytree(self.pack_dir, temp_pack_dir)

        # Delete Textures
        if Configs.check_option(self.configs_settings[config], "textures"):
            if Configs.check_option(self.configs_settings[config]["textures"], "delete") and \
                    self.configs_settings[config]["textures"]["delete"]:
                print("Deleting textures...")
                self.delete(temp_pack_dir, "textures", self.configs_settings[config]["textures"]["ignore"])

        # Regenerate Meta
        if Configs.check_option(self.configs_settings[config], "regenerate_meta") and self.configs_settings[config][
            "regenerate_meta"]:
            print("Regenerating meta...")
            self.regenerate_meta(temp_pack_dir, self.configs_settings[config]["mc_version"])

        # Patch
        if Configs.check_option(self.configs_settings[config], "patches") and len(
                self.configs_settings[config]["patches"]) > 0:
            print("Applying patches...")
            patches = self.configs_settings[config]["patches"]

            for patch in patches:
                print(f"Applying: {patch}")
                patch_dir = filter_selection(self.PACKS, patch)
                self.patch_pack(temp_pack_dir, patch_dir)

        self.number_of_packers -= 1

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

        for pack in packs:
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
