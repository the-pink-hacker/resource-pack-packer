import json
import os
import shutil
from glob import glob
from os import path

from configs import check_option
from settings import parse_dir_keywords

PATCH_TYPE_REPLACE = "replace"
PATH_TYPE_REMOVE = "remove"


def get_patches(config):
    patches = []

    for patch in config["patches"]:
        patches.append(Patch(patch))

    return patches


class Patch:
    def __init__(self, patch):
        with open(path.join("patches", f"{patch}.json")) as file:
            data = json.load(file)
            self.patch = data["patch"]
            self.type = data["type"]


# Replaces and adds files accordingly
def _patch_replace(pack, patch, resource_pack_dir):
    patch_dir = parse_dir_keywords(patch.patch["directory"], resource_pack_dir)
    patch_files = glob(path.join(patch_dir, "**"), recursive=True)

    for file in patch_files:
        # The location that the file should go to
        pack_file = file.replace(patch_dir, pack)

        # Removes all files in pack that are in the patch.py
        if path.isfile(pack_file) and path.exists(pack_file):
            os.remove(pack_file)

        # Applies patch.py
        if path.isfile(file) and path.exists(file):
            try:
                shutil.copy(file, pack_file)
            except IOError:
                os.makedirs(path.dirname(pack_file))
                shutil.copy(file, pack_file)


def _remove_block(file):
    if path.isfile(file) and path.exists(path.dirname(file)):
        os.remove(file)


# Removes all specified files
def _patch_remove(pack, patch):
    files = patch.patch["files"]
    blocks = patch.patch["blocks"]

    for block in blocks:
        block_name_plural = block["block"]

        # Example: stone_bricks -> stone_brick
        if check_option(block, "plural") and block["plural"]:
            block_name = block_name_plural[:-1]
        else:
            block_name = block_name_plural

        # Models
        # Normal block
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name_plural}.json"))

        # Item
        _remove_block(path.join(pack, "assets/minecraft/models/item", f"{block_name_plural}.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/item", f"{block_name}_stairs.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/item", f"{block_name}_wall.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/item", f"{block_name}_slab.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/item", f"{block_name}_pressure_plate.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/item", f"{block_name}_fence.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/item", f"{block_name}_fence_gate.json"))

        # Stairs
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_inner.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_inner.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_outer.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_inner.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_outer.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_.json"))

        # Classic 3D only
        # Bottom
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_north.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_east.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_south.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_west.json"))
        # Top
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_north.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_east.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_south.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_west.json"))
        # Bottom Inner
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_inner_ne.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_inner_nw.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_inner_se.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_inner_sw.json"))
        # Top Inner
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_inner_ne.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_inner_nw.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_inner_se.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_inner_sw.json"))
        # Bottom Outer
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_outer_ne.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_outer_nw.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_outer_se.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_outer_sw.json"))
        # Top Outer
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_outer_ne.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_outer_nw.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_outer_se.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_stairs_top_outer_sw.json"))

        # Slab
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_slab.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_slab_top.json"))

        # Wall
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_wall_post.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_wall_side.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_wall_side_tall.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_wall_inventory.json"))

        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_pressure_plate.json"))

        # Button
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_button.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_button_pressed.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_button_inventory.json"))

        # Fence
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_fence_post.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_fence_side.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_fence_gate.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_fence_gate_open.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_fence_gate_wall.json"))
        _remove_block(path.join(pack, "assets/minecraft/models/block", f"{block_name}_fence_gate_wall_open.json"))

        # Blockstates
        _remove_block(path.join(pack, "assets/minecraft/blockstates", f"{block_name_plural}.json"))
        _remove_block(path.join(pack, "assets/minecraft/blockstates", f"{block_name}_stairs.json"))
        _remove_block(path.join(pack, "assets/minecraft/blockstates", f"{block_name}_wall.json"))
        _remove_block(path.join(pack, "assets/minecraft/blockstates", f"{block_name}_fence.json"))
        _remove_block(path.join(pack, "assets/minecraft/blockstates", f"{block_name}_fence_gate.json"))
        _remove_block(path.join(pack, "assets/minecraft/blockstates", f"{block_name}_slab.json"))
        _remove_block(path.join(pack, "assets/minecraft/blockstates", f"{block_name}_pressure_plate.json"))
        _remove_block(path.join(pack, "assets/minecraft/blockstates", f"{block_name}_button.json"))

        print(f"Removed Block: {block_name_plural}")

    for file in files:
        file_abs = path.join(pack, file)

        # Removes file
        if path.isfile(file_abs) and path.exists(path.dirname(file_abs)):
            os.remove(file_abs)
            print(f"removed: {file_abs}")

        # Removes folder
        if path.exists(file_abs):
            shutil.rmtree(file_abs)


def patch_pack(pack, patch, resource_pack_dir):
    if patch.type == PATCH_TYPE_REPLACE:
        _patch_replace(pack, patch, resource_pack_dir)
    elif patch.type == PATH_TYPE_REMOVE:
        _patch_remove(pack, patch)
