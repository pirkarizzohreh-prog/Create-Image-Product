"""Quality-control checks run after export. Each check is a pure function
returning (passed: bool, detail: dict) so results are easy to log, test, and
surface in the review queue. `run_qc` aggregates them into a single report;
any single failed check routes the job to manual review."""
from PIL import Image

CORNER_SAMPLE_PX = 12


def check_background_whiteness(final_image: Image.Image, tolerance: float) -> tuple[bool, dict]:
    w, h = final_image.size
    s = min(CORNER_SAMPLE_PX, w // 4, h // 4) or 1
    corners = {
        "top_left": final_image.crop((0, 0, s, s)),
        "top_right": final_image.crop((w - s, 0, w, s)),
        "bottom_left": final_image.crop((0, h - s, s, h)),
        "bottom_right": final_image.crop((w - s, h - s, w, h)),
    }
    max_deviation = 0.0
    per_corner = {}
    for name, patch in corners.items():
        pixels = list(patch.getdata())
        avg = tuple(sum(c[i] for c in pixels) / len(pixels) for i in range(3))
        deviation = max(255 - avg[0], 255 - avg[1], 255 - avg[2])
        per_corner[name] = {"avg_rgb": [round(v, 1) for v in avg], "deviation": round(deviation, 2)}
        max_deviation = max(max_deviation, deviation)

    passed = max_deviation <= tolerance
    return passed, {"max_deviation": round(max_deviation, 2), "tolerance": tolerance, "corners": per_corner}


def check_product_coverage(coverage_percent: float, min_pct: float, max_pct: float) -> tuple[bool, dict]:
    passed = min_pct <= coverage_percent <= max_pct
    return passed, {"coverage_percent": round(coverage_percent, 2), "min": min_pct, "max": max_pct}


def check_centering(padding_px: dict, output_size_px: int, tolerance_percent: float) -> tuple[bool, dict]:
    tolerance_px = (tolerance_percent / 100.0) * output_size_px
    horizontal_delta = abs(padding_px["left"] - padding_px["right"])
    vertical_delta = abs(padding_px["top"] - padding_px["bottom"])
    passed = horizontal_delta <= tolerance_px and vertical_delta <= tolerance_px
    return passed, {
        "horizontal_delta_px": horizontal_delta,
        "vertical_delta_px": vertical_delta,
        "tolerance_px": round(tolerance_px, 2),
    }


def check_identity_similarity(source_image: Image.Image, recreated_image: Image.Image, threshold: float) -> tuple[bool, dict]:
    import imagehash

    source_hash = imagehash.phash(source_image, hash_size=16)
    recreated_hash = imagehash.phash(recreated_image, hash_size=16)
    max_bits = source_hash.hash.size
    hamming_distance = source_hash - recreated_hash
    similarity = 1.0 - (hamming_distance / max_bits)

    passed = similarity >= threshold
    return passed, {
        "similarity": round(similarity, 4),
        "threshold": threshold,
        "hamming_distance": int(hamming_distance),
    }


def run_qc(ctx) -> dict:
    """ctx is a apps.imaging.pipeline.context.PipelineContext that has been
    run through export. Reads accumulated stage detail off ctx.detail."""
    reasons = []
    checks = {}

    whiteness_pass, whiteness_detail = check_background_whiteness(
        ctx.final_image, ctx.params.qc_background_whiteness_tolerance
    )
    checks["background_whiteness"] = {"passed": whiteness_pass, **whiteness_detail}
    if not whiteness_pass:
        reasons.append("Background is not sufficiently pure white.")

    coverage_percent = ctx.detail.get("remove_background", {}).get("coverage_percent")
    if coverage_percent is not None:
        coverage_pass, coverage_detail = check_product_coverage(
            coverage_percent, ctx.params.qc_min_product_coverage_percent, ctx.params.qc_max_product_coverage_percent
        )
        checks["product_coverage"] = {"passed": coverage_pass, **coverage_detail}
        if not coverage_pass:
            reasons.append("Product coverage ratio out of expected bounds (possibly clipped or near-empty frame).")

    padding_px = ctx.detail.get("square_center_pad", {}).get("padding_px")
    if padding_px:
        centering_pass, centering_detail = check_centering(
            padding_px, ctx.params.output_size_px, ctx.params.qc_centering_tolerance_percent
        )
        checks["centering"] = {"passed": centering_pass, **centering_detail}
        if not centering_pass:
            reasons.append("Product is not evenly centered / padding is asymmetric.")

    if ctx.mode == "recreate_studio" and ctx.pre_ai_image is not None and ctx.post_ai_image is not None:
        identity_pass, identity_detail = check_identity_similarity(
            ctx.pre_ai_image, ctx.post_ai_image, ctx.params.qc_identity_similarity_threshold
        )
        checks["identity_similarity"] = {"passed": identity_pass, **identity_detail}
        if not identity_pass:
            reasons.append("AI-recreated product may have drifted from the original (low identity similarity score).")

    overall_passed = all(c["passed"] for c in checks.values()) if checks else False
    return {"passed": overall_passed, "reasons": reasons, "checks": checks}
