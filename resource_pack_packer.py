from packer import *


RUN_TYPE = input("Run as:\nconfig\ndev\nmanual\npublish\n\n").lower()

packer = Packer(RUN_TYPE)

packer.start()
