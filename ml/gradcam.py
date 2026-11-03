"""
Explainable AI (XAI) Grad-CAM Module for Alzheimer's Brain MRI.
Implements gradient-weighted Class Activation Mapping (Grad-CAM)
as described by Selvaraju et al. (2017).
- Computes exact gradients of the target class score w.r.t. the last convolutional layer.
- Produces normalized activation heatmaps.
- Blends heatmaps onto MRI scans using OpenCV JET colormap.
- Generates side-by-side diagnostic visualizations.
"""

import os
import sys
from pathlib import Path
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

import tensorflow as tf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "saved_models" / "alzheimer_cnn_best.keras"

TARGET_CLASSES = [
    "Non-Demented",
    "Very Mild Demented",
    "Mild Demented",
    "Moderate Demented"
]
IMG_SIZE = (224, 224)


class GradCAMExplainer:
    """True Gradient-Weighted Class Activation Mapping (Grad-CAM) Engine."""

    def __init__(self, model_path=None, target_layer_name=None):
        self.model_path = model_path or MODEL_PATH
        self.target_layer_name = target_layer_name
        self.model = None
        self.grad_model = None
        self._load_model()

    def _load_model(self):
        """Load model and construct gradient computation sub-model."""
        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"Model file not found at: {self.model_path}")

        self.model = tf.keras.models.load_model(str(self.model_path))

        # Auto-detect last Conv2D layer if not specified
        if not self.target_layer_name:
            for layer in reversed(self.model.layers):
                if isinstance(layer, tf.keras.layers.Conv2D) or "conv" in layer.name.lower():
                    self.target_layer_name = layer.name
                    break

        if not self.target_layer_name:
            raise ValueError("Could not find any Convolutional layer in the model for Grad-CAM.")

        # Build submodel that maps model input -> (target conv layer output, predictions)
        target_layer = self.model.get_layer(self.target_layer_name)
        self.grad_model = tf.keras.models.Model(
            inputs=self.model.inputs,
            outputs=[target_layer.output, self.model.output]
        )
        print(f"[OK] GradCAM initialized with target layer: '{self.target_layer_name}'")

    def preprocess_image(self, img_input):
        """
        Takes image path, numpy array, or PIL Image.
        Returns:
            preprocessed_tensor: (1, 224, 224, 3) normalized [0, 1]
            original_image_rgb: (224, 224, 3) uint8 [0, 255]
        """
        if isinstance(img_input, (str, Path)):
            img = cv2.imread(str(img_input))
            if img is None:
                raise ValueError(f"Could not read image from {img_input}")
            if len(img.shape) == 2 or img.shape[2] == 1:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            else:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        elif isinstance(img_input, np.ndarray):
            img = img_input.copy()
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            elif img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        elif isinstance(img_input, Image.Image):
            img = np.array(img_input.convert("RGB"))
        else:
            raise TypeError("Unsupported image input type.")

        orig_resized = cv2.resize(img, IMG_SIZE, interpolation=cv2.INTER_AREA)
        tensor = orig_resized.astype(np.float32)
        tensor = np.expand_dims(tensor, axis=0)
        return tensor, orig_resized

    def compute_gradcam(self, img_tensor, class_index=None):
        """
        Compute Grad-CAM heatmap using gradient tape.
        Args:
            img_tensor: preprocessed input tensor of shape (1, 224, 224, 3)
            class_index: int target class index. If None, uses top predicted class.
        Returns:
            heatmap: (224, 224) float32 in [0, 1]
            predicted_class_idx: int
            confidence: float
            all_probabilities: list of floats
        """
        with tf.GradientTape() as tape:
            conv_outputs, predictions = self.grad_model(img_tensor)
            all_probs = predictions[0].numpy()
            
            if class_index is None:
                class_index = int(tf.argmax(predictions[0]))

            confidence = float(all_probs[class_index])
            target_score = predictions[:, class_index]

        # Gradients of target class score w.r.t feature maps of last conv layer
        grads = tape.gradient(target_score, conv_outputs)

        # Global average pooling over spatial dimensions (H, W) -> alpha weights
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

        # Weight feature maps by importance
        conv_outputs = conv_outputs[0]
        heatmap = tf.reduce_sum(tf.multiply(pooled_grads, conv_outputs), axis=-1)

        # Apply ReLU to retain only positive influence
        heatmap = tf.maximum(heatmap, 0.0)

        # Normalize between 0 and 1
        max_val = tf.reduce_max(heatmap)
        if max_val > 0:
            heatmap = heatmap / max_val

        heatmap = heatmap.numpy()
        # Resize heatmap to target image size
        heatmap_resized = cv2.resize(heatmap, IMG_SIZE, interpolation=cv2.INTER_LINEAR)

        return heatmap_resized, class_index, confidence, all_probs.tolist()

    def generate_overlay(self, original_rgb, heatmap, alpha=0.45, colormap=cv2.COLORMAP_JET):
        """
        Overlay colormapped heatmap onto original MRI.
        Args:
            original_rgb: (224, 224, 3) uint8 [0, 255]
            heatmap: (224, 224) float [0, 1]
            alpha: float blending weight for heatmap
        Returns:
            superimposed_img: (224, 224, 3) uint8 [0, 255] RGB
        """
        heatmap_uint8 = np.uint8(255 * heatmap)
        colored_heatmap = cv2.applyColorMap(heatmap_uint8, colormap)
        colored_heatmap = cv2.cvtColor(colored_heatmap, cv2.COLOR_BGR2RGB)

        overlay = cv2.addWeighted(colored_heatmap, alpha, original_rgb, 1.0 - alpha, 0)
        return overlay, colored_heatmap

    def generate_side_by_side(self, original_rgb, heatmap, overlay, predicted_class, confidence, output_path=None):
        """
        Create a side-by-side medical visualization:
        [Original MRI] | [Grad-CAM Heatmap] | [Overlay Analysis]
        Structured with strict grid margins and no text collisions.
        """
        fig = plt.figure(figsize=(15, 5.8), facecolor="#0B132B")
        gs = fig.add_gridspec(1, 3, top=0.76, bottom=0.08, left=0.05, right=0.95, wspace=0.15)

        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[0, 2])

        # Header Titles with generous top clearance
        fig.text(
            0.5, 0.94,
            "Explainable AI (Grad-CAM) Neuroimaging Diagnostic Attention",
            ha="center", va="top",
            color="#FFFFFF", fontsize=15, fontweight="bold"
        )
        fig.text(
            0.5, 0.85,
            f"Predicted Stage: {predicted_class}   |   Diagnostic Confidence: {confidence * 100:.2f}%",
            ha="center", va="top",
            color="#38BDF8", fontsize=12, fontweight="bold"
        )

        # 1. Original MRI
        ax1.imshow(original_rgb)
        ax1.set_title("1. Original Brain MRI", color="#F8FAFC", fontsize=12, fontweight="bold", pad=10)
        ax1.axis("off")

        # 2. Heatmap
        ax2.imshow(heatmap, cmap="jet")
        ax2.set_title("2. Grad-CAM Activation Heatmap", color="#F8FAFC", fontsize=12, fontweight="bold", pad=10)
        ax2.axis("off")

        # 3. Overlay
        ax3.imshow(overlay)
        ax3.set_title(f"3. Diagnostic Overlay ({confidence * 100:.1f}%)", color="#38BDF8", fontsize=12, fontweight="bold", pad=10)
        ax3.axis("off")

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(str(output_path), dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
            plt.close(fig)
            return str(output_path)
        else:
            plt.close(fig)
            return None

    def explain(self, img_input, output_overlay_path=None, output_side_by_side_path=None, output_heatmap_path=None):
        """
        Full end-to-end explanation for a single MRI scan.
        """
        img_tensor, orig_rgb = self.preprocess_image(img_input)
        heatmap, pred_idx, conf, probs = self.compute_gradcam(img_tensor)
        pred_label = TARGET_CLASSES[pred_idx]

        overlay, colored_heatmap = self.generate_overlay(orig_rgb, heatmap)

        if output_heatmap_path:
            Path(output_heatmap_path).parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_heatmap_path), cv2.cvtColor(colored_heatmap, cv2.COLOR_RGB2BGR))

        if output_overlay_path:
            Path(output_overlay_path).parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_overlay_path), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

        sbs_path = None
        if output_side_by_side_path:
            sbs_path = self.generate_side_by_side(orig_rgb, heatmap, overlay, pred_label, conf, output_side_by_side_path)

        return {
            "predicted_class": pred_label,
            "predicted_index": pred_idx,
            "confidence": conf,
            "all_probabilities": {cls: float(probs[i]) for i, cls in enumerate(TARGET_CLASSES)},
            "overlay_path": str(output_overlay_path) if output_overlay_path else None,
            "heatmap_path": str(output_heatmap_path) if output_heatmap_path else None,
            "side_by_side_path": sbs_path,
            "raw_heatmap": heatmap
        }
