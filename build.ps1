pyinstaller --onefile --noupx resource_pack_packer.py
Copy-Item README.md -Destination dist\README.md
Copy-Item LICENSE -Destination dist\LICENSE
