import json
import logging
from enum import Enum
from os import path
from typing import Optional, List

import requests
from markdown import markdown

from resource_pack_packer.configs import Config, PackInfo
from resource_pack_packer.settings import MAIN_SETTINGS

URL_CURSEFORGE = "https://minecraft.curseforge.com"
URL_VERSIONS = f"{URL_CURSEFORGE}/api/game/versions"

VERSIONS = []


def get_versions() -> Optional[List[dict]]:
    versions = requests.get(URL_VERSIONS, params={"token": MAIN_SETTINGS.curseforge})

    if versions.ok:
        return versions.json()
    else:
        logging.warning(f"Could not get versions list: {versions}")
        return None


def get_game_version(version, versions):
    version_split = version.split(".")[0:2]

    # This is the ONLY way to get the game version. CurseForge Fix your API!
    # This won't work with older versions that lack a snapshot version (1.7.x and lower). Might fix
    snapshot_version = f"{version_split[0]}.{version_split[1]}-Snapshot"

    for ver in versions:
        if ver["name"] == snapshot_version:
            return ver["gameVersionTypeID"]

    logging.warning("Could not find game version")
    return None


def get_version_id(name: str, versions: List[dict]) -> Optional[str]:
    game_version = get_game_version(name, versions)

    for version in versions:
        if version["name"] == name:
            if version["gameVersionTypeID"] == game_version:
                return version["id"]
    logging.warning(f"Version not found: {name}")
    return


def versions_to_ids(names: List[str], versions: List[dict]) -> List[str]:
    ids = []

    for name in names:
        version = get_version_id(name, versions)

        if version is not None:
            ids.append(version)

    return ids


class ChangelogType(Enum):
    HTML = "html"
    MARKDOWN = "markdown"
    MARKDOWN_HTML = "markdown-html"


def get_changelog(temp_pack_dir: str, changelog_type: str) -> str:
    match changelog_type:
        case ChangelogType.HTML.value:
            changelog_dir = path.join(temp_pack_dir, "changelog.html")
        case ChangelogType.MARKDOWN.value:
            changelog_dir = path.join(temp_pack_dir, "changelog.md")
        case ChangelogType.MARKDOWN_HTML.value:
            changelog_dir = path.join(temp_pack_dir, "changelog.md")
        case _:
            logging.warning(f"Incorrect changelog type: {changelog_type}. Defaulting to markdown")
            changelog_dir = path.join(temp_pack_dir, "changelog.md")

    if path.exists(changelog_dir):
        with open(changelog_dir, "r") as changelog:
            changelog_content = changelog.read()

            # Converts to html if set to markdown-html
            if changelog_type == ChangelogType.MARKDOWN_HTML.value:
                changelog_content = markdown(changelog_content)

            return changelog_content
    else:
        logging.warning(f"Changelog not found: {changelog_dir}")
        return ""


class ReleaseType(Enum):
    RELEASE = "release"
    BETA = "beta"
    ALPHA = "alpha"


def parse_release_type(release_type: str) -> str:
    match release_type.lower():
        case ReleaseType.RELEASE.value:
            return ReleaseType.RELEASE.value
        case ReleaseType.BETA.value:
            return ReleaseType.BETA.value
        case ReleaseType.ALPHA.value:
            return ReleaseType.ALPHA.value
        case _:
            logging.warning(f"Incorrect release type: {release_type}. Defaulting to: {ReleaseType.RELEASE.value}")
            return ReleaseType.RELEASE.value


def parse_changelog_type(changelog_type: str) -> str:
    match changelog_type:
        case ChangelogType.HTML.value:
            return ChangelogType.HTML.value
        case ChangelogType.MARKDOWN.value:
            return ChangelogType.MARKDOWN.value
        case ChangelogType.MARKDOWN_HTML.value:
            return ChangelogType.MARKDOWN_HTML.value
        case _:
            logging.warning(f"Incorrect changelog type: {changelog_type}. Defaulting to: {ChangelogType.MARKDOWN.value}")
            return ChangelogType.MARKDOWN.value


# Only called when user wants to upload to curseforge
def init():
    global VERSIONS
    # All the versions of minecraft on curseforge
    VERSIONS = get_versions()


class UploadFileRequest:
    def __init__(self, pack_info: PackInfo, config: Config, output_dir: str, temp_pack_dir: str, pack_name: str, release_type: str):
        self.pack_info = pack_info
        self.config = config
        self.output_dir = output_dir
        logging.info(get_changelog(temp_pack_dir, ChangelogType.HTML.value))
        self.metadata = {
            "changelog": get_changelog(temp_pack_dir, self.pack_info.curseforge_changelog_type),
            "changelogType": parse_changelog_type(self.pack_info.curseforge_changelog_type),
            "displayName": pack_name,
            "gameVersions": versions_to_ids(config.mc_versions, VERSIONS),
            "releaseType": parse_release_type(release_type),
        }

    def upload(self):
        with open(self.output_dir, "rb") as file:
            upload = requests.post(
                f"{URL_CURSEFORGE}/api/projects/{self.pack_info.curseforge_id}/upload-file",
                params={"token": MAIN_SETTINGS.curseforge},
                data={"metadata": json.dumps(self.metadata, ensure_ascii=False)},
                files={"file": file}
            )

            logging.info(upload.json())
