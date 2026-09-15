from PIL import Image

WHITE = (255, 255, 255)


def stage_compose_white(cutout_rgba: Image.Image) -> tuple[Image.Image, dict]:
    """Crops the cutout to its content bounding box and alpha-composites it
    onto a pure white RGB background, sized exactly to the content."""
    bbox = cutout_rgba.getbbox()
    if bbox is None:
        bbox = (0, 0, cutout_rgba.width, cutout_rgba.height)
    cropped = cutout_rgba.crop(bbox)

    white_bg = Image.new("RGBA", cropped.size, WHITE + (255,))
    composed = Image.alpha_composite(white_bg, cropped).convert("RGB")

    detail = {"content_size": composed.size, "crop_bbox": bbox}
    return composed, detail


def stage_square_center_pad(content_rgb: Image.Image, output_size_px: int, padding_percent: float) -> tuple[Image.Image, dict]:
    """Places `content_rgb` (already on white, tightly cropped to the
    product) onto an output_size_px x output_size_px pure white canvas,
    scaled to fit within (1 - padding%) of the canvas and centered — which
    guarantees equal padding on all four edges by construction."""
    canvas = Image.new("RGB", (output_size_px, output_size_px), WHITE)

    usable_fraction = max(0.0, 1.0 - (padding_percent / 100.0) * 2.0)
    # padding_percent is applied per-edge; usable content area is the canvas
    # minus padding_percent on each side, i.e. (1 - 2*padding%) of the canvas.
    target_edge = max(1, round(output_size_px * usable_fraction))

    w, h = content_rgb.size
    scale = min(target_edge / w, target_edge / h)
    new_size = (max(1, round(w * scale)), max(1, round(h * scale)))
    resized = content_rgb.resize(new_size, Image.LANCZOS)

    paste_x = (output_size_px - new_size[0]) // 2
    paste_y = (output_size_px - new_size[1]) // 2
    canvas.paste(resized, (paste_x, paste_y))

    padding_left = paste_x
    padding_right = output_size_px - (paste_x + new_size[0])
    padding_top = paste_y
    padding_bottom = output_size_px - (paste_y + new_size[1])

    detail = {
        "output_size": (output_size_px, output_size_px),
        "content_size": new_size,
        "padding_px": {
            "left": padding_left, "right": padding_right,
            "top": padding_top, "bottom": padding_bottom,
        },
    }
    return canvas, detail
