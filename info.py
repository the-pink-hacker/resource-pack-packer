RESOURCE_PACK_FOLDER_DIR = None
TEMP_DIR = None
OUT_DIR = None
PATCH_DIR = None


def set_info(resource_pack_folder_dir, temp_dir, out_dir, patch_dir):
    global RESOURCE_PACK_FOLDER_DIR, TEMP_DIR, OUT_DIR, PATCH_DIR

    RESOURCE_PACK_FOLDER_DIR = resource_pack_folder_dir
    TEMP_DIR = temp_dir
    OUT_DIR = out_dir
    PATCH_DIR = patch_dir
