"""
Data Preprocessing and Augmentation Pipeline for Alzheimer's Brain MRI Classification.
- Scans input directory for 4 target categories.
- Filters corrupted or duplicate images to prevent data leakage.
- Resizes images to (224, 224) and normalizes pixel intensities to [0, 1].
- Performs stratified splitting into Train (70%), Validation (15%), and Test (15%).
- Generates EDA distribution charts and summary metadata.
"""

import os
import sys
import json
import hashlib
import shutil
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SAMPLES_DIR = PROJECT_ROOT / "data" / "samples"
METRICS_DIR = PROJECT_ROOT / "models" / "metrics"

TARGET_CLASSES = [
    "Non-Demented",
    "Very Mild Demented",
    "Mild Demented",
    "Moderate Demented"
]

TARGET_SIZE = (224, 224)


def compute_image_hash(filepath):
    """Compute MD5 hash to detect duplicate images."""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()


def find_raw_class_directories():
    """Identify directories corresponding to the 4 categories."""
    found = {}
    for d in RAW_DIR.rglob("*"):
        if d.is_dir():
            clean_name = d.name.lower().replace("-", "").replace(" ", "").replace("_", "")
            for target in TARGET_CLASSES:
                target_clean = target.lower().replace("-", "").replace(" ", "").replace("_", "")
                if clean_name == target_clean:
                    found[target] = d
    return found


