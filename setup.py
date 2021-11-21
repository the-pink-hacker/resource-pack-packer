from resource_pack_packer.packer import Packer


RUN_TYPE = input("Run as:\nconfig\ndev\nmanual\npublish\n\n").lower()

packer = Packer(RUN_TYPE)

packer.start()
