import shutil, sys, json, os
from os import path
from glob import glob

def LoadSettings():
	if not path.exists("settings.json"):
		with open("settings.json", "x") as file:	
			data = {
	"locations": {
		"pack_folder": path.normpath(path.join(path.abspath(path.expanduser(input("Minecraft Folder: "))), "resourcepacks")),
		"temp": "temp",
		"out": path.normpath(path.abspath(path.expanduser(input("Output Folder: "))))
		}
}
			json.dump(data, file, indent="\t")

	with open("settings.json", "r") as file:
		return json.load(file)

def FilterPacks(packs, selected):
	for pack in packs:
		# Checks for match
		if selected in pack:
			return pack
		# Checks for close match
		if selected.lower() in pack.lower():
			return pack
	return None

def ClearTemp():
	if path.exists(TempDir):
		print("Clearing Temp...")
		shutil.rmtree(TempDir)

def Delete(dir, folder, ignore=None):
	namespaces = glob(path.join(dir, "assets", "*"))

	for namespace in namespaces:
		if path.exists(path.join(namespace, folder)):
			folders = glob(path.join(namespace, folder, "*"))

			for fold in folders:
				if path.basename(fold) != ignore.lower():
					shutil.rmtree(fold)
			print(f"Deleted {path.basename(namespace)}'s Textures")

def AutoPackCheck(version, index, defaultValue=0):
	try:
		return int(version.split(".")[index])
	except:
		return 0

def AutoPack(version):
	version = str(version)
	if AutoPackCheck(version, 1) >= 17:
		return AutoPackCheck(version, 1) - 10
	elif AutoPackCheck(version, 1) == 16:
		return 6
	elif AutoPackCheck(version, 1) >= 15:
		return 5
	elif AutoPackCheck(version, 1) >= 13:
		return 4
	elif AutoPackCheck(version, 1) >= 11:
		return 3
	elif AutoPackCheck(version, 1) >= 9:
		return 2
	elif AutoPackCheck(version, 1) >= 7:
		return 1
	elif AutoPackCheck(version, 1) >= 6:
		if AutoPackCheck(version, 2) == 1:
			return 1
	return 0

def RegenerateMeta(dir, version):
	packFormat = AutoPack(version)
	print(f"Pack Format: {packFormat}")
	
	with open(path.join(dir, "pack.mcmeta"), "r") as file:
		data = json.load(file)

	with open(path.join(dir, "pack.mcmeta"), "w", newline="\n") as file:
		if data["pack"]["pack_format"] != packFormat:
			data["pack"]["pack_format"] = packFormat

			json.dump(data, file, ensure_ascii=False, indent=2)

def PatchPack(pack, patch):
	patchFiles = glob(path.join(patch, "**"), recursive=True)

	for file in patchFiles:
		# Removes all files in pack that are in the patch
		packFile = file.replace(patch, pack)

		if path.isfile(packFile) and path.exists(packFile):
			os.remove(packFile)

		# Applies patch
		if path.isfile(file):
			shutil.copy(file, packFile)

# Loads settings.json
Settings = LoadSettings()

ResourcePackFolderDir = path.normpath(path.join(path.abspath(path.expanduser(Settings["locations"]["pack_folder"])), "*"))
TempDir = path.normpath(path.abspath(path.expanduser(Settings["locations"]["temp"])))
OutDir = path.normpath(path.abspath(path.expanduser(Settings["locations"]["out"])))

# Gets all packs
Packs = glob(ResourcePackFolderDir, recursive=False)

SelectedPack = input("Pack Name: ")

SelectedPack = FilterPacks(Packs, SelectedPack)

print(f"Selected Pack: {SelectedPack}")

if input("Is this correct? y/n\n").lower() == "n":
	sys.exit()

Version = input("Version: ")

MCVersion = input("MC Version: ")

PackName = f"{path.basename(SelectedPack)} v{Version} - {MCVersion}"
FullPackName = path.join(TempDir, PackName)

ClearTemp()

print("Copying...")

# Copys the pack
shutil.copytree(SelectedPack, FullPackName)

if input("Delete Texture Files? y/n\n").lower() == "y":
	Ignore = input("Ignore: ")

	print("Deleting Files...")

	Delete(FullPackName, "textures", Ignore)

if input("Regenerate pack.mcmeta? y/n\n").lower() == "y":
	RegenerateMeta(FullPackName, MCVersion)

if input("Apply patch? y/n\n").lower() == "y":
	Patch = FilterPacks(Packs, input("Patches: "))
	print(f"Selected Patch: {Patch}")
	print("Patching...")

	PatchPack(FullPackName, Patch)

print("Zipping Files...")

# Zip files
shutil.make_archive(FullPackName, "zip", FullPackName)

# Move to out
if path.exists(path.normpath(path.join(OutDir, PackName + ".zip"))):
	if input(f"Pack already exists. Do you want to overwrite {path.normpath(path.join(OutDir, PackName + '.zip'))}. y/n\n").lower() == "y":
		os.remove(path.normpath(path.join(OutDir, PackName + ".zip")))
		shutil.move(path.normpath(FullPackName + ".zip"), OutDir)

		print(f"Completed pack sent to: {OutDir}")
else:
	shutil.move(path.normpath(FullPackName + ".zip"), OutDir)
	print(f"Completed pack sent to: {OutDir}")

ClearTemp()
