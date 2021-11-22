import setuptools

setuptools.setup(
    name="resource_pack_packer",
    version="0.4",
    description="Automates the development and distribution of Minecraft resource packs.",
    author="RyanGar46",
    entry_points={
        "console_scripts": [
            "resource_pack_packer = main:main"
        ]
    },
    packages=setuptools.find_packages(where="")
)
