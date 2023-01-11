import logging
import os
import tkinter
from tkinter import filedialog

from resource_pack_packer.console import parse_dir
from resource_pack_packer.lib.jsetting.settings import Settings

root = tkinter.Tk()
root.withdraw()

logger = logging.getLogger("SETTINGS")

# The location of the rpp
PROGRAM_PATH = os.path.dirname(os.path.dirname(__file__))

print(f"RPP Path: {PROGRAM_PATH}")


def parse_keyword(directory, keyword, variable):
    return os.path.normpath(directory.replace(f"#{keyword}", variable))


def parse_dir_keywords(directory):
    directory = parse_keyword(directory, "packdir", os.path.join(
        MAIN_SETTINGS.get_property("locations", "minecraft"), "resourcepacks"))
    directory = parse_keyword(directory, "workdir", MAIN_SETTINGS.get_property(
        "locations", "working_directory"))
    return parse_dir(directory)


def folder_dialog(title="Select Folder", directory=os.path.abspath(os.sep)):
    logging.info(f"Select Folder: {title}")
    return parse_dir(filedialog.askdirectory(title=title, initialdir=directory))


print(f"Settings Path: {os.path.join(PROGRAM_PATH, 'settings.json')}")

MAIN_SETTINGS = Settings(0, os.path.join(PROGRAM_PATH, "settings.json"))\
    .add_property("locations", "minecraft")\
    .add_property("locations", "temp", "temp")\
    .add_property("locations", "out", "out")\
    .add_property("locations", "working_directory")\
    .add_property("locations", "patch", "patches")\
    .add_property("run_options", "dev", {
        "configs": "?",
        "minify_json": False,
        "delete_empty_folders": False,
        "zip_pack": False,
        "out_dir": "#packdir",
        "version": "DEV",
        "rerun": True,
        "validate": True
    })\
    .add_property("run_options", "build", {
        "configs": "*",
        "minify_json": True,
        "delete_empty_folders": True,
        "zip_pack": True
    })\
    .add_property("run_options", "build_single", {
        "configs": "?",
        "minify_json": True,
        "delete_empty_folders": True,
        "zip_pack": True
    })\
    .add_property("tokens", "curseforge")

# Load settings file
MAIN_SETTINGS.load()
MAIN_SETTINGS.save()
