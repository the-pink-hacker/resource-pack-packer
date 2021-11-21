import json
from os import path

import requests
from markdown import markdown

from resource_pack_packer.settings import MAIN_SETTINGS

URL_CURSEFORGE = "https://minecraft.curseforge.com"
URL_VERSIONS = f"{URL_CURSEFORGE}/api/game/versions"

RELEASE_TYPE_ALPHA = "alpha"
RELEASE_TYPE_BETA = "beta"
RELEASE_TYPE_RELEASE = "release"

CHANGELOG_TYPE_HTML = "html"
CHANGELOG_TYPE_MARKDOWN = "markdown"
CHANGELOG_TYPE_MARKDOWN_HTML = "markdown-html"


VERSIONS = []


def get_versions():
    versions = requests.get(URL_VERSIONS, params={"token": MAIN_SETTINGS.curseforge})

    if versions.ok:
        return versions.json()
    else:
        print(f"Could not get versions list: {versions}")
        return None


def get_game_version(version, versions):
    version_split = version.split(".")[0:2]

    # This is the ONLY way to get the game version. CurseForge Fix your API!
    # This won't work with older versions that lack a snapshot version (1.7.x and lower). Might fix
    snapshot_version = f"{version_split[0]}.{version_split[1]}-Snapshot"

    for ver in versions:
        if ver["name"] == snapshot_version:
            return ver["gameVersionTypeID"]

    print("Could not find game version")
    return None


def get_version_id(name, versions):
    game_version = get_game_version(name, versions)

    print(game_version)

    for version in versions:
        if version["name"] == name:
            if version["gameVersionTypeID"] == game_version:
                return version["id"]
    print(f"Version not found: {name}")
    return None


def versions_to_ids(names, versions):
    ids = []

    for name in names:
        version = get_version_id(name, versions)

        if version is not None:
            ids.append(version)

    return ids


def get_changelog(temp_pack_dir, changelog_type):
    if changelog_type == CHANGELOG_TYPE_HTML:
        changelog_dir = path.join(temp_pack_dir, "changelog.html")
    elif changelog_type == CHANGELOG_TYPE_MARKDOWN:
        changelog_dir = path.join(temp_pack_dir, "changelog.md")
    elif changelog_type == CHANGELOG_TYPE_MARKDOWN_HTML:
        changelog_dir = path.join(temp_pack_dir, "changelog.md")
    else:
        return ""

    if path.exists(changelog_dir):
        with open(changelog_dir, "r") as changelog:
            changelog_content = changelog.read()

            # Converts to html if set to markdown-html
            if changelog_type == CHANGELOG_TYPE_MARKDOWN_HTML:
                changelog_content = markdown(changelog_content)

            return changelog_content
    else:
        print(f"Changelog not found: {changelog_dir}")
        return None


def parse_release_type(release_type):
    if release_type.lower() == RELEASE_TYPE_RELEASE:
        return RELEASE_TYPE_RELEASE
    elif release_type.lower() == RELEASE_TYPE_BETA:
        return RELEASE_TYPE_BETA
    elif release_type.lower() == RELEASE_TYPE_ALPHA:
        return RELEASE_TYPE_ALPHA
    else:
        print(f"Incorrect release type: {release_type}, defaulting to: {RELEASE_TYPE_RELEASE}")
        return RELEASE_TYPE_RELEASE


def parse_changelog_type(changelog_type):
    if changelog_type == CHANGELOG_TYPE_HTML:
        return CHANGELOG_TYPE_HTML
    elif changelog_type == CHANGELOG_TYPE_MARKDOWN:
        return CHANGELOG_TYPE_MARKDOWN
    elif changelog_type == CHANGELOG_TYPE_MARKDOWN_HTML:
        return CHANGELOG_TYPE_HTML
    else:
        print(f"Incorrect changelog type: {changelog_type}, defaulting to: {CHANGELOG_TYPE_MARKDOWN}")
        return CHANGELOG_TYPE_MARKDOWN


def init():
    global VERSIONS
    # All of the versions of minecraft on curseforge
    VERSIONS = get_versions()


class UploadFileRequest:
    def __init__(self, pack_info, config, output_dir, temp_pack_dir, pack_name, release_type):
        self.pack_info = pack_info
        self.config = config
        self.output_dir = output_dir
        print(get_changelog(temp_pack_dir, CHANGELOG_TYPE_MARKDOWN_HTML))
        self.metadata = {
            "changelog": get_changelog(temp_pack_dir, self.pack_info.curseforge_changelog_type),
            "changelogType": parse_changelog_type(self.pack_info.curseforge_changelog_type),
            "displayName": pack_name,
            "gameVersions": versions_to_ids(config.mc_versions, VERSIONS),
            "releaseType": parse_release_type(release_type),
        }

    def upload(self):
        with open(self.output_dir, "rb") as file:
            upload = requests.post(f"{URL_CURSEFORGE}/api/projects/{self.pack_info.curseforge_id}/upload-file",
                                   params={"token": MAIN_SETTINGS.curseforge},
                                   data={"metadata": json.dumps(self.metadata, ensure_ascii=False)},
                                   files={"file": file})

            print(upload.json())
