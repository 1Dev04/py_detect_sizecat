import math

# =========================
# GLOBAL REFERENCES
# =========================

REAL_TORSO_HEIGHT_CM = 25

BREED_MODIFIER = {
    "maine_coon": 1.15,
    "ragdoll": 1.10,
    "british_shorthair": 1.05,
    "siamese": 0.95,
    "unknown": 1.0
}

# =========================
# POSTURE
# =========================

def estimate_posture(w, h):
    ratio = w / max(h, 1)

    if ratio > 1.4:
        return "lying", 0.85
    elif ratio < 0.9:
        return "sitting", 0.92
    else:
        return "standing", 1.0


# =========================
# BODY METRICS
# =========================

def estimate_body_metrics(bbox):
    x1, y1, x2, y2 = bbox
    w = max(x2 - x1, 1)
    h = max(y2 - y1, 1)

    posture, posture_factor = estimate_posture(w, h)

    torso_ratio = {
        "lying": 0.55,
        "sitting": 0.60,
        "standing": 0.65
    }[posture]

    effective_height = h * torso_ratio
    pixel_to_cm = REAL_TORSO_HEIGHT_CM / max(effective_height, 1)

    body_length_cm = round(
        w * pixel_to_cm * (1.0 if posture == "lying" else 0.9),
        1
    )

    chest_base = math.pi * (w * pixel_to_cm) * 0.6
    chest_cm = round(chest_base * posture_factor, 1)
    neck_cm = round(chest_cm * 0.62, 1)

    # quality & confidence
    size_ratio = min(1.0, (w * h) / (300 * 300))
    aspect_score = 1.0 if 0.6 < w / h < 1.8 else 0.6
    confidence = round((size_ratio * 0.6 + aspect_score * 0.4), 2)

    quality_flag = (
        "good" if confidence > 0.75 else
        "medium" if confidence > 0.5 else
        "poor"
    )

    return {
        "posture": posture,
        "chest_cm": chest_cm,
        "neck_cm": neck_cm,
        "body_length_cm": body_length_cm,
        "confidence": confidence,
        "quality_flag": quality_flag
    }


# =========================
# WEIGHT
# =========================

def estimate_weight(chest_cm, body_length_cm, breed="unknown"):
    base_weight = (chest_cm ** 2 * body_length_cm) / 3000
    return round(base_weight * BREED_MODIFIER.get(breed, 1.0), 1)


# =========================
# SIZE (CLOTHING)
# =========================

def determine_size(weight, chest_cm):
    if weight < 2.5 or chest_cm < 24:
        return "XS"
    if weight < 4 or chest_cm < 32:
        return "S"
    if weight < 6 or chest_cm < 38:
        return "M"
    if weight < 8.5 or chest_cm < 45:
        return "L"
    return "XL"


# =========================
# MAIN ENTRY
# =========================

def analyze_cat(image_path: str, bounding_box: list, cat_color: str = None):
    """
    🔥 CatAnalyzer V4 (10/10)
    - anatomy-based
    - posture aware
    - clothing ready
    """

    breed = "unknown"  # ML plug-in later

    metrics = estimate_body_metrics(bounding_box)

    weight = estimate_weight(
        metrics["chest_cm"],
        metrics["body_length_cm"],
        breed
    )

    size_category = determine_size(weight, metrics["chest_cm"])

    return {
        "breed": breed,
        "cat_color": cat_color,
        "weight": weight,
        "size_category": size_category,
        "chest_cm": metrics["chest_cm"],
        "neck_cm": metrics["neck_cm"],
        "body_length_cm": metrics["body_length_cm"],
        "posture": metrics["posture"],
        "confidence": metrics["confidence"],
        "quality_flag": metrics["quality_flag"],
        "analysis_method": "cv_heuristic_v4"
    }
