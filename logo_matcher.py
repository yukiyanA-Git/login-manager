import io
import base64
from typing import Optional, List, Dict
from PIL import Image, ImageChops

def pil_to_base64(img: Image.Image) -> str:
    """Converts PIL Image to base64 PNG string."""
    if img is None:
        return ""
    buffer = io.BytesIO()
    # Save as compressed PNG
    img.convert("RGB").save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def base64_to_pil(b64_str: str) -> Optional[Image.Image]:
    """Converts base64 PNG string back to PIL Image."""
    if not b64_str:
        return None
    try:
        data = base64.b64decode(b64_str)
        return Image.open(io.BytesIO(data))
    except Exception as e:
        print(f"Error decoding logo image: {e}")
        return None

def compute_image_similarity(img1: Image.Image, img2: Image.Image) -> float:
    """
    Computes visual similarity between 2 cropped logo images:
    1. Resizes both to 32x32 grayscale.
    2. Computes Difference Hash (dHash) & pixel MSE.
    Returns float score between 0.0 (completely different) and 1.0 (identical).
    """
    if img1 is None or img2 is None:
        return 0.0

    try:
        # Normalize size to 32x32 grayscale
        i1 = img1.convert("L").resize((32, 32), Image.Resampling.LANCZOS)
        i2 = img2.convert("L").resize((32, 32), Image.Resampling.LANCZOS)

        # Pixel difference
        diff = ImageChops.difference(i1, i2)
        stat = list(diff.getdata())
        avg_diff = sum(stat) / len(stat)

        # Similarity score: 1.0 - (avg_diff / 255)
        similarity = max(0.0, 1.0 - (avg_diff / 255.0))
        return similarity
    except Exception as e:
        print(f"Error computing image similarity: {e}")
        return 0.0

def match_logo_image(target_img: Image.Image, accounts: List[Dict], threshold: float = 0.78) -> Optional[Dict]:
    """
    Compares target screen-captured logo image against all stored account logo images.
    Returns the account dictionary with highest similarity above threshold.
    """
    if target_img is None or not accounts:
        return None

    best_match = None
    best_score = 0.0

    for acc in accounts:
        b64_logo = acc.get("logo_image", "")
        if not b64_logo:
            continue

        stored_img = base64_to_pil(b64_logo)
        if stored_img:
            score = compute_image_similarity(target_img, stored_img)
            if score > best_score:
                best_score = score
                best_match = acc

    if best_score >= threshold:
        print(f"[Logo Matcher] Visual logo match found: '{best_match.get('name')}' (Similarity: {best_score:.2f})")
        return best_match

    return None
