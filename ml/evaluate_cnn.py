"""
Independent Model Evaluation Pipeline.
- Evaluates trained CNN on unseen test set.
- Generates Accuracy, Precision, Recall, and F1-score.
- Computes and plots Confusion Matrix.
- Saves detailed Classification Report.
"""

import os
import sys
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support

import tensorflow as tf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_PATH = PROJECT_ROOT / "models" / "saved_models" / "alzheimer_cnn_best.keras"
METRICS_DIR = PROJECT_ROOT / "models" / "metrics"

TARGET_CLASSES = [
    "Non-Demented",
    "Very Mild Demented",
    "Mild Demented",
    "Moderate Demented"
]
IMG_SIZE = (224, 224)
BATCH_SIZE = 32


def evaluate_model():
    """Run full evaluation on the independent test set."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Trained model not found at: {MODEL_PATH}")

    test_dir = PROCESSED_DIR / "test"
    if not test_dir.exists():
        raise FileNotFoundError(f"Test dataset not found in {test_dir}")

    print("[1/4] Loading trained CNN model...")
    model = tf.keras.models.load_model(str(MODEL_PATH))
    print("[OK] Model loaded successfully.")

    print("[2/4] Preparing test dataset...")
    test_ds = tf.keras.utils.image_dataset_from_directory(
        str(test_dir),
        class_names=TARGET_CLASSES,
        label_mode="categorical",
        batch_size=BATCH_SIZE,
        image_size=IMG_SIZE,
        shuffle=False
    )

    print("[3/4] Running inference on independent test dataset...")
    y_true = []
    for _, labels_batch in test_ds:
        y_true.extend(np.argmax(labels_batch.numpy(), axis=1))
    y_true = np.array(y_true)

    y_pred_probs = model.predict(test_ds, verbose=1)
    y_pred = np.argmax(y_pred_probs, axis=1)

    # Compute Metrics
    acc = accuracy_score(y_true, y_pred)
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    prec_weight, rec_weight, f1_weight, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)

    report_str = classification_report(y_true, y_pred, target_names=TARGET_CLASSES, digits=4, zero_division=0)
    report_dict = classification_report(y_true, y_pred, target_names=TARGET_CLASSES, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred)

    print("\n" + "=" * 65)
    print("INDEPENDENT TEST SET EVALUATION RESULTS")
    print("=" * 65)
    print(f"Overall Accuracy:       {acc * 100:.2f}%")
    print(f"Macro Precision:        {prec_macro * 100:.2f}%")
    print(f"Macro Recall:           {rec_macro * 100:.2f}%")
    print(f"Macro F1-Score:         {f1_macro * 100:.2f}%")
    print(f"Weighted F1-Score:      {f1_weight * 100:.2f}%")
    print("-" * 65)
    print("Classification Report:\n")
    print(report_str)
    print("=" * 65)

    print("[4/4] Generating and saving Confusion Matrix visualizations...")
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    # Save Classification Report text and json
    with open(METRICS_DIR / "classification_report.txt", "w") as f:
        f.write("ALZHEIMER'S MRI CNN TEST EVALUATION REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(report_str + "\n\n")
        f.write(f"Accuracy:        {acc:.4f}\n")
        f.write(f"Macro Precision: {prec_macro:.4f}\n")
        f.write(f"Macro Recall:    {rec_macro:.4f}\n")
        f.write(f"Macro F1-Score:  {f1_macro:.4f}\n")

    summary_metrics = {
        "accuracy": float(acc),
        "macro_precision": float(prec_macro),
        "macro_recall": float(rec_macro),
        "macro_f1": float(f1_macro),
        "weighted_f1": float(f1_weight),
        "detailed_metrics": report_dict,
        "confusion_matrix": cm.tolist()
    }
    with open(METRICS_DIR / "evaluation_summary.json", "w") as f:
        json.dump(summary_metrics, f, indent=4)

    # Plot Confusion Matrix
    plt.figure(figsize=(9, 7))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=TARGET_CLASSES,
        yticklabels=TARGET_CLASSES,
        cbar=True,
        annot_kws={"size": 13, "weight": "bold"}
    )
    plt.title("Confusion Matrix - Alzheimer's MRI CNN Test Set", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Predicted Label", fontsize=12, fontweight="bold")
    plt.ylabel("True Clinical Label", fontsize=12, fontweight="bold")
    plt.xticks(rotation=20, ha="right", fontsize=10)
    plt.yticks(rotation=0, fontsize=10)
    plt.tight_layout()

    cm_path = METRICS_DIR / "confusion_matrix.png"
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"[OK] Saved Confusion Matrix to: {cm_path}")

    return summary_metrics


if __name__ == "__main__":
    evaluate_model()
