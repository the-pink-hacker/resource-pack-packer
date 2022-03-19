import json
import logging
import os
import tkinter
from tkinter import filedialog

from resource_pack_packer.console import parse_dir

root = tkinter.Tk()
root.withdraw()

logger = logging.getLogger("SETTINGS")


def parse_keyword(directory, keyword, variable):
    return os.path.normpath(directory.replace(f"#{keyword}", variable))


def parse_dir_keywords(directory):
    directory = parse_keyword(directory, "packdir", os.path.join(MAIN_SETTINGS.get_property("locations", "minecraft"), "resourcepacks"))
    directory = parse_keyword(directory, "workdir", MAIN_SETTINGS.get_property("locations", "working_directory"))
    return parse_dir(directory)


def folder_dialog(title="Select Folder", directory=os.path.abspath(os.sep)):
    logging.info(f"Select Folder: {title}")
    return parse_dir(filedialog.askdirectory(title=title, initialdir=directory))


class Settings:
    def __init__(self, version):
        self._properties = {}
        self.add_property("meta", "version", version)

    def add_property(self, group: str, key: str, default=None):
        """
        Add a property to be stored in the settings
        :param group: A section of properties
        :param key: The name of the property
        :param default: The default value of the property
        """
        if group in self._properties:
            self._properties[group] |= {key: default}
        else:
            self._properties |= {group: {key: default}}

    def set_property(self, group: str, key: str, value):
        """
        Set the value of a property
        :param group: A section of properties
        :param key: The name of the property
        :param value: The value that the property will be set to
        """
        self._properties[group][key] = value

    def get_property(self, group: str, key: str):
        """
        Get the value of a property
        :param group: A section of properties
        :param key: The name of the property
        :return: The value stored in the property
        """
        if group in self._properties:
            if key in self._properties[group]:
                return self._properties[group][key]
            else:
                raise AttributeError(f"No property called '{key}' in '{group}'")
        else:
            raise AttributeError(f"No properties in {group}")

    def get_group(self, group: str):
        """
        Get the value of a property
        :param group: A section of properties
        :return: The value stored in the property
        """
        if group in self._properties:
            return self._properties[group]
        else:
            raise AttributeError(f"No properties in {group}")

    def save(self):
        with open("settings.json", "w", encoding="utf-8") as file:
            json.dump(self._properties, file, ensure_ascii=False, indent=2)
        logger.info(f"Saved settings to {os.path.abspath('settings.json')}")

    def load(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as file:
                settings_file = json.load(file)
            for group, properties in settings_file.items():
                for key, value in properties.items():
                    self.add_property(group, key, value)


MAIN_SETTINGS = Settings(0)

# Locations
MAIN_SETTINGS.add_property("locations", "minecraft")
MAIN_SETTINGS.add_property("locations", "temp", "temp")
MAIN_SETTINGS.add_property("locations", "out", "out")
MAIN_SETTINGS.add_property("locations", "working_directory")

# Run options
MAIN_SETTINGS.add_property("run_options", "dev", {
    "configs": "?",
    "minify_json": False,
    "delete_empty_folders": False,
    "zip_pack": False,
    "out_dir": "#packdir",
    "version": "DEV",
    "rerun": True,
    "validate": True
})
MAIN_SETTINGS.add_property("run_options", "build", {
    "configs": "*",
    "minify_json": True,
    "delete_empty_folders": True,
    "zip_pack": True
})
MAIN_SETTINGS.add_property("run_options", "build_single", {
    "configs": "?",
    "minify_json": True,
    "delete_empty_folders": True,
    "zip_pack": True
})

# API tokens
MAIN_SETTINGS.add_property("tokens", "curseforge")

# Load settings file
MAIN_SETTINGS.load()
MAIN_SETTINGS.save()
