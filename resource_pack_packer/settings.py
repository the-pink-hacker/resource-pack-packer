import json
import os.path
from os import path
import tkinter
from tkinter import filedialog

root = tkinter.Tk()
root.withdraw()


def parse_keyword(directory, keyword, variable):
    return path.normpath(directory.replace(f"#{keyword}", variable))


def parse_dir_keywords(directory):
    directory = parse_keyword(directory, "packdir", MAIN_SETTINGS.pack_folder)
    directory = parse_keyword(directory, "workdir", MAIN_SETTINGS.working_directory)
    return parse_dir(directory)


def parse_dir(directory):
    return path.normpath(path.abspath(path.expanduser(directory)))


def folder_dialog(title="Select Folder", directory=os.path.abspath(os.sep)):
    print(f"Select Folder: {title}")
    return parse_dir(filedialog.askdirectory(title=title, initialdir=directory))


class Settings:
    def __init__(self):
        self.pack_folder = ""
        self.temp_dir = ""
        self.out_dir = ""
        self.patch_dir = ""
        self.curseforge = ""
        self.working_directory = ""

    def load(self):
        with open("settings.json", "r") as file:
            data = json.load(file)

        self.pack_folder = data["locations"]["pack_folder"]
        self.temp_dir = data["locations"]["temp"]
        self.out_dir = data["locations"]["out"]
        self.patch_dir = data["locations"]["patch"]
        self.working_directory = data["locations"]["working_directory"]
        self.curseforge = data["api_tokens"]["curseforge"]

        print(f"Working Dir: {self.working_directory}")

    def save(self):
        data = {
            "locations": {
                "pack_folder": self.pack_folder,
                "temp": self.temp_dir,
                "out": self.out_dir,
                "patch": self.patch_dir,
                "working_directory": self.working_directory
            },
            "api_tokens": {
                "curseforge": self.curseforge
            }
        }
        with open("settings.json", "w") as file:
            json.dump(data, file, indent="\t")


def get_settings() -> Settings:
    print("SETTINGS ARE BEING CREATED!!!")
    # Check if settings file has been created
    if path.exists("settings.json"):
        settings = Settings()
        settings.load()
        print(settings.patch_dir)
        return settings
    else:
        settings = Settings()
        settings.pack_folder = path.join(folder_dialog(title="Select Minecraft Directory"), "resourcepacks")
        settings.temp_dir = "temp"
        settings.out_dir = "out"
        settings.patch_dir = "patches"
        settings.working_directory = folder_dialog(title="Select Working Directory")
        settings.save()
        return settings


MAIN_SETTINGS = get_settings()
