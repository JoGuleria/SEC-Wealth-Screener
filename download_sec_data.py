import requests
from pathlib import Path

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Start with one quarter. Add more later.
FILES = {
    "2026q1": "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/2026q1_form345.zip"
}

HEADERS = {
    "User-Agent": "Your Name your.email@example.com",
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov"
}

for quarter, url in FILES.items():
    output_path = RAW_DIR / f"{quarter}_form345.zip"

    if output_path.exists():
        print(f"Already downloaded: {output_path}")
        continue

    print(f"Downloading {quarter}...")
    response = requests.get(url, headers=HEADERS, timeout=60)
    response.raise_for_status()

    output_path.write_bytes(response.content)
    print(f"Saved to {output_path}")