"""
Keramorph – Feature extraction from ceramic profile images.

Two complementary representations:
  1. **Shape descriptors** (Fourier, Hu moments, geometric) → for baseline models.
  2. **Normalised contour image** → for CNN / Siamese models.
"""
from __future__ import annotations

import cv2
import numpy as np
from dataclasses import dataclass

__all__ = [
    "ContourResult",
    "extract_contour",
    "normalise_profile",
    "fourier_descriptors",
    "hu_moments",
    "geometric_features",
    "extract_all_descriptors",
    "assess_quality",
]


# ── data classes ─────────────────────────────────────────

@dataclass
class ContourResult:
    """Result of contour extraction."""
    contour: np.ndarray          # largest contour (N, 1, 2)
    mask: np.ndarray             # binary mask H×W
    bbox: tuple[int, int, int, int]  # x, y, w, h
    area: float
    perimeter: float


@dataclass
class QualityReport:
    """Input quality assessment."""
    score: float                 # 0..1
    warnings: list[str]
    ok: bool


# ── contour extraction ──────────────────────────────────

def extract_contour(
    img_gray: np.ndarray,
    method: str = "canny",
    canny_low: int = 50,
    canny_high: int = 150,
    morph_kernel: int = 5,
    morph_iters: int = 2,
) -> ContourResult | None:
    """Extract the dominant contour from a grayscale image.

    Returns *None* when no significant contour is found.
    """
    # binarise
    if method == "canny":
        edges = cv2.Canny(img_gray, canny_low, canny_high)
    elif method == "threshold":
        _, edges = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif method == "adaptive":
        edges = cv2.adaptiveThreshold(
            img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
    else:
        raise ValueError(f"Unknown contour method: {method}")

    # morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_kernel, morph_kernel))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=morph_iters)
    edges = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    if area < 100:  # noise threshold
        return None

    x, y, w, h = cv2.boundingRect(largest)
    if w >= img_gray.shape[1] - 1 and h >= img_gray.shape[0] - 1:  # whole image
        return None

    mask = np.zeros_like(img_gray)
    cv2.drawContours(mask, [largest], -1, 255, thickness=cv2.FILLED)

    return ContourResult(
        contour=largest,
        mask=mask,
        bbox=(x, y, w, h),
        area=area,
        perimeter=cv2.arcLength(largest, closed=True),
    )


# ── normalisation ───────────────────────────────────────

def normalise_profile(
    img_gray: np.ndarray,
    contour_result: ContourResult,
    target_size: tuple[int, int] = (224, 224),
) -> np.ndarray:
    """Crop to bounding box, centre, scale and return binary contour image."""
    x, y, w, h = contour_result.bbox
    pad = 10
    x0 = max(x - pad, 0)
    y0 = max(y - pad, 0)
    x1 = min(x + w + pad, img_gray.shape[1])
    y1 = min(y + h + pad, img_gray.shape[0])

    crop = contour_result.mask[y0:y1, x0:x1]

    # resize keeping aspect ratio (pad to square first)
    h_c, w_c = crop.shape[:2]
    side = max(h_c, w_c)
    canvas = np.zeros((side, side), dtype=np.uint8)
    dy = (side - h_c) // 2
    dx = (side - w_c) // 2
    canvas[dy : dy + h_c, dx : dx + w_c] = crop

    normalised = cv2.resize(canvas, target_size, interpolation=cv2.INTER_AREA)
    return normalised


# ── shape descriptors ───────────────────────────────────

def fourier_descriptors(contour: np.ndarray, num_descriptors: int = 64) -> np.ndarray:
    """Elliptic Fourier-like descriptors via DFT on contour coordinates."""
    pts = contour.squeeze()  # (N, 2)
    if pts.ndim != 2 or pts.shape[0] < 4:
        return np.zeros(num_descriptors, dtype=np.float64)

    # complex representation
    z = pts[:, 0].astype(np.float64) + 1j * pts[:, 1].astype(np.float64)
    z -= z.mean()  # centre

    coeffs = np.fft.fft(z)
    # take low-frequency coefficients (translation-invariant via centering)
    n = min(num_descriptors, len(coeffs))
    desc = np.abs(coeffs[1 : n + 1])  # skip DC

    # normalise by first coefficient for scale-invariance
    if desc[0] != 0:
        desc = desc / desc[0]

    # pad if contour had fewer points than requested
    if len(desc) < num_descriptors:
        desc = np.pad(desc, (0, num_descriptors - len(desc)))
    return desc[:num_descriptors]


def hu_moments(contour: np.ndarray) -> np.ndarray:
    """7 Hu moments (log-transformed)."""
    moments = cv2.moments(contour)
    hu = cv2.HuMoments(moments).flatten()
    # log transform for better numerical range
    hu = -np.sign(hu) * np.log10(np.abs(hu) + 1e-12)
    return hu  # shape (7,)


def geometric_features(contour_result: ContourResult) -> dict[str, float]:
    """Hand-crafted geometric features."""
    _, _, w, h = contour_result.bbox
    aspect_ratio = w / max(h, 1)

    hull = cv2.convexHull(contour_result.contour)
    hull_area = cv2.contourArea(hull)
    solidity = contour_result.area / max(hull_area, 1)

    circularity = (
        4 * np.pi * contour_result.area / max(contour_result.perimeter ** 2, 1)
    )

    return {
        "aspect_ratio": float(aspect_ratio),
        "solidity": float(solidity),
        "circularity": float(circularity),
        "extent": float(contour_result.area / max(w * h, 1)),
    }


def extract_all_descriptors(
    contour_result: ContourResult,
    num_fourier: int = 64,
) -> np.ndarray:
    """Concatenate all descriptors into a single feature vector."""
    fd = fourier_descriptors(contour_result.contour, num_fourier)
    hu = hu_moments(contour_result.contour)
    geo = geometric_features(contour_result)
    geo_arr = np.array(list(geo.values()), dtype=np.float64)
    return np.concatenate([fd, hu, geo_arr])


# ── quality assessment ──────────────────────────────────

def assess_quality(
    img_gray: np.ndarray,
    contour_result: ContourResult | None,
) -> QualityReport:
    """Heuristic quality check on the input image + contour."""
    warnings: list[str] = []
    score = 1.0

    h, w = img_gray.shape[:2]

    # too small
    if h < 64 or w < 64:
        warnings.append("image_too_small")
        score -= 0.3

    # very low contrast
    std = float(np.std(img_gray))
    if std < 20:
        warnings.append("low_contrast")
        score -= 0.2

    if contour_result is None:
        warnings.append("no_contour_detected")
        return QualityReport(score=max(score - 0.5, 0), warnings=warnings, ok=False)

    # contour covers too little of the image
    img_area = h * w
    fill = contour_result.area / img_area
    if fill < 0.02:
        warnings.append("contour_too_small")
        score -= 0.2
    elif fill > 0.95:
        warnings.append("contour_fills_entire_image")
        score -= 0.1

    # extreme aspect ratio (possible bad crop / perspective)
    _, _, bw, bh = contour_result.bbox
    ar = bw / max(bh, 1)
    if ar > 5 or ar < 0.2:
        warnings.append("extreme_aspect_ratio")
        score -= 0.15

    score = max(score, 0.0)
    return QualityReport(score=round(score, 2), warnings=warnings, ok=len(warnings) == 0)
