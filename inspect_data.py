import zipfile
from pathlib import Path

zip_path = Path("data/raw/2026q1_form345.zip")

with zipfile.ZipFile(zip_path, "r") as z:
    print("Files inside ZIP:")
    for name in z.namelist():
        print("-", name)

