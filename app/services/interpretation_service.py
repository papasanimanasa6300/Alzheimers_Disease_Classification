"""
Clinical Interpretation Service for Alzheimer's Neuroimaging Analysis.
Translates technical CNN classifications and Grad-CAM activations into
crystal-clear, patient-friendly, and clinically meaningful explanations.
"""

TARGET_CLASSES = [
    "Non-Demented",
    "Very Mild Demented",
    "Mild Demented",
    "Moderate Demented"
]

STAGE_DETAILS = {
    "Non-Demented": {
        "title": "Healthy / Normal (No Dementia Detected)",
        "short_title": "Normal / Healthy",
        "severity": "Normal",
        "severity_badge": "bg-success",
        "badge_class": "badge-nondemented",
        "icon": "fa-circle-check",
        "theme_color": "#198754",
        "summary": "Your brain MRI shows healthy, normal brain structure with no significant signs of Alzheimer's disease.",
        "what_it_means": (
            "The neural network detected intact brain tissue across all evaluated cortical regions. "
            "The fluid cavities (ventricles) and the memory centers (hippocampus) are of normal size and volume "
            "for your age group. There is no evidence of accelerated brain shrinkage."
        ),
        "daily_life_impact": (
            "Daily memory, language, spatial awareness, and decision-making abilities are expected to be normal. "
            "Occasional everyday forgetfulness (such as misplacing an item for a moment) is a natural part of normal aging and does not indicate dementia."
        ),
        "brain_features_observed": (
            "Normal brain volume, healthy cortical thickness, and normal fluid cavities with no signs of abnormal tissue loss."
        ),
        "gradcam_guide": (
            "The Grad-CAM heatmap shows balanced, low-level baseline signals (mostly cool blue/cyan) with no focal red disease hotspots."
        ),
        "recommended_steps": [
            "Maintain an active physical and mental routine (daily walking, reading, puzzles).",
            "Take the online Cognitive Assessment in this app to document your healthy memory baseline.",
            "Continue standard annual routine health checkups with your primary physician."
        ]
    },
    "Very Mild Demented": {
        "title": "Stage 1: Very Mild Impairment (Early Warning Signs)",
        "short_title": "Very Mild Impairment",
        "severity": "Early Warning",
        "severity_badge": "bg-warning text-dark",
        "badge_class": "badge-verymild",
        "icon": "fa-triangle-exclamation",
        "theme_color": "#ffc107",
        "summary": "The AI detected early, subtle changes in brain structure often known as Minimal Cognitive Impairment (MCI).",
        "what_it_means": (
            "This is the earliest detectable stage. The scan shows very mild tissue thinning in the brain's memory center (hippocampus) "
            "and subtle widening of the brain's internal fluid cavities (lateral ventricles). "
            "Early detection at this stage provides the best opportunity for medical guidance, diet, and cognitive exercises to help protect brain health."
        ),
        "daily_life_impact": (
            "The individual is fully independent in daily living, working, and self-care. "
            "However, they may notice subtle memory lapses like forgetting recent conversations, taking slightly longer to find words, or occasionally misplacing items."
        ),
        "brain_features_observed": (
            "Subtle reduction in hippocampal volume and early widening of fluid chambers (ventricles) compared to a fully healthy baseline."
        ),
        "gradcam_guide": (
            "Red and yellow hotspots in the Grad-CAM heatmap highlight where the AI spotted these subtle volume changes, "
            "particularly around the ventricles and the medial temporal lobes."
        ),
        "recommended_steps": [
            "Consult a neurologist or memory specialist for a formal in-person clinical review.",
            "Complete our 5-domain Cognitive Assessment to test memory, orientation, and attention performance.",
            "Adopt brain-supportive habits: Mediterranean diet, regular cardiovascular exercise, quality sleep, and social engagement.",
            "Plan a follow-up scan in 6 to 12 months to monitor any changes over time."
        ]
    },
    "Mild Demented": {
        "title": "Stage 2: Mild Alzheimer's Disease",
        "short_title": "Mild Dementia",
        "severity": "Moderate Concern",
        "severity_badge": "bg-warning text-dark",
        "badge_class": "badge-mild",
        "icon": "fa-circle-exclamation",
        "theme_color": "#fd7e14",
        "summary": "The scan displays clear structural changes consistent with mild-stage Alzheimer's disease.",
        "what_it_means": (
            "The neural network identified evident shrinkage (atrophy) in the brain's memory and language regions. "
            "The ventricles (fluid spaces) are visibly enlarged because surrounding brain tissue has reduced in volume. "
            "This pattern typically indicates active neurodegenerative progression."
        ),
        "daily_life_impact": (
            "Noticeable memory difficulty in daily life: forgetting names of acquaintances, losing track of bills or appointments, "
            "or feeling confused in unfamiliar surroundings. Assistance may be needed for complex tasks like finances, medications, or navigation."
        ),
        "brain_features_observed": (
            "Noticeable bilateral enlargement of the ventricles and distinct shrinkage in the temporal lobes and hippocampus."
        ),
        "gradcam_guide": (
            "Prominent red and yellow attention areas indicate where the AI focused heavily on the enlarged ventricular borders and temporal tissue loss."
        ),
        "recommended_steps": [
            "Schedule an appointment with a neurologist for comprehensive diagnostic testing (MMSE/MoCA).",
            "Discuss FDA-approved therapeutic treatments and lifestyle interventions with your medical provider.",
            "Establish structured daily routines and calendar reminders to assist with daily activities.",
            "Take the online cognitive assessment to document a functional baseline for your doctor."
        ]
    },
    "Moderate Demented": {
        "title": "Stage 3: Moderate Alzheimer's Disease",
        "short_title": "Moderate Dementia",
        "severity": "Advanced Care Needed",
        "severity_badge": "bg-danger",
        "badge_class": "badge-moderate",
        "icon": "fa-circle-radiation",
        "theme_color": "#dc3545",
        "summary": "The scan exhibits pronounced brain tissue shrinkage characteristic of moderate Alzheimer's disease.",
        "what_it_means": (
            "The MRI reveals substantial cerebral atrophy across multiple brain lobes. "
            "The ventricles are significantly enlarged and both memory and cognitive processing structures show considerable volume loss."
        ),
        "daily_life_impact": (
            "Significant memory impairment extending to personal history and details of everyday life. "
            "The individual may have difficulty recognizing familiar faces, remembering the current year, and typically requires assistance with daily activities like dressing, bathing, or preparing food."
        ),
        "brain_features_observed": (
            "Widespread brain tissue shrinkage (cortical atrophy) with pronounced ventricular expansion."
        ),
        "gradcam_guide": (
            "Large, intense red regions across both hemispheres demonstrate where widespread tissue loss triggered the model's highest-confidence diagnosis."
        ),
        "recommended_steps": [
            "Prompt medical consultation with a neurology and geriatric multidisciplinary care team.",
            "Establish supportive full-time care strategies and a secure, comfortable living environment.",
            "Work with healthcare professionals and family support groups for specialized dementia care planning."
        ]
    }
}


def get_stage_info(category_name):
    """Retrieve full clinical and patient-friendly information for a category."""
    return STAGE_DETAILS.get(category_name, STAGE_DETAILS["Very Mild Demented"])


def format_probability_breakdown(all_probs, predicted_category=None):
    """
    Format the 4-class probability dictionary into an ordered, styled list
    for intuitive visual cards and charts.
    """
    if not all_probs or not isinstance(all_probs, dict):
        # Fallback distribution
        all_probs = {cls: 0.25 for cls in TARGET_CLASSES}

    result = []
    for cls in TARGET_CLASSES:
        prob = float(all_probs.get(cls, 0.0))
        details = STAGE_DETAILS.get(cls, {})
        is_primary = (cls == predicted_category)
        result.append({
            "category": cls,
            "short_title": details.get("short_title", cls),
            "probability": prob,
            "percentage": f"{prob * 100:.1f}%",
            "percent_val": round(prob * 100, 1),
            "theme_color": details.get("theme_color", "#0d6efd"),
            "badge_class": details.get("badge_class", "bg-secondary"),
            "is_primary": is_primary
        })
    return result