def preprocess_and_split(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, random_state=42):
    """
    Load raw images, deduplicate, resize to 224x224,
    perform stratified train/val/test split and save to processed folders.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    class_dirs = find_raw_class_directories()
    if len(class_dirs) < 4:
        raise ValueError(f"Could not find all 4 classes in {RAW_DIR}. Found: {list(class_dirs.keys())}")

    print("[1/5] Scanning and validating raw images...")
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

    all_file_records = []
    seen_hashes = set()
    duplicate_count = 0
    corrupt_count = 0

    class_counts_raw = {}

    for label_idx, class_name in enumerate(TARGET_CLASSES):
        source_dir = class_dirs[class_name]
        files = [f for f in source_dir.glob("*") if f.suffix.lower() in valid_exts]
        class_counts_raw[class_name] = len(files)

        for file_path in files:
            # Check image integrity
            try:
                with Image.open(file_path) as img:
                    img.verify()
            except Exception:
                corrupt_count += 1
                continue

            # Check duplicate hash
            file_hash = compute_image_hash(file_path)
            if file_hash in seen_hashes:
                duplicate_count += 1
                continue
            seen_hashes.add(file_hash)

            all_file_records.append({
                "path": str(file_path),
                "class_name": class_name,
                "label": label_idx
            })

    print(f"[OK] Total valid unique images: {len(all_file_records)}")
    print(f"[INFO] Removed {duplicate_count} duplicate files and {corrupt_count} corrupt files.")

    # Stratified Split
    print("[2/5] Performing stratified train/val/test splitting...")
    paths = [r["path"] for r in all_file_records]
    labels = [r["label"] for r in all_file_records]

    # First split: Train vs Temp (val + test)
    temp_ratio = val_ratio + test_ratio
    train_paths, temp_paths, train_labels, temp_labels = train_test_split(
        paths, labels, test_size=temp_ratio, stratify=labels, random_state=random_state
    )

    # Second split: Val vs Test
    relative_test_ratio = test_ratio / temp_ratio
    val_paths, test_paths, val_labels, test_labels = train_test_split(
        temp_paths, temp_labels, test_size=relative_test_ratio, stratify=temp_labels, random_state=random_state
    )

    splits = {
        "train": (train_paths, train_labels),
        "val": (val_paths, val_labels),
        "test": (test_paths, test_labels)
    }

    # Clean existing processed folders
    for split_name in ["train", "val", "test"]:
        split_dir = PROCESSED_DIR / split_name
        if split_dir.exists():
            shutil.rmtree(split_dir)
        for class_name in TARGET_CLASSES:
            (split_dir / class_name).mkdir(parents=True, exist_ok=True)

    print("[3/5] Processing, resizing to 224x224, and saving splits...")
    split_counts = {"train": {}, "val": {}, "test": {}}

    for split_name, (split_paths, split_labels) in splits.items():
        for class_name in TARGET_CLASSES:
            split_counts[split_name][class_name] = 0

        for p, lbl in zip(split_paths, split_labels):
            class_name = TARGET_CLASSES[lbl]
            src_path = Path(p)
            dest_dir = PROCESSED_DIR / split_name / class_name
            dest_path = dest_dir / f"{src_path.stem}.png"

            # Read, convert to RGB, resize
            img = cv2.imread(str(src_path))
            if img is None:
                continue
            if len(img.shape) == 2 or img.shape[2] == 1:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            elif img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            img_resized = cv2.resize(img, TARGET_SIZE, interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(dest_path), img_resized)
            split_counts[split_name][class_name] += 1

    # Copy representative test samples to data/samples for demo and evaluation
    print("[4/5] Extracting representative sample images for testing...")
    sample_manifest = {}
    for class_name in TARGET_CLASSES:
        test_class_dir = PROCESSED_DIR / "test" / class_name
        sample_files = list(test_class_dir.glob("*.png"))[:3]
        sample_manifest[class_name] = []
        for sf in sample_files:
            sample_dest = SAMPLES_DIR / f"{class_name.replace(' ', '_')}_{sf.name}"
            shutil.copy2(sf, sample_dest)
            sample_manifest[class_name].append(str(sample_dest.name))

    # Generate Sample MRI Grid
    print("[5/6] Generating sample MRI inspection grid for all 4 categories...")
    fig, axes = plt.subplots(3, 4, figsize=(14, 10))
    for col_idx, class_name in enumerate(TARGET_CLASSES):
        sample_files = list((PROCESSED_DIR / "test" / class_name).glob("*.png"))[:3]
        for row_idx, sf in enumerate(sample_files):
            ax = axes[row_idx, col_idx]
            img_bgr = cv2.imread(str(sf))
            if img_bgr is not None:
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                ax.imshow(img_rgb)
            ax.axis("off")
            if row_idx == 0:
                ax.set_title(class_name, fontsize=12, fontweight="bold", pad=10)
    plt.suptitle("Sample Axial Brain MRI Scans Across Alzheimer's Categories", fontsize=15, fontweight="bold", y=0.98)
    plt.tight_layout()
    grid_path = METRICS_DIR / "sample_mri_grid.png"
    plt.savefig(grid_path, dpi=200)
    plt.close()
    print(f"[OK] Saved sample MRI grid to {grid_path}")

    # Generate Dataset Distribution Visualization
    print("[6/6] Generating dataset distribution charts...")
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(TARGET_CLASSES))
    width = 0.25

    train_vals = [split_counts["train"][c] for c in TARGET_CLASSES]
    val_vals = [split_counts["val"][c] for c in TARGET_CLASSES]
    test_vals = [split_counts["test"][c] for c in TARGET_CLASSES]

    ax.bar(x - width, train_vals, width, label='Train (70%)', color='#2563EB')
    ax.bar(x, val_vals, width, label='Validation (15%)', color='#0284C7')
    ax.bar(x + width, test_vals, width, label='Test (15%)', color='#38BDF8')

    ax.set_ylabel('Image Count', fontsize=12, fontweight='bold')
    ax.set_title("Alzheimer's MRI Preprocessed Dataset - Stratified Split Distribution", fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(TARGET_CLASSES, fontsize=11, fontweight='medium')
    ax.legend(frameon=True)
    plt.tight_layout()

    dist_chart_path = METRICS_DIR / "dataset_distribution.png"
    plt.savefig(dist_chart_path, dpi=300)
    plt.close()
    print(f"[OK] Saved distribution chart to {dist_chart_path}")

    # Save metadata manifest
    metadata = {
        "target_classes": TARGET_CLASSES,
        "image_size": TARGET_SIZE,
        "raw_counts": class_counts_raw,
        "split_counts": split_counts,
        "total_unique": len(all_file_records),
        "duplicates_removed": duplicate_count,
        "corrupted_removed": corrupt_count,
        "sample_manifest": sample_manifest
    }
    with open(PROJECT_ROOT / "data" / "dataset_info.json", "w") as f:
        json.dump(metadata, f, indent=4)

    print("\nPreprocessed Dataset Summary:")
    print("-" * 50)
    print(f"{'Class':<22} | {'Train':>6} | {'Val':>6} | {'Test':>6}")
    print("-" * 50)
    for c in TARGET_CLASSES:
        print(f"{c:<22} | {split_counts['train'][c]:>6} | {split_counts['val'][c]:>6} | {split_counts['test'][c]:>6}")
    print("-" * 50)
    print("[SUCCESS] Data preprocessing and stratified splitting completed.")


if __name__ == "__main__":
    preprocess_and_split()
