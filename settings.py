import json
from os import path


def _parse_keyword(directory, keyword, variable):
    return path.normpath(directory.replace(f"#{keyword}", variable))


def parse_dir_keywords(directory, pack_folder_dir):
    directory = _parse_keyword(directory, "packdir", pack_folder_dir)
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
                        "pack_folder": path.normpath(
                            path.join(parse_dir(input("Minecraft Folder: ")), "resourcepacks")),
                        "temp": "temp",
                        "out": parse_dir(input("Output Folder: "))
                    }
                }
                json.dump(data, file, indent="\t")

        with open("settings.json", "r") as file:
            self.data = json.load(file)
