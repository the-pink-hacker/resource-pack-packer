import json
import logging
import os
from glob import glob

import jsonschema


def validate(pack: str):
    assets_dir = os.path.join(pack, "assets", "*")
    validate_assets(os.path.join(assets_dir, "blockstates", "**"), "json", "minecraft/assets/blockstates/blockstate.schema.json")
    validate_assets(os.path.join(assets_dir, "models", "**"), "json", "minecraft/assets/models/model.schema.json")


def validate_assets(folder: str, extension: str, schema):
    files = glob(folder, recursive=True)
    for file in files:
        if os.path.isfile(file):
            if file.endswith(f".{extension}"):
                with open(file, "r") as raw_data:
                    data = json.load(raw_data)
                with open(os.path.join("schema", schema), "r") as raw_schema:
                    parsed_schema = json.load(raw_schema)

                try:
                    jsonschema.validate(data, parsed_schema)
                except jsonschema.ValidationError as e:
                    logging.warning(f"{file} didn't match schema:\n{e}")
