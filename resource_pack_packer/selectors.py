import logging
import os
import re
from enum import Enum
from glob import glob
from typing import List, Optional


def parse_minecraft_identifier(identifier: str, folder: str, extension: str):
    """
    Parses a minecraft file path. Example:
    minecraft:block/sandstone -> assets/minecraft/models/block/sandstone.json
    :param identifier: A Minecraft identifier
    :param folder: The path from the namespace
    :param extension: The file extension
    :return: Relative path from resource pack
    """
    file_path = os.path.normpath(identifier)
    namespace_regex = re.compile("^[a-z]*(?=:)")
    namespace_match = re.match(namespace_regex, file_path)
    if namespace_match is not None:
        span = namespace_match.span()
        namespace = file_path[span[0]:span[1]]
        file_path = file_path.replace(f"{namespace}:", "")
    else:
        namespace = "minecraft"
    return os.path.join("assets", namespace, folder, f"{file_path}.{extension}")


class FileSelectorType(Enum):
    FILE = "file"
    PATH = "path"
    IDENTIFIER = "identifier"
    BLOCK = "block"


class FileSelector:
    def __init__(self, selector_type: str, arguments: dict, pack: str):
        self.selector_type = selector_type
        self.arguments = arguments
        self.pack = pack

    def run(self, logger: logging.Logger) -> Optional[List[str]]:
        match self.selector_type:
            case FileSelectorType.FILE.value:
                return self.arguments["files"]
            case FileSelectorType.PATH.value:
                file_path = self.arguments["path"]

                if "recursive" in self.arguments:
                    recursive = self.arguments["recursive"]
                else:
                    recursive = False

                files = glob(os.path.join(self.pack, file_path, "*"), recursive=recursive)

                if "regex" in self.arguments:
                    regex = re.compile(self.arguments["regex"])

                    sorted_files = []
                    for file in files:
                        if regex.match(os.path.relpath(file, os.path.join(self.pack, file_path))) is not None:
                            sorted_files.append(os.path.relpath(file, self.pack))
                    return sorted_files
                else:
                    return files
            case FileSelectorType.IDENTIFIER.value:
                if "models" in self.arguments:
                    models = self.arguments["models"]
                else:
                    models = []

                if "blocksates" in self.arguments:
                    blockstates = self.arguments["blockstates"]
                else:
                    blockstates = []

                if "lang" in self.arguments:
                    lang_files = self.arguments["lang"]
                else:
                    lang_files = []

                parsed_models = []

                for model in models:
                    parsed_models.append(os.path.join(self.pack, parse_minecraft_identifier(model, "models", "json")))

                parsed_blockstates = []

                for blockstate in blockstates:
                    parsed_blockstates.append(os.path.join(self.pack, parse_minecraft_identifier(blockstate, "blockstates", "json")))

                parsed_lang_files = []

                for lang_file in lang_files:
                    parsed_lang_files.append(os.path.join(self.pack, parse_minecraft_identifier(lang_file, "lang", "json")))

                return parsed_models + parsed_blockstates + parsed_lang_files
            case FileSelectorType.BLOCK.value:
                pass
            case _:
                logger.error(f"Incorrect file selector type: {self.selector_type}")
                return

    @staticmethod
    def parse(data: dict, pack):
        return FileSelector(data["type"], data["arguments"], pack)
