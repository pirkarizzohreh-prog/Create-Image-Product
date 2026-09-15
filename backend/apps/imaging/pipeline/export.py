import hashlib
import io

from PIL import Image

EXT_BY_FORMAT = {"WEBP": "webp", "PNG": "png", "JPEG": "jpg"}


def stage_export(im: Image.Image, output_format: str = "WEBP", quality: int = 90) -> tuple[bytes, dict]:
    output_format = output_format.upper()
    buf = io.BytesIO()
    save_kwargs = {}
    if output_format in ("WEBP", "JPEG"):
        save_kwargs["quality"] = quality
    if output_format == "WEBP":
        save_kwargs["method"] = 6
    im.save(buf, format=output_format, **save_kwargs)
    data = buf.getvalue()

    checksum = hashlib.sha256(data).hexdigest()
    detail = {
        "format": output_format,
        "extension": EXT_BY_FORMAT.get(output_format, output_format.lower()),
        "size_bytes": len(data),
        "checksum": checksum,
        "dimensions": im.size,
    }
    return data, detail
