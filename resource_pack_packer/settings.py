import json
from os import path


def parse_keyword(directory, keyword, variable):
    return path.normpath(directory.replace(f"#{keyword}", variable))


def parse_dir_keywords(directory):
    directory = parse_keyword(directory, "packdir", MAIN_SETTINGS.pack_folder)
    return parse_dir(directory)


def parse_dir(directory):
    return path.normpath(path.abspath(path.expanduser(directory)))


class Settings:
    def __init__(self):
        # Generates settings file if not found
        if not path.exists("settings.json"):
            with open("settings.json", "x") as file:
                data = {
                    "locations": {
                        "pack_folder": path.normpath(path.join(parse_dir(input("Minecraft Folder: ")), "resourcepacks")),
                        "temp": "temp",
                        "out": parse_dir(input("Output Folder: ")),
                        "patch": "patches"
                    },
                    "api_tokens": {
                        "curseforge": ""
                    }
                }
                json.dump(data, file, indent="\t")

        with open("settings.json", "r") as file:
            data = json.load(file)
            self.pack_folder = parse_dir(data["locations"]["pack_folder"])
            self.temp_dir = parse_dir(data["locations"]["temp"])
            self.out_dir = parse_dir(data["locations"]["out"])
            self.patch_dir = parse_dir(data["locations"]["patch"])
            self.curseforge = data["api_tokens"]["curseforge"]


MAIN_SETTINGS = Settings()
