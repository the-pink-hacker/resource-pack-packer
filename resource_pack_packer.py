from packer import *


RUN_TYPE = input("Run as:\nconfig\ndev\nmanual\n\n").lower()

packer = Packer(RUN_TYPE)

packer.start()
