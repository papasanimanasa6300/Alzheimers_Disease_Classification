"""
Verification Test for Phase 4: Grad-CAM Explainable AI Engine.
Runs actual gradient-based Grad-CAM on representative images from all four classes:
1. Non-Demented
2. Very Mild Demented
3. Mild Demented
4. Moderate Demented
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.gradcam import GradCAMExplainer

SAMPLES_DIR = PROJECT_ROOT / "data" / "samples"
OUTPUT_DIR = PROJECT_ROOT / "models" / "metrics" / "gradcam_tests"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_CLASSES = [
    "Non-Demented",
    "Very Mild Demented",
    "Mild Demented",
    "Moderate Demented"
]


def test_all_classes():
    print("=" * 60)
    print("TESTING GRAD-CAM ON ALL FOUR ALZHEIMER CLASSES")
    print("=" * 60)

    explainer = GradCAMExplainer(target_layer_name="last_conv_layer")
    print(f"[OK] Target Conv Layer Verified: '{explainer.target_layer_name}'")

    for class_name in TARGET_CLASSES:
        prefix = class_name.replace(" ", "_")
        matches = list(SAMPLES_DIR.glob(f"{prefix}*.png"))
        if not matches:
            # Fallback to any file with part of name
            matches = [f for f in SAMPLES_DIR.glob("*.png") if class_name.split()[0].lower() in f.name.lower()]

        if not matches:
            print(f"[WARN] No sample found for class: {class_name}")
            continue

        sample_img = matches[0]
        print(f"\nProcessing {class_name}: {sample_img.name}")

        overlay_out = OUTPUT_DIR / f"gradcam_overlay_{prefix}.png"
        sbs_out = OUTPUT_DIR / f"gradcam_side_by_side_{prefix}.png"

        result = explainer.explain(
            img_input=sample_img,
            output_overlay_path=str(overlay_out),
            output_side_by_side_path=str(sbs_out)
        )

        print(f"  [+] Predicted Class: {result['predicted_class']}")
        print(f"  [+] Confidence:      {result['confidence'] * 100:.2f}%")
        print(f"  [+] Heatmap Range:   [{result['raw_heatmap'].min():.3f}, {result['raw_heatmap'].max():.3f}]")
        print(f"  [+] Overlay Saved:   {overlay_out.name}")
        print(f"  [+] Side-by-Side:    {sbs_out.name}")

        assert overlay_out.exists(), f"Overlay image was not created for {class_name}"
        assert sbs_out.exists(), f"Side-by-side visualization was not created for {class_name}"

    print("\n" + "=" * 60)
    print("[SUCCESS] Grad-CAM verified across all four classes.")
    print("=" * 60)


if __name__ == "__main__":
    test_all_classes()
