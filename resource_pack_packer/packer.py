import json
import logging
import os
import shutil
import zipfile
from glob import glob
from multiprocessing import pool
from os import path
from threading import Thread
from timeit import default_timer
from typing import Union

from resource_pack_packer.configs import PackInfo, parse_name_scheme_keywords, Config, RunOptions
from resource_pack_packer.settings import MAIN_SETTINGS, parse_dir_keywords


def zip_dir(src, dest):
    if not path.exists(path.dirname(dest)):
        os.makedirs(path.dirname(dest))

    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(src):
            for file in files:
                zip_file.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), src))


def minify_json(directory):
    if directory.endswith(".json"):
        with open(directory, "r", encoding="utf8") as json_file:
            data = json.load(json_file)

        with open(directory, "w", encoding="utf8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=None)


class Packer:
    def __init__(self, pack=None, parent=None):
        self.configs: Union[str, None] = None
        self.PACK_FOLDER_DIR = MAIN_SETTINGS.pack_folder
        self.TEMP_DIR = parse_dir_keywords(os.path.join(MAIN_SETTINGS.working_directory, MAIN_SETTINGS.temp_dir))
        self.OUT_DIR = parse_dir_keywords(os.path.join(MAIN_SETTINGS.working_directory, MAIN_SETTINGS.out_dir))
        self.PATCH_DIR = parse_dir_keywords(os.path.join(MAIN_SETTINGS.working_directory, MAIN_SETTINGS.patch_dir))

        self.PACK_OVERRIDE = pack is not None

        if self.PACK_OVERRIDE:
            self.pack = pack
            self.parent = parent
        else:
            self.pack = None

        self.logger = logging.getLogger("Packing")

    def start(self, pack_overide: Union[str, None] = None, run_option_overide: Union[str, None] = None):
        # Pack info
        config_files = glob(path.join(MAIN_SETTINGS.working_directory, "configs", "*"))
        config_files_string = ""
        for config in config_files:
            config_files_string += f"- {os.path.basename(config.split('.')[0])}\n"

        if pack_overide is None:
            selected_pack_name = input(f"Choose pack:\n{config_files_string}\n")
        else:
            selected_pack_name = pack_overide

        self.pack_info = PackInfo.parse(selected_pack_name)
        self.pack_dir = parse_dir_keywords(self.pack_info.directory)
        self.logger = logging.getLogger(os.path.basename(self.pack_dir))
        self.logger.info(f"Located Pack: {self.pack_dir}")

        # Run options
        run_options_string = ""
        for run_option in self.pack_info.run_options:
            run_options_string += f"- {run_option.name}\n"
        if run_option_overide is None:
            selected_run_option = input(f"Choose run option:\n{run_options_string}\n")
        else:
            selected_run_option = run_option_overide

        self.run_option = self.pack_info.get_run_option(selected_run_option)

        if self.run_option.version is not None:
            self.version = self.run_option.version
        else:
            self.version = input("Resource pack version: ")

        # Config
        self.configs = self.run_option.get_configs(self.pack_info.configs, self.logger)

        # Pack
        if self.run_option.out_dir == MAIN_SETTINGS.out_dir:
            self.clear_temp()

        self.clear_out()
        start_time = default_timer()

        if len(self.configs) > 1:
            with pool.Pool(processes=os.cpu_count()) as p:
                p.map(self._pack, self.configs)
        else:
            self._pack(self.configs[0])

        self.logger.info(f"Time: {default_timer() - start_time} Seconds")

        # Rerun
        if self.run_option.rerun:
            input("\nPress enter to rerun...")
            self.start(selected_pack_name, selected_run_option)

    def _pack(self, config: Config):
        pack_name = parse_name_scheme_keywords(self.pack_info.name_scheme, path.basename(self.pack_dir), self.version,
                                               config.mc_version)
        logger = logging.getLogger(f"{os.path.basename(self.pack_dir)}\x1b[0m/\x1b[34m{config.name}\x1b[0m")

        temp_pack_dir = path.join(self.TEMP_DIR, pack_name)

        # Overrides output
        if self.run_option.out_dir != MAIN_SETTINGS.out_dir:
            temp_pack_dir = path.join(parse_dir_keywords(self.run_option.out_dir), pack_name)
            self.clear_temp(temp_pack_dir)

        # Copy Files
        logger.info("Copying...")
        self._copy_pack(self.pack_dir, temp_pack_dir)

        # Delete Textures
        if config.delete_textures:
            logger.info("Deleting textures...")
            self.delete(temp_pack_dir, "textures", config.ignore_textures, logger)

        # Generate Meta
        with open(os.path.join(temp_pack_dir, "pack.mcmeta"), "w") as file:
            meta = {
                "pack": {
                    "pack_format": config.pack_format,
                    "description": self.pack_info.description
                }
            }
            if config.minify_json and self.run_option.minify_json:
                indent = None
            else:
                indent = 2
            json.dump(meta, file, ensure_ascii=False, indent=indent)

        # Minify Json
        if config.minify_json and self.run_option.minify_json:
            logger.info("Minifying json files...")
            self.minify_json_files(temp_pack_dir)

        # Patch
        if len(config.patches) > 0:
            logger.info(f"Applying patches...")

            for patch in config.patches:
                patch.run(temp_pack_dir, logger.name, self.pack_info, config)

        # Delete Empty Folders
        if config.delete_empty_folders:
            directories = glob(path.join(temp_pack_dir, "**"), recursive=True)

            for directory in directories:
                if path.isdir(directory) and path.exists(directory):
                    if len(glob(path.join(directory, "**"), recursive=True)) == 1:
                        os.remove(directory)

        # Zip
        if self.run_option.zip_pack:
            output = path.normpath(path.join(self.OUT_DIR, pack_name + ".zip"))
            zip_dir(temp_pack_dir, output)
            logger.info(f"Completed pack: {output}")

    def _copy_pack(self, src: str, dest: str):
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

    def delete(self, directory, folder, ignore, logger: logging.Logger):
        namespaces = glob(path.join(directory, "assets", "*"))

        for i, namespace in enumerate(namespaces, start=1):
            if path.exists(path.join(namespace, folder)):
                folders = glob(path.join(namespace, folder, "*"))

                for fold in folders:
                    delete_files = True
                    for ig in ignore:
                        if path.basename(fold) == ig.lower():
                            delete_files = False

                    if delete_files:
                        shutil.rmtree(fold)
                logger.info(f"Deleted texture [{i}/{len(namespaces)}]: {path.basename(namespace)}")

    def minify_json_files(self, temp_pack_dir):
        files = glob(path.join(temp_pack_dir, "**"), recursive=True)

        for file in files:
            minify_json(file)

    def clear_temp(self, directory=None):
        """Clears the temp folder"""
        if directory is None:
            directory = self.TEMP_DIR

        if path.exists(directory):
            self.logger.info("Clearing Temp...")
            shutil.rmtree(directory)

    def clear_out(self):
        """Clears the out folder"""
        if path.exists(self.OUT_DIR):
            self.logger.info("Clearing Out...")
            shutil.rmtree(self.OUT_DIR)
