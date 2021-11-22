from resource_pack_packer.packer import Packer


def main():
    run_type = input("Run as:\nconfig\ndev\nmanual\npublish\n\n").lower()
    packer = Packer(run_type)
    packer.start()


if __name__ == "__main__":
    main()
