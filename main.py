import argparse
import logging
import os

from resource_pack_packer import dependencies
from resource_pack_packer.console import choose_from_list, parse_dir
from resource_pack_packer.packer import Packer
from resource_pack_packer.settings import MAIN_SETTINGS, folder_dialog


def main():
    # Create argparse info
    parser = argparse.ArgumentParser(description="RPP is a build tool for Minecraft resourcepacks")
    parser.add_argument("-b", "--build", action="store_true", help="Build a resourcepack in the current work directory")
    parser.add_argument("-s", "--setup", action="store_true", help="Setup a resourcepack in the current work directory")
    parser.add_argument("-p", "--pack", type=str, nargs=1, default=None, metavar="pack_name",
                        help="The name of a json file in \"/configs/\"")
    parser.add_argument("-r", "--runoption", type=str, nargs=1, default=None, metavar="run_option",
                        help="A list of run option names")
    parser.add_argument("-c", "--config", type=str, nargs="+", default=None, metavar="config",
                        help="A list of config names. \"*\" can also be used to represent every config")
    parser.add_argument("-w", "--workdir", type=str, nargs=1, default=None, metavar="work_directory",
                        help="A path to the current work directory")
    parser.add_argument("--close", action="store_true", help="Should the terminal close after running")
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        format="[\x1b[32m%(asctime)s\x1b[0m] [\x1b[34m%(name)s\x1b[0m] "
               "[\x1b[33m%(levelname)s\x1b[0m] \x1b[36m%(message)s\x1b[0m",
        datefmt="%H:%M:%S",
        level=logging.INFO
    )

    logger = logging.getLogger("MAIN")

    # Command line
    if args.workdir is not None:
        MAIN_SETTINGS.working_directory = parse_dir(args.workdir[0])
        MAIN_SETTINGS.save()
        return
    elif args.build or args.setup:
        pack = None
        run_option = None
        config = None

        if args.pack is not None:
            pack = args.pack[0]
        if args.runoption:
            run_option = args.runoption[0]
        if args.config is not None:
            config = args.config

        if args.build:
            Packer().start(pack, run_option, config, args.close)
        if args.setup:
            dependencies.setup(pack, config)
        
        if args.close:
            return

    logger.info(f"Working Dir: {MAIN_SETTINGS.working_directory}")

    run_type = choose_from_list(["build", "workdir", "setup", "close"])[0]
    if run_type == "build":
        Packer().start()
    elif run_type == "workdir":
        MAIN_SETTINGS.working_directory = folder_dialog("Select Working Directory: ", os.path.abspath(
            os.path.join(MAIN_SETTINGS.working_directory, os.pardir)))
        MAIN_SETTINGS.save()
        main()
    elif run_type == "setup":
        dependencies.setup()
    elif run_type == "close":
        return
    main()


if __name__ == "__main__":
    main()
