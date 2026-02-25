"""
Tests – ML feature extraction.
"""
import numpy as np
import pytest

from ml.features.extraction import (
    ContourResult,
    assess_quality,
    extract_contour,
    fourier_descriptors,
    geometric_features,
    hu_moments,
    normalise_profile,
)


def _make_circle_image(size: int = 224, radius: int = 60) -> np.ndarray:
    """Create a synthetic grayscale image with a white circle on black background."""
    img = np.zeros((size, size), dtype=np.uint8)
    cv2 = pytest.importorskip("cv2")
    cv2.circle(img, (size // 2, size // 2), radius, 255, -1)
    return img


class TestExtractContour:
    def test_finds_circle(self) -> None:
        img = _make_circle_image()
        result = extract_contour(img, method="threshold")
        assert result is not None
        assert result.area > 100
        assert result.contour.shape[0] >= 4

    def test_returns_none_for_blank(self) -> None:
        blank = np.zeros((224, 224), dtype=np.uint8)
        result = extract_contour(blank, method="threshold")
        assert result is None

    def test_invalid_method_raises(self) -> None:
        img = _make_circle_image()
        with pytest.raises(ValueError, match="Unknown contour method"):
            extract_contour(img, method="magic")


class TestNormaliseProfile:
    def test_output_shape(self) -> None:
        img = _make_circle_image()
        cr = extract_contour(img, method="threshold")
        assert cr is not None
        norm = normalise_profile(img, cr, target_size=(128, 128))
        assert norm.shape == (128, 128)

    def test_output_is_binary_ish(self) -> None:
        img = _make_circle_image()
        cr = extract_contour(img, method="threshold")
        assert cr is not None
        norm = normalise_profile(img, cr)
        unique = np.unique(norm)
        # should be binary or near-binary (with possible anti-aliasing)
        assert norm.max() > 200
        assert len(unique) > 2  # has some anti-aliasing


class TestDescriptors:
    def test_fourier_shape(self) -> None:
        img = _make_circle_image()
        cr = extract_contour(img, method="threshold")
        assert cr is not None
        fd = fourier_descriptors(cr.contour, num_descriptors=32)
        assert fd.shape == (32,)

    def test_hu_shape(self) -> None:
        img = _make_circle_image()
        cr = extract_contour(img, method="threshold")
        assert cr is not None
        h = hu_moments(cr.contour)
        assert h.shape == (7,)

    def test_geometric_keys(self) -> None:
        img = _make_circle_image()
        cr = extract_contour(img, method="threshold")
        assert cr is not None
        geo = geometric_features(cr)
        assert "aspect_ratio" in geo
        assert "solidity" in geo
        assert "circularity" in geo
        assert "extent" in geo


class TestQuality:
    def test_good_image_is_ok(self) -> None:
        img = _make_circle_image()
        cr = extract_contour(img, method="threshold")
        report = assess_quality(img, cr)
        assert report.ok or report.score > 0.5

    def test_blank_image_warns(self) -> None:
        blank = np.zeros((224, 224), dtype=np.uint8)
        report = assess_quality(blank, None)
        assert not report.ok
        assert "no_contour_detected" in report.warnings

    def test_tiny_image_warns(self) -> None:
        tiny = np.ones((30, 30), dtype=np.uint8) * 128
        report = assess_quality(tiny, None)
        assert "image_too_small" in report.warnings
