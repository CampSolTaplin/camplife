"""Sample actual route colors from each Recorrido image."""
import numpy as np
from PIL import Image
from pathlib import Path

CARPOOLS = Path(__file__).resolve().parent.parent / "Carpools"

def sample(path, points_dict):
    img = np.array(Image.open(path).convert("RGB"))
    print(f"\n{path.name}  ({img.shape[1]}x{img.shape[0]})")
    for label, (x, y) in points_dict.items():
        if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
            c = img[y, x]
            print(f"  {label:12} at ({x},{y}): RGB({c[0]}, {c[1]}, {c[2]})  hex #{c[0]:02X}{c[1]:02X}{c[2]:02X}")

# Try sampling at approximate locations of route features (based on my earlier visual estimates)
# Scheck (1192x850): blue route top runs at y~100, blue right at x~1000, orange at y~430
print("=" * 60)
sample(CARPOOLS / "Scheck Family Plaza Recorrido.png", {
    "blue top":   (700, 100),
    "blue right": (1000, 200),
    "blue bot":   (700, 400),
    "orange":     (700, 450),
    "yellow drop":(390, 360),
    "teal gate":  (1070, 400),
})

# Hillel (1021x805): red route bottom, orange to top-left
sample(CARPOOLS / "Hillel Carpool Recorrido.png", {
    "red bottom": (500, 700),
    "red side":   (900, 600),
    "orange":     (300, 300),
    "yellow drop":(600, 700),
    "teal gate":  (180, 170),
})

# Savage (1192x850)
sample(CARPOOLS / "Savage Playground Recorrido.png", {
    "green path": (500, 300),
    "green path2":(400, 500),
    "orange":     (700, 450),
    "yellow drop":(280, 720),
    "teal gate":  (1070, 400),
})

# ECA (1192x850)
sample(CARPOOLS / "ECA CARPOOL Recorrido.png", {
    "pink path":  (250, 500),
    "pink path2":(350, 300),
    "orange":     (700, 450),
    "yellow drop":(390, 360),
    "teal gate":  (1070, 400),
})
