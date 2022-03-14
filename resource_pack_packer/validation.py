import json
import logging
import os
from glob import glob
from multiprocessing import Pool

import jsonschema

from resource_pack_packer.console import add_to_logger_name


def validate(pack: str, logger_name: str):
    logger = add_to_logger_name(logger_name, "validation")

    assets_dir = os.path.join(pack, "assets", "*")

    logger.info("Validating blockstates...")
    validate_assets(os.path.join(assets_dir, "blockstates", "**"), "json",
                    "minecraft/assets/blockstates/blockstate.schema.json", logger)
    logger.info("Validated blockstates.")

    logger.info("Validating models...")
    validate_assets(os.path.join(assets_dir, "models", "**"), "json", "minecraft/assets/models/model.schema.json",
                    logger)
    logger.info("Validated models.")

    validate_asset(os.path.join(assets_dir, "sounds.json"), get_schema("minecraft/assets/models/model.schema.json"),
                   logger)


def get_schema(schema: str) -> dict:
    with open(os.path.join("schema", schema), "r") as raw_schema:
        parsed_schema = json.load(raw_schema)
    return parsed_schema


def validate_asset(file: str, schema: dict, logger: logging.Logger) -> bool:
    if os.path.exists(file):
        with open(file, "r") as raw_data:
            data = json.load(raw_data)

        try:
            jsonschema.validate(data, schema)
            return True
        except jsonschema.ValidationError as e:
            logger.warning(f"{file} didn't match schema:\n{e.message}")
            return False
    return True


def validate_assets(folder: str, extension: str, schema: str, logger: logging.Logger):
    files = glob(folder, recursive=True)
    parsed_schema = get_schema(schema)
    filtered_files = []

    for file in files:
        if os.path.isfile(file) and file.endswith(f".{extension}"):
            filtered_files.append([file, parsed_schema, logger])

    with Pool(processes=os.cpu_count()) as p:
        p.map(_validate_assets, filtered_files)


def _validate_assets(arg: list):
    validate_asset(arg[0], arg[1], arg[2])
