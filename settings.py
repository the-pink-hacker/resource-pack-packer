import json
from os import path


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
                            path.join(path.abspath(path.expanduser(input("Minecraft Folder: "))), "resourcepacks")),
                        "temp": "temp",
                        "out": path.normpath(path.abspath(path.expanduser(input("Output Folder: "))))
                    }
                }
                json.dump(data, file, indent="\t")

        with open("settings.json", "r") as file:
            self.data = json.load(file)
