from packer import *


# Loads settings.json
settings = Settings().data

RESOURCE_PACK_FOLDER_DIR = path.join(parse_dir(settings["locations"]["pack_folder"]), "*")
TEMP_DIR = parse_dir(settings["locations"]["temp"])
OUT_DIR = parse_dir(settings["locations"]["out"])

# Gets all packs
PACKS = glob(RESOURCE_PACK_FOLDER_DIR, recursive=False)

RUN_TYPE = input("Run as manual or config: ").lower()

packer = Packer(RUN_TYPE, TEMP_DIR, RESOURCE_PACK_FOLDER_DIR, OUT_DIR, PACKS)

packer.start()
