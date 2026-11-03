"""
Dataset Download and Verification Script for Alzheimer's MRI Preprocessed Dataset.
Dataset source: https://www.kaggle.com/datasets/rajmohan096/alzheimer-mri-preprocessed-dataset
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DATASET_SLUG = "rajmohan096/alzheimer-mri-preprocessed-dataset"

# Expected classes
TARGET_CLASSES = [
    "Non-Demented",
    "Very Mild Demented",
    "Mild Demented",
    "Moderate Demented"
]


def check_local_dataset():
    """Check if dataset already exists in data/raw or find subdirectories."""
    if not RAW_DATA_DIR.exists():
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Check for class directories inside data/raw first
    class_dirs = [d for d in RAW_DATA_DIR.rglob("*") if d.is_dir() and any(c.lower().replace("-", "").replace(" ", "").replace("_", "") in d.name.lower().replace("-", "").replace(" ", "").replace("_", "") for c in TARGET_CLASSES)]
    if len(class_dirs) >= 4:
        return True

    # Check for zip files in data/raw
    zip_files = list(RAW_DATA_DIR.glob("*.zip"))
    if zip_files:
        print(f"[INFO] Found zip file: {zip_files[0]}. Extracting...")
        with zipfile.ZipFile(zip_files[0], 'r') as zip_ref:
            zip_ref.extractall(RAW_DATA_DIR)
        print("[OK] Extraction complete.")

    class_dirs = [d for d in RAW_DATA_DIR.rglob("*") if d.is_dir() and any(c.lower().replace("-", "").replace(" ", "").replace("_", "") in d.name.lower().replace("-", "").replace(" ", "").replace("_", "") for c in TARGET_CLASSES)]
    return len(class_dirs) >= 4


def inspect_dataset():
    """Inspect and display counts for each category in raw dataset."""
    print("=" * 60)
    print("INSPECTING ALZHEIMER'S MRI DATASET")
    print("=" * 60)

    # Search for matching directories
    found_dirs = {}
    for d in RAW_DATA_DIR.rglob("*"):
        if d.is_dir():
            clean_name = d.name.lower().replace("-", "").replace(" ", "").replace("_", "")
            for target in TARGET_CLASSES:
                target_clean = target.lower().replace("-", "").replace(" ", "").replace("_", "")
                if clean_name == target_clean:
                    found_dirs[target] = d

    if len(found_dirs) < 4:
        print(f"[WARN] Found {len(found_dirs)} / 4 classes in {RAW_DATA_DIR}:")
        for k, v in found_dirs.items():
            print(f"  - {k}: {v}")
        return False, found_dirs

    total_images = 0
    print("\nDataset Class Distribution:")
    print("-" * 50)
    for target in TARGET_CLASSES:
        dir_path = found_dirs[target]
        valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
        images = [f for f in dir_path.glob("*") if f.suffix.lower() in valid_exts]
        count = len(images)
        total_images += count
        print(f"  [+] {target:<22}: {count:>5} images (Path: {dir_path.name})")

    print("-" * 50)
    print(f"  Total Images Verified: {total_images}")
    print("=" * 60)
    return True, found_dirs


def download_with_kaggle_api():
    """Attempt download using kaggle API."""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        print(f"[INFO] Kaggle API authenticated successfully.")
        print(f"[INFO] Downloading dataset: {DATASET_SLUG} to {RAW_DATA_DIR}...")
        api.dataset_download_files(DATASET_SLUG, path=str(RAW_DATA_DIR), unzip=True)
        print("[OK] Dataset downloaded and unzipped successfully.")
        return True
    except Exception as e:
        print(f"[ERROR] Kaggle download failed: {e}")
        return False


if __name__ == "__main__":
    if check_local_dataset():
        valid, dirs = inspect_dataset()
        if valid:
            sys.exit(0)

    print("\n[INFO] Dataset not found in data/raw. Attempting Kaggle API download...")
    if download_with_kaggle_api():
        inspect_dataset()
    else:
        print("\n" + "=" * 60)
        print("KAGGLE AUTHENTICATION REQUIRED")
        print("=" * 60)
        print("To download the dataset automatically:")
        print("1. Go to https://www.kaggle.com/settings -> 'Create New Token'")
        print("2. A file named 'kaggle.json' will download.")
        print("3. Either:")
        print("   - Place 'kaggle.json' in: C:\\Users\\Manasa papasani\\.kaggle\\kaggle.json")
        print("   - OR provide your Kaggle Username and API Key.")
        print("   - OR download the zip directly from:")
        print("     https://www.kaggle.com/datasets/rajmohan096/alzheimer-mri-preprocessed-dataset")
        print("     and place the zip file in: C:\\PROJECT\\Alzheimers_Disease_Classification\\data\\raw\\")
        print("=" * 60)
        sys.exit(1)
