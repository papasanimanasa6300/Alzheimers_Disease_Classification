"""
High-Performance Convolutional Neural Network (CNN) Model Architecture and Training Pipeline.
- 4-Class Classification: Non-Demented, Very Mild Demented, Mild Demented, Moderate Demented.
- Implements Conv2D, ReLU, MaxPooling, Dropout, Flatten, Dense, Softmax.
- Features EarlyStopping, ReduceLROnPlateau, ModelCheckpoint.
- Optimized for fast CPU training throughput with strided initial receptive field.
- Computes class weights to handle dataset imbalance.
- Saves best model to models/saved_models/alzheimer_cnn_best.keras.
"""

import os
import sys
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from sklearn.utils.class_weight import compute_class_weight

import tensorflow as tf
from tensorflow.keras import layers, models, callbacks, optimizers

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_SAVE_DIR = PROJECT_ROOT / "models" / "saved_models"
METRICS_DIR = PROJECT_ROOT / "models" / "metrics"

TARGET_CLASSES = [
    "Non-Demented",
    "Very Mild Demented",
    "Mild Demented",
    "Moderate Demented"
]
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 10


def build_alzheimer_cnn(input_shape=(224, 224, 3), num_classes=4):
    """
    Construct CNN architecture with data augmentation layers and dedicated named
    last convolutional layer for Grad-CAM class activation mapping.
    Uses strided initial receptive field (similar to ResNet/AlexNet) for rapid CPU execution.
    """
    inputs = layers.Input(shape=input_shape, name="mri_input")

    # Rescaling and Augmentation
    x = layers.Rescaling(1.0 / 255.0, name="rescaling")(inputs)
    x = layers.RandomFlip("horizontal", name="aug_flip")(x)
    x = layers.RandomRotation(0.04, name="aug_rot")(x)

    # Block 1: Strided Conv + Pool
    x = layers.Conv2D(32, (5, 5), strides=2, padding="same", activation="relu", name="conv1")(x)
    x = layers.BatchNormalization(name="bn1")(x)
    x = layers.MaxPooling2D((2, 2), name="pool1")(x)
    x = layers.Dropout(0.20, name="drop1")(x)

    # Block 2
    x = layers.Conv2D(64, (3, 3), padding="same", activation="relu", name="conv2")(x)
    x = layers.BatchNormalization(name="bn2")(x)
    x = layers.MaxPooling2D((2, 2), name="pool2")(x)
    x = layers.Dropout(0.25, name="drop2")(x)

    # Block 3
    x = layers.Conv2D(128, (3, 3), padding="same", activation="relu", name="conv3")(x)
    x = layers.BatchNormalization(name="bn3")(x)
    x = layers.MaxPooling2D((2, 2), name="pool3")(x)
    x = layers.Dropout(0.25, name="drop3")(x)

    # Block 4 (Target layer for Grad-CAM)
    x = layers.Conv2D(128, (3, 3), padding="same", activation="relu", name="last_conv_layer")(x)
    x = layers.BatchNormalization(name="bn4")(x)
    x = layers.MaxPooling2D((2, 2), name="pool4")(x)
    x = layers.Dropout(0.30, name="drop4")(x)

    # Classification Head
    x = layers.Flatten(name="flatten")(x)
    x = layers.Dense(128, activation="relu", name="dense1")(x)
    x = layers.BatchNormalization(name="bn_dense")(x)
    x = layers.Dropout(0.40, name="drop_dense1")(x)
    x = layers.Dense(64, activation="relu", name="dense2")(x)
    x = layers.Dropout(0.25, name="drop_dense2")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="predictions")(x)

    model = models.Model(inputs=inputs, outputs=outputs, name="Alzheimer_MRI_CNN")
    model.compile(
        optimizer=optimizers.Adam(learning_rate=0.0006),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    return model


def train(epochs=EPOCHS, batch_size=BATCH_SIZE):
    """Execute training pipeline with tf.data cached datasets and class weighting."""
    MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    train_dir = PROCESSED_DIR / "train"
    val_dir = PROCESSED_DIR / "val"

    if not train_dir.exists() or not val_dir.exists():
        raise FileNotFoundError(f"Processed datasets not found in {PROCESSED_DIR}. Run ml/dataset_preprocessing.py first.")

    print("[1/4] Preparing high-throughput tf.data Datasets...")
    raw_train_ds = tf.keras.utils.image_dataset_from_directory(
        str(train_dir),
        class_names=TARGET_CLASSES,
        label_mode="categorical",
        batch_size=batch_size,
        image_size=IMG_SIZE,
        shuffle=True,
        seed=42
    )

    raw_val_ds = tf.keras.utils.image_dataset_from_directory(
        str(val_dir),
        class_names=TARGET_CLASSES,
        label_mode="categorical",
        batch_size=batch_size,
        image_size=IMG_SIZE,
        shuffle=False
    )

    # Known class counts from preprocessing:
    # Non-Demented: 2240, Very Mild: 1568, Mild: 627, Moderate: 45
    counts = [2240, 1568, 627, 45]
    total_samples = sum(counts)
    class_weight_dict = {
        i: float(total_samples / (len(counts) * c))
        for i, c in enumerate(counts)
    }
    print(f"[INFO] Computed Balanced Class Weights: {class_weight_dict}")

    # Optimize datasets with memory cache and prefetch
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = raw_train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    val_ds = raw_val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    print("[2/4] Constructing CNN Architecture...")
    model = build_alzheimer_cnn(input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3), num_classes=len(TARGET_CLASSES))
    model.summary()

    # Save summary to file
    with open(METRICS_DIR / "model_summary.txt", "w") as f:
        model.summary(print_fn=lambda x: f.write(x + "\n"))

    best_model_path = MODEL_SAVE_DIR / "alzheimer_cnn_best.keras"
    training_callbacks = [
        callbacks.ModelCheckpoint(
            filepath=str(best_model_path),
            monitor="val_accuracy",
            mode="max",
            save_best_only=True,
            verbose=1
        ),
        callbacks.EarlyStopping(
            monitor="val_loss",
            patience=4,
            mode="min",
            restore_best_weights=True,
            verbose=1
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=2,
            min_lr=1e-6,
            verbose=1
        )
    ]

    print(f"[3/4] Training Model for up to {epochs} epochs...")
    history = model.fit(
        train_ds,
        epochs=epochs,
        validation_data=val_ds,
        class_weight=class_weight_dict,
        callbacks=training_callbacks,
        verbose=1
    )

    print("[4/4] Generating Training and Validation Curves...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Accuracy Plot
    ax1.plot(history.history["accuracy"], label="Train Accuracy", color="#2563EB", lw=2)
    ax1.plot(history.history["val_accuracy"], label="Validation Accuracy", color="#059669", lw=2)
    ax1.set_title("Model Accuracy Across Epochs", fontsize=13, fontweight="bold")
    ax1.set_xlabel("Epoch", fontsize=11)
    ax1.set_ylabel("Accuracy", fontsize=11)
    ax1.legend(loc="lower right")
    ax1.grid(True, linestyle="--", alpha=0.6)

    # Loss Plot
    ax2.plot(history.history["loss"], label="Train Loss", color="#DC2626", lw=2)
    ax2.plot(history.history["val_loss"], label="Validation Loss", color="#D97706", lw=2)
    ax2.set_title("Model Loss Across Epochs", fontsize=13, fontweight="bold")
    ax2.set_xlabel("Epoch", fontsize=11)
    ax2.set_ylabel("Categorical Crossentropy Loss", fontsize=11)
    ax2.legend(loc="upper right")
    ax2.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    curves_path = METRICS_DIR / "training_curves.png"
    plt.savefig(curves_path, dpi=300)
    plt.close()
    print(f"[OK] Saved training curves to: {curves_path}")

    # Save history json
    hist_dict = {k: [float(val) for val in v] for k, v in history.history.items()}
    with open(METRICS_DIR / "training_history.json", "w") as f:
        json.dump(hist_dict, f, indent=4)

    print(f"[SUCCESS] Best model successfully saved to: {best_model_path}")
    return model, history


if __name__ == "__main__":
    train()
