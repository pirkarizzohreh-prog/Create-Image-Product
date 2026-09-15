import io

from PIL import Image, ImageOps

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "BMP", "TIFF", "HEIF"}
MIN_EDGE_PX = 300
MAX_PIXELS = 40_000_000  # guard against decompression-bomb sized uploads


class IngestError(Exception):
    pass


def stage_ingest(source_bytes: bytes) -> Image.Image:
    """Open, validate, and normalize a raw upload into an RGB PIL Image."""
    try:
        im = Image.open(io.BytesIO(source_bytes))
        im.load()
    except Exception as exc:
        raise IngestError(f"Could not decode image: {exc}") from exc

    if im.format not in ALLOWED_FORMATS:
        raise IngestError(f"Unsupported image format: {im.format}")

    if im.width * im.height > MAX_PIXELS:
        raise IngestError(f"Image too large ({im.width}x{im.height}); exceeds {MAX_PIXELS} pixel limit.")

    if min(im.width, im.height) < MIN_EDGE_PX:
        raise IngestError(f"Image too small ({im.width}x{im.height}); minimum edge is {MIN_EDGE_PX}px.")

    # Respect EXIF orientation from mobile cameras, then drop EXIF (not needed downstream).
    im = ImageOps.exif_transpose(im)
    if im.mode != "RGB":
        im = im.convert("RGB")
    return im
