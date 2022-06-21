import json
import logging
import os
from enum import Enum
from functools import singledispatch
from glob import glob
from multiprocessing import Pool
from typing import overload, Optional

import jsonschema

from resource_pack_packer.console import add_to_logger_name


class AssetType(Enum):
    BLOCKSTATE = "blockstate"
    MODEL = "model"
    SOUND_INDEX = "sound_index"

    @staticmethod
    def get_path(asset_type: "AssetType") -> str:
        """
        Gets the relative path of the asset from the asset folder.

        :param asset_type: The type of asset
        :return: The relative path of the asset
        """

        match asset_type:
            case AssetType.BLOCKSTATE:
                return os.path.join("blockstates", "**")
            case AssetType.MODEL:
                return os.path.join("models", "**")
            case AssetType.SOUND_INDEX:
                return "sounds.json"

    @staticmethod
    def get_schema_path(asset_type: "AssetType") -> str:
        """
        Get the path of the schema.

        :param asset_type: The type of asset
        :return: The path of the schema
        """

        match asset_type:
            case AssetType.BLOCKSTATE:
                return os.path.join("minecraft", "assets", "blockstates", "blockstate.schema.json")
            case AssetType.MODEL:
                return os.path.join("minecraft", "assets", "models", "model.schema.json")
            case AssetType.SOUND_INDEX:
                return os.path.join("minecraft", "assets", "sounds.schema.json")


def validate(pack: str, logger_name: str):
    logger = add_to_logger_name(logger_name, "validation")

    assets_dir = os.path.join(pack, "assets", "*")

    # Blockstates
    logger.info("Validating blockstates...")
    validate_assets(assets_dir, AssetType.BLOCKSTATE, "json", logger)
    logger.info("Validated blockstates.")

    # Models
    logger.info("Validating models...")
    validate_assets(assets_dir, AssetType.MODEL, "json", logger)
    logger.info("Validated models.")

    # Sound index
    validate_asset(os.path.join(assets_dir, AssetType.get_path(AssetType.SOUND_INDEX)), AssetType.SOUND_INDEX, logger)


def get_schema(asset_type: AssetType) -> dict:
    with open(os.path.join("schema", AssetType.get_schema_path(asset_type)), "r") as raw_schema:
        parsed_schema = json.load(raw_schema)
    return parsed_schema


@singledispatch
def validate_asset(assets_dir: str, asset_type: AssetType, logger: logging.Logger, schema: Optional[dict] = None) -> bool:
    if schema is None:
        schema = get_schema(asset_type)

    file = os.path.join(assets_dir)

    if os.path.exists(file):
        with open(file, "r") as raw_data:
            data = json.load(raw_data)

        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            logger.warning(f"{file} didn't match schema:\n{e.message}")
            return False

        # Asset specific checks
        match asset_type:
            case AssetType.MODEL:
                # Elements
                if "elements" in data:
                    for element in data["elements"]:
                        # Faces
                        if "faces" in element:
                            for face in element["faces"].values():
                                # Texture
                                if "texture" in face and face["texture"] == "#missing":
                                    logger.warning(f"Missing texture in: {file}")

    return True


def validate_assets(asset_dir: str, asset_type: AssetType, extension: str, logger: logging.Logger):
    files = glob(os.path.join(asset_dir, AssetType.get_path(asset_type)), recursive=True)
    parsed_schema = get_schema(asset_type)
    filtered_files = []

    for file in files:
        if os.path.isfile(file) and file.endswith(f".{extension}"):
            filtered_files.append([file, asset_type, logger, parsed_schema])

    with Pool(processes=os.cpu_count()) as p:
        p.map(_validate_assets, filtered_files)


def _validate_assets(arg: list):
    validate_asset(arg[0], arg[1], arg[2], arg[3])
