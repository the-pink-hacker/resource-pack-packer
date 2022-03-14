import json
import logging
import os
from glob import glob

import jsonschema

from resource_pack_packer.console import add_to_logger_name


def validate(pack: str, logger_name: str):
    logger = add_to_logger_name(logger_name, "validation")

    assets_dir = os.path.join(pack, "assets", "*")

    logger.info("Validating blockstates...")
    blockstate_errors = validate_assets(os.path.join(assets_dir, "blockstates", "**"), "json", "minecraft/assets/blockstates/blockstate.schema.json", logger)
    logger.info(f"Validated blockstates. Errors: {blockstate_errors}")

    logger.info("Validating models...")
    model_errors = validate_assets(os.path.join(assets_dir, "models", "**"), "json", "minecraft/assets/models/model.schema.json", logger)
    logger.info(f"Validated models. Errors: {model_errors}")

    validate_asset(os.path.join(assets_dir, "sounds.json"), "minecraft/assets/models/model.schema.json", logger)


def validate_asset(file: str, schema: str, logger: logging.Logger) -> bool:
    if os.path.exists(file):
        with open(file, "r") as raw_data:
            data = json.load(raw_data)
        with open(os.path.join("schema", schema), "r") as raw_schema:
            parsed_schema = json.load(raw_schema)

        try:
            jsonschema.validate(data, parsed_schema)
            return True
        except jsonschema.ValidationError as e:
            logger.warning(f"{file} didn't match schema:\n{e.message}")
            return False
    return True


def validate_assets(folder: str, extension: str, schema: str, logger: logging.Logger) -> int:
    files = glob(folder, recursive=True)
    errors = 0
    for file in files:
        if os.path.isfile(file):
            if file.endswith(f".{extension}"):
                if not validate_asset(file, schema, logger):
                    errors += 1
    return errors
