pyinstaller --onefile --noupx main.py
Copy-Item README.md -Destination dist\README.md
Copy-Item LICENSE -Destination dist\LICENSE
