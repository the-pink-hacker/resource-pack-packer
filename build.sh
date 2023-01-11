name="rpp"

pyinstaller --noconfirm --onedir --console --name $name --add-data "resource_pack_packer:resource_pack_packer/" --paths "./"  "main.py"

# Make schema folders
mkdir -p "dist/$name/schema"

# Move schemas into folder
# There might be a way to do this with pyinstaller, but I can't figure it out
cp -r "schema"* "dist/$name/schema"
