import os
import difflib

names = [
    "Kyrre Glette",
    "Morten Qvenild",
    "Georgios Marentakis",
    "Budhaditya Chattopadhyay",
    "Sashi Komandur",
    "Synne Tollerud Bull",
    "Claire Ghetti",
    "Andreas Bergsland",
    "Jonna Vuoskoski",
    "Hilde Norbakken",
    "Sidsel Karlsen",
    "Fredrik Graver",
    "Ragnhild Brøvig",
    "Irina Eidsvold-Tøien",
    "Jon Marius Aareskjold-Drecker",
    "Ingrid Romarheim Haugen",
    "Arnulf Mattes",
    "Olivier Lartillot",
    "Carsten Griwodz",
    "Baltasar Beferull‐Lozano",
    "Kjetil Nordby"
]

assets_folder = "../assets/images/portraits"
extensions = [".jpg", ".jpeg", ".png"]

missing = []
files = os.listdir(assets_folder)
for name in names:
    found = False
    # Generate possible filename patterns
    patterns = [name.replace(" ", "_").replace("‐", "-") + ext for ext in extensions]
    # Fuzzy match against all files in the folder
    for pattern in patterns:
        matches = difflib.get_close_matches(pattern, files, n=1, cutoff=0.8)
        if matches:
            found = True
            break
    if not found:
        missing.append(name)

print("Missing images for:")
for name in missing:
    print(name)
