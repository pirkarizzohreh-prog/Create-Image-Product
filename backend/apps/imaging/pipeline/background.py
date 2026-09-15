import cv2
import numpy as np
from PIL import Image

_session = None


def _get_session():
    """Lazily create the rembg session (loads the U^2-Net ONNX model on
    first use) so importing this module doesn't require the model to be
    downloaded/available at import time (useful for unit tests)."""
    global _session
    if _session is None:
        from rembg import new_session

        _session = new_session("u2net")
    return _session


class BackgroundRemovalError(Exception):
    pass


def stage_remove_background(im: Image.Image) -> tuple[Image.Image, dict]:
    """Segments the product from its background, returning an RGBA cutout
    with a cleaned, feathered alpha edge (reduces halos / stray pixel
    islands from the raw matting model)."""
    from rembg import remove

    try:
        cutout = remove(im, session=_get_session())
    except Exception as exc:
        raise BackgroundRemovalError(f"Background segmentation failed: {exc}") from exc

    if cutout.mode != "RGBA":
        cutout = cutout.convert("RGBA")

    r, g, b, a = cutout.split()
    alpha = np.array(a)

    # Remove small stray-pixel islands and fill small holes in the mask.
    kernel = np.ones((5, 5), np.uint8)
    alpha_bin = (alpha > 20).astype(np.uint8) * 255
    alpha_clean = cv2.morphologyEx(alpha_bin, cv2.MORPH_OPEN, kernel)
    alpha_clean = cv2.morphologyEx(alpha_clean, cv2.MORPH_CLOSE, kernel)

    # Keep only the largest connected component (the product), drop noise.
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(alpha_clean, connectivity=8)
    if num_labels > 1:
        largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        alpha_clean = np.where(labels == largest, 255, 0).astype(np.uint8)

    # Feather the edge slightly so the composite onto white doesn't show a hard/aliased outline.
    alpha_feathered = cv2.GaussianBlur(alpha_clean, (5, 5), 0)
    alpha_final = np.minimum(alpha, alpha_feathered).astype(np.uint8)

    cutout_clean = Image.merge("RGBA", (r, g, b, Image.fromarray(alpha_final)))

    ys, xs = np.where(alpha_final > 10)
    if len(xs) == 0:
        raise BackgroundRemovalError("No foreground product detected after segmentation.")
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)

    coverage_percent = 100.0 * float((alpha_final > 10).sum()) / (alpha_final.shape[0] * alpha_final.shape[1])
    detail = {"bbox": bbox, "coverage_percent": round(coverage_percent, 2)}
    return cutout_clean, detail
