from resource_pack_packer.packer import Packer
from resource_pack_packer.settings import MAIN_SETTINGS


def main():
    print(f"Working Dir: {MAIN_SETTINGS.working_directory}")

    run_type = input("config\ndev\nmanual\npublish\nworkdir\n\n").lower()
    if run_type == "workdir":
        working_directory = input("Working Directory: ")
        MAIN_SETTINGS.working_directory = working_directory
        MAIN_SETTINGS.save()
        main()
    else:
        packer = Packer(run_type)
        packer.start()


if __name__ == "__main__":
    main()
