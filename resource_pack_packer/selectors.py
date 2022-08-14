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
    UNION = "union"


class FileSelector:
    """
    Select a collection of files from a patch file.
    """

    def __init__(self, selector_type: str, arguments: dict, pack: str):
        self.selector_type = selector_type
        self.arguments = arguments
        self.pack = pack

    def run(self, pack_info, logger: logging.Logger) -> Optional[List[str]]:
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

                parsed_models = list(map(lambda m: os.path.join(self.pack, parse_minecraft_identifier(m, "models", "json")), models))
                parsed_blockstates = list(map(lambda b: os.path.join(self.pack, parse_minecraft_identifier(b, "blockstates", "json")), blockstates))
                parsed_lang_files = list(map(lambda l: os.path.join(self.pack, parse_minecraft_identifier(l, "lang", "json")), lang_files))

                return parsed_models + parsed_blockstates + parsed_lang_files
            case FileSelectorType.BLOCK.value:
                blocks = self.arguments["blocks"]

                files = []

                for block in blocks:
                    if "plural" in block:
                        plural = block["plural"]
                    else:
                        plural = False

                    block_plural = block["block"]

                    if plural:
                        block_single = block["block"][:-1]
                    else:
                        block_single = block["block"]

                    parsed_block_files = []

                    if pack_info.block_files is not None:
                        for block_file in pack_info.block_files:
                            parsed_block_file = block_file.replace("[block_name]", block_single)
                            parsed_block_file = parsed_block_file.replace("[block_name_plural]", block_plural)
                            if os.path.exists(os.path.join(self.pack, parsed_block_file)):
                                parsed_block_files.append(os.path.join(self.pack, parsed_block_file))
                    else:
                        logger.error("block_files is not set")
                        return

                    files += parsed_block_files
                return files
            case FileSelectorType.UNION.value:
                # Prevents multiple of the same file being selected
                files: set = set()

                if "selectors" in self.arguments:
                    for selectors in self.arguments["selectors"]:
                        selector_output = FileSelector.parse(selectors, self.pack).run(pack_info, logger)
                        if selector_output is not None:
                            files |= set(selector_output)

                print(files)
                return list(files)
            case _:
                logger.error(f"Incorrect file selector type: {self.selector_type}")
                return

    @staticmethod
    def parse(data: dict, pack: str):
        return FileSelector(data["type"], data["arguments"], pack)


class Direction(Enum):
    NORTH = "north"
    EAST = "east"
    SOUTH = "south"
    WEST = "west"
    UP = "up"
    DOWN = "down"
    CENTER = "center"
    NONE = "none"

    @staticmethod
    def flip(direction: str) -> "Direction":
        match direction:
            case Direction.NORTH.value:
                return Direction.SOUTH.value
            case Direction.EAST.value:
                return Direction.WEST.value
            case Direction.SOUTH.value:
                return Direction.NORTH.value
            case Direction.WEST.value:
                return Direction.EAST.value
            case Direction.UP.value:
                return Direction.DOWN.value
            case Direction.DOWN.value:
                return Direction.UP.value
            case Direction.CENTER.value:
                return Direction.CENTER.value
            case _:
                return Direction.NONE.value
