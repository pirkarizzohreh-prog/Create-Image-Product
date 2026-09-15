import cv2
import numpy as np
from PIL import Image


def _pil_to_cv(im: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def _cv_to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))


def _gray_world_white_balance(bgr: np.ndarray) -> np.ndarray:
    result = bgr.astype(np.float32)
    b, g, r = cv2.split(result)
    b_avg, g_avg, r_avg = b.mean(), g.mean(), r.mean()
    gray_avg = (b_avg + g_avg + r_avg) / 3.0
    # Avoid divide-by-zero on degenerate (near-black/near-white) input.
    b *= (gray_avg / b_avg) if b_avg > 1e-3 else 1.0
    g *= (gray_avg / g_avg) if g_avg > 1e-3 else 1.0
    r *= (gray_avg / r_avg) if r_avg > 1e-3 else 1.0
    return cv2.merge([b, g, r]).clip(0, 255).astype(np.uint8)


def _clahe_contrast(bgr: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)


def _unsharp_mask(bgr: np.ndarray, amount: float = 0.6, sigma: float = 2.0) -> np.ndarray:
    blurred = cv2.GaussianBlur(bgr, (0, 0), sigma)
    sharpened = cv2.addWeighted(bgr, 1 + amount, blurred, -amount, 0)
    return sharpened


def stage_enhance(im: Image.Image, min_edge_px: int = 1200) -> tuple[Image.Image, dict]:
    """Denoise, white-balance, contrast-normalize, and sharpen a raw product
    photo. Upscales (Lanczos) if the image is below the configured minimum
    working resolution so downstream stages have enough detail to work with."""
    detail: dict = {"input_size": im.size}

    bgr = _pil_to_cv(im)

    if min(im.size) < min_edge_px:
        scale = min_edge_px / min(im.size)
        new_size = (round(im.width * scale), round(im.height * scale))
        bgr = cv2.resize(bgr, new_size, interpolation=cv2.INTER_LANCZOS4)
        detail["upscaled_to"] = new_size

    bgr = cv2.fastNlMeansDenoisingColored(bgr, None, h=6, hColor=6, templateWindowSize=7, searchWindowSize=21)
    bgr = _gray_world_white_balance(bgr)
    bgr = _clahe_contrast(bgr)
    bgr = _unsharp_mask(bgr)

    out = _cv_to_pil(bgr)
    detail["output_size"] = out.size
    return out, detail
