"""Download the Brazilian E-Commerce Public Dataset by Olist from Kaggle.

Dataset page: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce (CC BY-NC-SA 4.0)
1. Create a Kaggle API token (Kaggle > Settings > API > Create New Token) and save it as
   ~/.kaggle/kaggle.json, or set KAGGLE_USERNAME and KAGGLE_KEY environment variables.
2. Run: python scripts/download_data.py

Alternatively, download the dataset zip from the page above and extract the CSVs into data/raw/.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import RAW, TABLES


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    if all((RAW / f).exists() for f in TABLES.values()):
        print("Data already present.")
        return
    subprocess.run([sys.executable, "-m", "kaggle", "datasets", "download",
                    "-d", "olistbr/brazilian-ecommerce", "-p", str(RAW), "--unzip"], check=True)
    missing = [f for f in TABLES.values() if not (RAW / f).exists()]
    if missing:
        sys.exit(f"Missing after download: {missing}")
    print("Downloaded", len(TABLES), "files.")


if __name__ == "__main__":
    main()
