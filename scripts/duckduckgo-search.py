import os
from ddgs import DDGS
import requests

def duckduckgo_image_search(query):
    with DDGS() as ddgs:
        try:
            results = ddgs.images(query, max_results=1)
            for result in results:
                return result["image"]
        except Exception as e:
            print(f"No image found for query '{query}': {e}")
    return None

def download_image(url, path):
    try:
        res = requests.get(url, stream=True)
        if res.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in res.iter_content(1024):
                    f.write(chunk)
    except Exception as e:
        print(f"Failed to download {url}: {e}")

people = [
    ("Kyrre Glette", "UiO"),
    ("Morten Qvenild", "NMH"),
    ("Georgios Marentakis", "HiØ"),
    ("Budhaditya Chattopadhyay", "UiB"),
    ("Sashi Komandur", "INN"),
    ("Synne Tollerud Bull", "Kristiania"),
    ("Claire Ghetti", "UiB"),
    ("Andreas Bergsland", "NTNU"),
    ("Jonna Vuoskoski", "UiO"),
    ("Hilde Norbakken", "UiA"),
    ("Sidsel Karlsen", "NMH"),
    ("Fredrik Graver", "INN"),
    ("Ragnhild Brøvig", "UiO"),
    ("Irina Eidsvold-Tøien", "BI"),
    ("Jon Marius Aareskjold-Drecker", "UiT"),
    ("Ingrid Romarheim Haugen", "NB"),
    ("Arnulf Mattes", "UiB"),
    ("Olivier Lartillot", "UiO"),
    ("Carsten Griwodz", "UiO"),
    ("Baltasar Beferull‐Lozano", "SimulaMet"),
    ("Kjetil Nordby", "AHO"),
]

institutions = [
    "UiO", "NMH", "HiØ", "UiB", "INN", "Kristiania", "NTNU", "UiA", "BI", "UiT", "NB", "SimulaMet", "AHO"
]

os.makedirs("assets/images/portraits", exist_ok=True)
os.makedirs("assets/images/logos", exist_ok=True)

# Download portraits
for name, inst in people:
    query = f"{name} {inst} portrait"
    img_url = duckduckgo_image_search(query)
    if img_url:
        filename = f"assets/images/portraits/{name.replace(' ', '_')}_{inst}.jpg"
        download_image(img_url, filename)
        print(f"Downloaded portrait for {name} ({inst})")
    else:
        print(f"No image found for {name} ({inst})")

# Download logos
for inst in institutions:
    query = f"{inst} logo"
    img_url = duckduckgo_image_search(query)
    if img_url:
        filename = f"assets/images/logos/{inst}_logo.jpg"
        download_image(img_url, filename)
        print(f"Downloaded logo for {inst}")
    else:
        print(f"No logo found for {inst}")

print("Download complete.")
