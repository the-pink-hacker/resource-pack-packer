import logging
import os

from resource_pack_packer import dependencies
from resource_pack_packer.console import choose_from_list
from resource_pack_packer.packer import Packer
from resource_pack_packer.settings import MAIN_SETTINGS, folder_dialog


def main():
    logging.basicConfig(
        format="[\x1b[32m%(asctime)s\x1b[0m] | [\x1b[34m%(name)s\x1b[0m] [\x1b[33m%(levelname)s\x1b[0m] | \x1b[36m%(message)s\x1b[0m",
        datefmt="%H:%M:%S",
        level=logging.INFO
    )

    logger = logging.getLogger("Main")

    logger.info(f"Working Dir: {MAIN_SETTINGS.working_directory}")

    run_type = choose_from_list(["run", "workdir", "setup"])[0]
    if run_type == "run":
        packer = Packer()
        packer.start()
    elif run_type == "workdir":
        MAIN_SETTINGS.working_directory = folder_dialog("Select Working Directory: ", os.path.abspath(os.path.join(MAIN_SETTINGS.working_directory, os.pardir)))
        MAIN_SETTINGS.save()
        main()
    elif run_type == "setup":
        dependencies.setup()


if __name__ == "__main__":
    main()
